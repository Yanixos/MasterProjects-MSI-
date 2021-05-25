#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Yanis Alim

from collections import namedtuple
from scipy.signal import hilbert, chirp
import matplotlib.pyplot as plt
import numpy as np
import argparse
import math  

SIGFOX_FRAME     = namedtuple("SIGFOX_FRAME", "PREAMBULE FTYPE FLAGS SEQUENCE_NUM DEVICE_ID PAYLOAD MAC CRC16")
SYNC             = "1010" * 5
UPLINK_BAUDRATE  = 100
CRC16_POLYNOMIAL = 0x1021
MIN_LEN_FRAME    = 86
MAX_LEN_FRAME    = 192
MAX_FRAME_NUM    = 3
PACKET_AND_PAYLOD_LEN_FROM_FTYPE = {
	0x06b : [8, 0 ], 0x6e0 : [8, 0 ], 0x034 : [8, 0 ],                  # class A
	0x08d : [9, 1 ], 0x0d2 : [9, 1 ], 0x302 : [9, 1 ],                  # class B
	0x35f : [12,2 ], 0x598 : [12,3 ], 0x5a3 : [12,4 ],                  # class C
	0x611 : [16,5 ], 0x6bf : [16,6 ], 0x72c : [16,7 ], 0xf67 : [16,8],  # class D
	0x94c : [20,12], 0x971 : [20,11], 0x997 : [20,10], 0x9bf : [20,9]   # class E
                                    }
# The data returned from this dictionary is the ["ORIGINAL_TYPE", PAYLOAD_LENGTH, REPLICA_NUMBER]
DATA_FROM_REPLICA_TYPE = {     
    "0x6e0" :   ["0x06b", 0, 2] ,    "0x034" :   ["0x06b",  0, 3],              
    "0x0d2" :   ["0x08d", 1, 2] ,    "0x302" :   ["0x08d",  1, 3],
    "0x598" :   ["0x35f", 2, 2] ,    "0x5a3" :   ["0x35f",  2, 3],
    "0x6bf" :   ["0x611", 5, 2] ,    "0x72c" :   ["0x611",  5, 3],
    "0x971" :   ["0x94c",12, 2] ,    "0x997" :   ["0x94c", 12, 3],
                                  }

def downlink_demodulate(file):
    pass

def uplink_crc(data) :
    data = bytes(int(data[i : i + 8], 2) for i in range(0, len(data), 8))
    remainder = np.uint16(0)

    for byte in data  :
        remainder ^= (byte << 8)
        for _ in range(8) :
            remainder = ((remainder << 1) ^ CRC16_POLYNOMIAL) if (remainder & (1 << 15)) else (remainder << 1)
    
    return hex( ~ np.uint16(remainder) )

# convolutional "encoder/decoder" : realizes the register shifts (Polynomial Multiplication/Division) using a Polynomial Generator 111 : X² + + X + 1
def encode_decode_r3_fields(field, Enc_Dec):
    field = bin(int('1'+field[2:], 16))[3:] 
    w     = [int(field[i : i + 8], 2) for i in range(0, len(field), 8)]

    b2    = 0
    b1    = 0
    j     = 0
    result = []
    while j < len(w):
        n = w[j]
        v = 0
        i = 0
        while i < 8 : 
            b00 = (n & 128) >> 7
            b01 = (n & 64) >> 6
            v  += b00 if b2 == 0 else 1 - b00
            v   = v << 1
            v  += b01 if b1 == 0 else 1 - b01
            b2  = b00 if Enc_Dec else (v & 2) >> 1
            b1  = b01 if Enc_Dec else v & 1
            v   = v << 1
            n   = n << 2
            i  += 2
        v  >>= 1
        w[j] = v
        result.append("0x{:02x}".format(w[j]))
        j   += 1

    return "0x" + "".join( x.replace("0x",'') for x in result )


