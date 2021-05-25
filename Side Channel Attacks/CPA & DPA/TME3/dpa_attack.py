from timeit import default_timer as timer
from datetime import timedelta
from tqdm import tnrange
import numpy as np
import sys

sbox = (
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16)

HW = [bin(n).count("1") for n in range(0, 256)]

leakage_points = [1505, 1760, 2010, 2262,\
                  1563, 1814, 2067, 2321,\
                  1618, 1871, 2124, 2376,\
                  1676, 1927, 2180, 2429]

leakage_ranges = [ \
    range(1505 , 1510), range(1755 , 1765), range(2005 , 2015), range(2254 , 2278), 
    range(1561 , 1565), range(1805 , 1820), range(2060 , 2075), range(2314 , 2326),
    range(1615 , 1625), range(1865 , 1878), range(2120 , 2130), range(2370 , 2384), 
    range(1670 , 1680), range(1920 , 1934), range(2175 , 2185), range(2425 , 2435)  
]

def capture_traces() :
    scope.adc.samples = 3000
    scope.adc.offset = 0

    ktp = cw.ktp.Basic() # object dedicated to the generation of key (fixed by default) and plain text

    traces = [] # list of traces
    N = 80  # Number of traces


    for i in tnrange(N, desc = 'Capturing traces'):
        key, text = ktp.next()  # creation of a pair comprising (fixed) key and text 
        trace = cw.capture_trace(scope, target, text, key) # a trace is composed of the following fields :
                                                           #    a wave (samples)
                                                           #    textin (input text), textout (output text)
                                                           #    key (input key)    
        if trace is None:
            continue
        traces.append(trace)
    return traces

def store_traces(i=''):
    traces = capture_traces() 
    
    trace_array = np.asarray([trace.wave for trace in traces])  
    textin_array = np.asarray([trace.textin for trace in traces])
    known_keys = np.asarray([trace.key for trace in traces])    
    
    np.save("DPA_traces{}.npy".format(i), trace_array)
    np.save("DPA_textin{}.npy".format(i), textin_array)
    np.save("DPA_keys{}.npy".format(i), known_keys[0])

def load_traces(i='') :
    traces = np.load('./DPA_traces{}.npy'.format(i))
    pt     = np.load('./DPA_textin{}.npy'.format(i))
    key    = np.load('./DPA_keys{}.npy'.format(i))
    return traces, pt, key

def intermediate(pt, key):
    return sbox[pt ^ key]

def DPA_Attack(traces, pt, destinguisher="HW_Threshold") :
    
    mean_diffs = np.zeros(256)
    threshold = 4
    recovered_key = []

    for bnum in range(16):
        maximum = 0

        for guess in range(0, 256):
            group1 = []
            group2 = []    

            for trace_index in range(len(traces)):
                
                if destinguisher.upper() == "HW" :
                    avg_point = leakage_points[bnum]
                    hw = HW[intermediate( pt[trace_index][bnum], guess)]
                    
                    if hw < threshold :
                        group1.append(traces[trace_index][avg_point])
                    else:
                        group2.append(traces[trace_index][avg_point])
                
                else :
                    avg_range = leakage_ranges[bnum]
                    lsb_msb = intermediate( pt[trace_index][bnum], guess)

                    if  destinguisher.upper() == "MSB" :
                            hyp = lsb_msb & 0x80 
                    elif destinguisher.upper() == "LSB" :
                            hyp = lsb_msb & 0x01 
                    else :
                        print("[!] Unknown destinguisher: {}".format(destinguisher))
                        sys.exit(-1)
                        
                    if hyp :
                        group1.append(traces[trace_index][avg_range])
                    else:
                        group2.append(traces[trace_index][avg_range])
            
            group1_avg = np.asarray(group1).mean(axis=0)
            group2_avg = np.asarray(group2).mean(axis=0)
            
            mean_diffs[guess] = np.max(abs(group1_avg - group2_avg))
                
            if mean_diffs[guess] > maximum :
                maximum = mean_diffs[guess]
                best_guess = guess

        recovered_key.append(best_guess)
    
    return recovered_key

if __name__ == '__main__' :
    for i in range(1) :
        store_traces(i)
    
    num_traces = 100
    destinguisher = "HW"
    #destinguisher = "MSB"
    #destinguisher = "LSB"
    
    for i in range(1):
        traces, pt, key = load_traces(i)
        start = timer()
        recovered_key = DPA_Attack(traces[:num_traces], pt, destinguisher)
        end = timer()
        print("Recovered key: {}".format(recovered_key))
        print("Correct   key: {}".format(list(key)))
        print("The attack took:  {}".format(timedelta(seconds=end-start)))
