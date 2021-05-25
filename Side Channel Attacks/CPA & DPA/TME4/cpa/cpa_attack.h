#ifndef CPA_ATTACK_H
# define CPA_ATTACK_H

#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <math.h>
#include <stdint.h>

#define KEY_SIZE 16
#define WAVE_SIZE 3000

/*
We have 2 different ways to perform the CPA Attack : 
  - Use the whole wave
  - Use only leakage ranges of the wave
Because of that we opted for a union type, so that we can either have :
  - The whole wave as a double array
  - A range for each SBOX output, which result in 16 arrays of type double
*/

typedef union         
{
  double* all;
  double* intervals[KEY_SIZE];
} u_wave ;

// Trace structure in C
typedef struct s_trace
{
  u_wave     wave;   
  int        textin[KEY_SIZE];
  int        key[KEY_SIZE];

}  t_trace;

// Precalculated Hamming Weight array: HW = [  i.count('1') for i in range(256)]
double HW[256] = {
    0.0, 1.0, 1.0, 2.0, 1.0, 2.0, 2.0, 3.0, 1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 3.0, 4.0, 1.0, 2.0, 2.0, 
    3.0, 2.0, 3.0, 3.0, 4.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 
    3.0, 4.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 3.0, 
    4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 1.0, 2.0, 2.0, 3.0, 2.0, 3.0, 3.0, 4.0, 2.0, 3.0, 3.0, 4.0, 
    3.0, 4.0, 4.0, 5.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 3.0, 4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 
    6.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 3.0, 4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 3.0, 4.0, 
    4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 4.0, 5.0, 5.0, 6.0, 5.0, 6.0, 6.0, 7.0, 1.0, 2.0, 2.0, 3.0, 2.0, 
    3.0, 3.0, 4.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 
    3.0, 4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 3.0, 4.0, 4.0, 
    5.0, 4.0, 5.0, 5.0, 6.0, 3.0, 4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 4.0, 5.0, 5.0, 6.0, 5.0, 6.0, 
    6.0, 7.0, 2.0, 3.0, 3.0, 4.0, 3.0, 4.0, 4.0, 5.0, 3.0, 4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 3.0, 
    4.0, 4.0, 5.0, 4.0, 5.0, 5.0, 6.0, 4.0, 5.0, 5.0, 6.0, 5.0, 6.0, 6.0, 7.0, 3.0, 4.0, 4.0, 5.0, 
    4.0, 5.0, 5.0, 6.0, 4.0, 5.0, 5.0, 6.0, 5.0, 6.0, 6.0, 7.0, 4.0, 5.0, 5.0, 6.0, 5.0, 6.0, 6.0, 
    7.0, 5.0, 6.0, 6.0, 7.0, 6.0, 7.0, 7.0, 8.0
};

int dpa_leakage_points[KEY_SIZE ]= {  1505, 1760, 2010, 2262,\
                                      1563, 1814, 2067, 2321,\
                                      1618, 1871, 2124, 2376,\
                                      1676, 1927, 2180, 2429 
                                    };

// Predefined AES SBOX
uint8_t sbox[256] =   {
  //0     1    2      3     4    5     6     7      8    9     A      B    C     D     E     F
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
  0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16

};
//------------------------------Trace related functions-----------------------------------------------------
void print_array(int *a);                                               // prints an array of size KET_SIZE
void print_samples(double **s, int i[]);                                // prints a wave from trace
void print_traces(t_trace *t, int n, int i[], int all);                 // prints the whole trace  
u_wave init_intervals(int* i);                                          // allocates the wave intervals
u_wave init_wave(int n);                                                // allocates the a wave of size nb_samples
void fill_interval(u_wave w, int i, double* v, int s);                  // fills the wave intervals
void fill_wave(u_wave w, double* v, int n);                             // fills the whole wave
void free_intervals(u_wave w);                                          // frees the wave intervals
void free_wave(u_wave w);                                               // frees the whole wave

//------------------------------HW related functions-----------------------------------------------------
unsigned int intermediate(int pt, int keyguess);                        // calculates sbox output

//------------------------------Formula related functions------------------------------------------------
void print_d_array(double* a, int len);                                 // prints a double array of size len
void init_array(double* a, int len, double v);                          // initializes an array to a specific value
double max_array(double* a,  int len);                                  // returns the max of an array
int argmax_array(double* a,  int len);                                  // return sthe max's index of an array
void sub_arrays(double* a, double* b, double* c, int len);              // substractes 2 arrays
void add_arrays(double* a, double* b, double* c, int len);              // adds 2 arrays
void mul_arrays(double* a, double* b, double* c, int len);              // multiplies 2 arrays 
void div_arrays(double* a, double* b, double* c, int len);              // divises 2 arrays
void sqrt_array(double* a, double* b, int len);                         // calculates the square root of all the array values
double mean(double *array, int  len);                                   // calulates the mean of an array                                                     
void mean_columns(t_trace *t, double* a, int b, int c, int d, int all); // calculates the mean of columns for a 2D array

//------------------------------CPA Attack related functions------------------------------------------------------------------
double corr_coef(t_trace *t, int n, int g, int p, int b, int all);      // calculates the correlation coef of a guess
int cpa_attack_byte(t_trace *t, int n, int b, int p, int all);          // recover a subkey using CPA attack 
void cpa_attack(t_trace *tr, int n, int* i, int all);                   // recover the AES key using CPA attack
int dpa_attack_byte(t_trace *tr, int n, int b);                          // recover a subkey using DPA attack
void dpa_attack(t_trace *tr, int n);                                    // recover the AES key using DPA attack
#endif