# convolutional "encoder/decoder" : realizes the register shifts (Polynomial Multiplication/Division) using a Polynomial Generator 101 : X² + 1
def encode_decode_r2_fields(field, Enc_Dec):
    field = bin(int('1'+field[2:], 16))[3:] 
    w     = [int(field[i : i + 8], 2) for i in range(0, len(field), 8)]

    b2    = 0
    b1    = 0
    j     = 0
    result = []
    while j < len(w):
        n = w[j]
        v = 0
        i = 0
        while i < 8 :
            b0 = (n & 128) >> 7
            v += b0 if b2 == b1 else 1 - b0
            b2 = b1
            b1 = b0 if Enc_Dec else v & 1
            n  = n << 1
            v  = v << 1
            i +=1
        v  >>= 1
        w[j] = v
        result.append("0x{:02x}".format(w[j]))
        j   += 1

    return "0x" + "".join( x.replace("0x",'') for x in result )

def decode_replica(replica):
    preambule    = "0x" + "a" * 5
    ftype        = DATA_FROM_REPLICA_TYPE[replica.FTYPE][0]
    len_payload  = DATA_FROM_REPLICA_TYPE[replica.FTYPE][1] * 2
    replica_num  = DATA_FROM_REPLICA_TYPE[replica.FTYPE][2]
    flag_seq_dev = encode_decode_r2_fields(replica.FLAGS + replica.SEQUENCE_NUM[2:] + replica.DEVICE_ID[2:],False) if replica_num == 2 else \
                   encode_decode_r3_fields(replica.FLAGS + replica.SEQUENCE_NUM[2:] + replica.DEVICE_ID[2:],False)
    flags        = flag_seq_dev[:3]
    sequence_num = "0x" + flag_seq_dev[3:6]
    device_id    = "0x" + flag_seq_dev[6:14]
    payload_mac  = encode_decode_r2_fields(replica.PAYLOAD + replica.MAC[2:], False)[:len(replica.PAYLOAD + replica.MAC[2:])] if replica_num == 2 else \
                   encode_decode_r3_fields(replica.PAYLOAD + replica.MAC[2:], False)[:len(replica.PAYLOAD + replica.MAC[2:])]
    payload      = payload_mac[:2+len_payload]
    mac          = "0x" + payload_mac[2+len_payload:]
    crc16        = encode_decode_r2_fields(replica.CRC16, False)[:len(replica.CRC16)] if replica_num == 2 else \
                   encode_decode_r3_fields(replica.CRC16, False)[:len(replica.CRC16)]
    recovered    = SIGFOX_FRAME(preambule, ftype, flags, sequence_num, device_id, payload, mac, crc16)

    return recovered


