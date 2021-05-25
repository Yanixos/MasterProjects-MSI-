
from ctypes import Structure, c_int, CDLL, c_double, POINTER, Union
from database_utils import Database, Trace, KEY_LEN
from timeit import default_timer as timer
from datetime import timedelta
import pathlib
import struct
import sys
import os

DOUBLE_SIZE = 8

# user controlled parameters
db_file = "traces.db"
new_capture = False
nb_samples = 3000
nb_traces = 50
traces_start_offset = 0
use_all_wave = False

leakage_ranges = [ \
    (1505 , 1510), (1755 , 1765), (2005 , 2015), (2254 , 2278), 
    (1561 , 1565), (1805 , 1820), (2060 , 2075), (2314 , 2326),
    (1615 , 1625), (1865 , 1878), (2120 , 2130), (2370 , 2384), 
    (1670 , 1680), (1920 , 1934), (2175 , 2185), (2425 , 2435)  
]

# store traces on the database
    
if new_capture:
    print("""
    [!] If you are executing this outside of a jupyter notebook, you won't be able to capture new traces unless you setup the chipwhisperer environment.
    [*] If you are inside a jupyter notebook,  please do  the following steps :
     1- Go to the cell "2.0.1  CAPTURE_NEW_TRACES_CELL" :
         1.1- Set your paramaters and make sure the parameter new_traces is set to True
         1.2- Execute the cell 
     2- Go to the cell "2.0.2  ATTACK_CODE_CELL" :
         2.1- Set your parameters and make sure the parameter new_traces is set to False
         2.2- Execute the cell
     3- Go to the cell "2.0.3  ATTACK_LAUNCHER_CELL" :
         3.1- Execute the cell""")
    sys.exit(0)
    
db  = Database(file=db_file)

# perform a query which selects args.number_of_traces traces starting from args.traces_start_offset offset
traces_from_db = Trace.select().limit(nb_traces).offset(traces_start_offset)


# load C lib
try:
    lib = CDLL(pathlib.Path("cpa/cpa_attack.so").absolute().as_posix())
except OSError as err:
    print("Make sure that `make` command was performed and the library was created. \nError : {}".format(err))

# define Ctype structure that matches the Python trace 

class U_WAVE(Union):
    _fields_ = [
        ("intervals", POINTER(c_double) * KEY_LEN),
        ("all", POINTER(c_double)),
    ]      

class TRACE(Structure):
    _fields_ = [
        ("wave", U_WAVE),
        ("textin", c_int * KEY_LEN),
        ("key", c_int * KEY_LEN)
    ]

# defining python pointers to C functions

if use_all_wave :
    intervals = [nb_samples] * KEY_LEN
    c_intervals = (c_int * KEY_LEN)(*intervals) 
    
    init_wave = lib.init_wave                            # python pointer to the C init_wave function 
    init_wave.restype = U_WAVE

    fill_wave = lib.fill_wave                             # python pointer to the C fill_wave function 
    fill_wave.restype = None

else :
    intervals = [ (end - start) for start, end in leakage_ranges]  # calculating the nb_samples for each interval
    c_intervals = (c_int * KEY_LEN)(*intervals)                    # convert it to C int array

    init_intervals = lib.init_intervals                            # python pointer to the C init_intervals function 
    init_intervals.restype = U_WAVE

    fill_intervals = lib.fill_intervals                             # python pointer to the C fill_intervals function 
    fill_intervals.restype = None

# creates a C wave from a binary wave stored in the db 

def handle_wave(nb_samples):
    wave = init_wave(nb_samples)
    wave_bin = struct.unpack_from("d" * nb_samples, trace.wave, 0 * DOUBLE_SIZE)  
    wave_bin = [round(x, 8) for x in wave_bin]
    fill_wave(wave, (c_double * nb_samples)(*wave_bin), nb_samples)
    return wave

def handle_intervals(c_intervals):
    
    wave = init_intervals(c_intervals)                         # allocate memory for all the intervals
    
    for i in range(len(leakage_ranges)):
        start, end = leakage_ranges[i]
        wave_bin = struct.unpack_from("d" * intervals[i], trace.wave, start * DOUBLE_SIZE)  
        wave_bin = [round(x, 8) for x in wave_bin]            # convert the packed data inside the db to samples
        fill_intervals(wave, i, (c_double * intervals[i])(*wave_bin), intervals[i])   # fill the wave structure
    
    return wave

# Create a list of C traces
traces = []

for trace in traces_from_db:                                  # create Traces in C from the Traces in the db
    if use_all_wave :
        wave = handle_wave(nb_samples)                               # create a wave 
    else :
        wave = handle_intervals(c_intervals)                         # create a wave intervals              
    correct_key = list(bytearray.fromhex(trace.key))
    traces.append(TRACE(
        wave,
        (c_int * KEY_LEN)(*list(bytearray.fromhex(trace.textin))),   # convert from Python Array to C Array
        (c_int * KEY_LEN)(*list(bytearray.fromhex(trace.key))),      # convert from Python Array to C Array
    ))
        
traces = (TRACE * nb_traces)(*traces)

# call the function that performs the attack

if use_all_wave :
    start = timer()
    lib.cpa_attack(traces, nb_traces, c_intervals, 1)
    #lib.dpa_attack(traces, nb_traces)
    end   = timer()
else :
    start = timer()
    lib.cpa_attack(traces, nb_traces, c_intervals, 0)
    end   = timer()

for t in traces :                           # free our allocated memroy
    if use_all_wave :
        lib.free_wave(t.wave)
    else :
        lib.free_intervals(t.wave)
        
print("Correct   key: ", end='')
for i in range(KEY_LEN): print(correct_key[i],end=' ')

print("\nThe attack took:  {}".format(timedelta(seconds=end-start)))