def parse_frames(binary_data) :
    #            "01010"*5   "XXX"            "XXXX"
    # FRAME :   | PREAMBLE | FTYPE | PACKET | CRC16       X       XXX         XXXXXXXX    X....X   X..X
    #                                PACKET :         | FLAG | SEQUENCE_NUM | DEVICE_ID | PAYLAOD | MAC 
    binary      = binary_data    
    CRC         = "NOT OK"    
    frames      = []
    frame_count = 0
    end_frame   = 0
    while len(binary) > MIN_LEN_FRAME and frame_count < MAX_FRAME_NUM :
        start_frame  = binary.index(SYNC)
        binary       = binary[ start_frame : ]
        ftype        = int(binary[20 :32],2)
        len_packet   = PACKET_AND_PAYLOD_LEN_FROM_FTYPE[ftype][0] * 8
        len_payload  = PACKET_AND_PAYLOD_LEN_FROM_FTYPE[ftype][1] * 8
        len_mac      = len_packet - len_payload - ( 6 * 8 )
        len_frame    = 20 + 12 + len_packet + 16    
        end_payload  = 80 + len_payload
        end_mac      = end_payload + len_mac
        end_frame   += start_frame + len_frame

        PREAMBULE    = "0x{:05x}".format(int(binary[0 :20],2))
        FTYPE        = "0x{:03x}".format(int(binary[20:32],2))
        FLAGS        = "0x{:01x}".format(int(binary[32:36],2))
        SEQUENCE_NUM = "0x{:03x}".format(int(binary[36:48],2))
        DEVICE_ID    = "0x{:08x}".format(int(binary[48:80],2))
        PAYLOAD      = "0x{:0{}x}".format(int(binary[80:end_payload],2),      len_payload // 4)
        MAC          = "0x{:0{}x}".format(int(binary[end_payload:end_mac],2), len_mac     // 4)
        CRC16        = "0x{:04x}".format( int(binary[end_mac:len_frame], 2))

        frame = SIGFOX_FRAME(PREAMBULE, FTYPE, FLAGS, SEQUENCE_NUM,  DEVICE_ID, PAYLOAD, MAC, CRC16)
        hex_frame = hex( int(binary[20:len_frame],2) )
        frames.append([frame,hex_frame])
        
        if frame_count == 0 and CRC16 == uplink_crc(binary[32:end_mac]) :
            CRC = "OK"
        binary = binary_data[end_frame:]
        frame_count += 1

    return frames, CRC

def hex_to_sigfox(string) :
    if string.startswith("0x") :
        string =  string[2:]
    if not string.startswith("aaaaa") :
        string = "aaaaa" + string
    binary_data = bin(int('1'+string, 16))[3:]
    replica = parse_frames(binary_data)
    frame = decode_replica(replica[0][0][0])
    print("[*] Reversed replica: \n{}".format(frame))


def exploit_envelope(baseband_envelope, average_power, bit_rate) :
    binary_data = ""
    rate_count = 0          
    for i in baseband_envelope :
        if i > average_power:                       # Signal power is stable at the high degree  
            rate_count += 1                         # we increment the rate_counter and continue
        else:                                       # Signal power is going down :  either it's the end of a bit count or changing phase in the DBPSK
            bit_count = round(rate_count/bit_rate)  # calculate the actual bit count
            rate_count = 0                          # reset rate counter

            if bit_count > 0:                       # if we reach 1 bit count at least we decode it
                                                    # if the last amplitude changed from the last one we keep it 0, else we change it to 1
                binary_data += ( "0" + "1" * (bit_count - 1) )
    return binary_data

def uplink_demodulate(file) :
    # read I and Q data 
    Fs = 1000000
    bit_rate = Fs / UPLINK_BAUDRATE
    IQ = np.fromfile(file, dtype=np.float32)
    I = IQ[0::2]
    Q = IQ[1::2]
    
    #                           __________________
    # get signal envelope r = \/ (I^2 + Q^2) / 2    https://www.tek.com/blog/calculating-rf-power-iq-samples
    baseband_envelope = []
    for i in range(len(I)):
        baseband_envelope.append( math.sqrt( (I[i]**2 + Q[i]**2) / 2 ) )

    # calculate the average  of the signal power to spot the amplitude change on the sigfox DBPSK modulation
    average_power = max(baseband_envelope)/2
    
    # get the binary data of the signal
    binary_data   = exploit_envelope(baseband_envelope, average_power, bit_rate)
 
    # parse the binary data to sigfox frames
    frames, CRC = parse_frames(binary_data)
    for i in range(3) :
        print("[*] Parsed frame:\n{}\n[*] Raw frame: {}\n".format(frames[i][0], frames[i][1]))
    print("[*] CRC: {}".format(CRC))


if __name__ == '__main__' :
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    parser.add_argument("-f", "--file", help="Complex file containing the uplink recording to be demodulated", required=False, dest="file")
    parser.add_argument("-d", "--decode", choices=["uplink", "downlink"], help = "Decode content of uplink/downlink frame", required=False, dest="decode")
    parser.add_argument("-r", "--reverse", help = "Reverse a 2nd or 3rd replica frame to the original one", required=False, dest="reverse")

    args = parser.parse_args()
    if args.decode == "uplink" :
        uplink_demodulate(args.file)
    else :
        downlink_demodulate(args.file)
    if args.reverse :
        hex_to_sigfox(args.reverse)

