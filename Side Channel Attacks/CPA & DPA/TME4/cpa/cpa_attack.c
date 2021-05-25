#include "cpa_attack.h"

//-----------------Trace related functions-----------------------------------

void print_array(int *array)                                // prints an array of size KET_SIZE                                       
{
    for(int i = 0; i < KEY_SIZE; i++)
        printf("%d ", array[i]);
    printf("\n");
}
void print_samples(double **samples, int intervals[])       // prints a wave from trace
{
     int nr_samples = 0;
     for (int i = 0; i < KEY_SIZE; i++)
     {
           nr_samples = intervals[i];
           printf("\tintervals[%d]: ",i);
           for(int j = 0; j < nr_samples; j++)
                printf("%.10f ", samples[i][j]);
           printf("\n");
     }
}

void print_traces(t_trace *tr, int nr_traces, int intervals[], int all) // prints the whole trace
{
    for(int i = 0; i < nr_traces; i++)
    {
        printf("Trace %d :\n", i);

        if (all == 1)
        {
            printf("Wave: "); 
            print_d_array(tr[i].wave.all, WAVE_SIZE);
        }
        else 
        {
            print_samples(tr[i].wave.intervals, intervals);
        }
            
        printf("\n");
        printf("\ttextin: "); print_array(tr[i].textin);
        printf("\tkey: "); print_array(tr[i].key);
    }
}

u_wave init_intervals(int* intervals)                                 // allocates the wave intervals
{
    u_wave wave;
    for(int i = 0; i < KEY_SIZE; i++)
        wave.intervals[i] = malloc(sizeof(double) * intervals[i]);
    
    return wave;
}

u_wave init_wave(int nb_samples)                                 // allocates the a wave of size nb_samples
{
    u_wave wave;

    wave.all = malloc(sizeof(double) * nb_samples);
    
    return wave;
}

void fill_intervals(u_wave wave, int index, double* values, int size) // fills the wave intervals
{
    for(int i = 0; i < size; i++)
        wave.intervals[index][i] = values[i];
}

void fill_wave(u_wave wave, double* values, int nb_samples)          // fills the whole wave
{
    for(int i = 0; i < nb_samples; i++)
        wave.all[i] = values[i];
}

void free_intervals(u_wave wave)                                     // frees the wave intervals
{
    for(int i = 0; i < KEY_SIZE; i++)
        free(wave.intervals[i]);
}

void free_wave(u_wave wave)                                     // frees the whole wave
{
    free(wave.all);
}

//------------------------------HW related functions-----------------------------------------------------

unsigned int intermediate(int pt, int keyguess)                 // calculates sbox output
{
    return sbox[pt ^ keyguess];
}
//------------------------------Formula related functions------------------------------------------------

void print_d_array(double* a, int len)                          // prints a double array of size len
{
    for (int i = 0; i < len; i++)
        printf("%.8f ", a[i]);
    printf("\n");
}

void init_array(double* a, int len, double v) {                 // initializes an array to a specific value
    for (int i = 0; i < len; i++)
        a[i] = v;
}

double max_array(double* a, int len)  {                        // returns the max of an array
    double max = 0;
    for (int i = 0; i < len; i++) 
        if (fabs(a[i]) > max)
            max = fabs(a[i]);   
    return max;
}

int argmax_array(double* a, int len)  {                        // return sthe max's index of an array
    double max = 0.0;
    int index_max = -1;
    for (int i = 0; i < len; i++) 
        if (a[i] > max) 
        {   
            max = a[i];
            index_max = i;
        }   
    return index_max;
}

void sub_arrays(double* a, double* b, double* c, int len)  {    // substractes 2 arrays
    for (int i = 0; i < len; i++) 
        c[i] = (a[i] - b[i]);
}

void add_arrays(double* a, double* b, double* c, int len)  {    // adds 2 arrays
    for (int i = 0; i < len; i++) 
        c[i] = (a[i] + b[i]);
}

void mul_arrays(double* a, double* b, double* c, int len)  {    // multiplies 2 arrays 
    for (int i = 0; i < len; i++) 
        c[i] = (a[i] * b[i]);
}

void div_arrays(double* a, double* b, double* c, int len)  {    // divises 2 arrays
    for (int i = 0; i < len; i++) 
        c[i] = (a[i] / b[i]);
}

void sqrt_array(double* a, double* b, int len)  {               // calculates the square root of all the array values
    for (int i = 0; i < len; i++) 
        b[i] = sqrt(a[i]);
}

double mean(double* array, int len) {                          // calulates the mean of an array          
    double result = 0;
    for (int i = 0; i < len; i++)
        result += array[i];
    return result / len;
}

void mean_columns(t_trace *traces, double* mean_columns, int nb_traces, int nb_samples, int bnum, int all)  {    // calculates the mean of columns for a 2D array
    for (int i = 0; i < nb_samples; i++) {
        double result = 0.0;
        for (int j = 0; j < nb_traces; j++) {
            if (all == 1)
                result += traces[j].wave.all[i];
            else 
                result += traces[j].wave.intervals[bnum][i];
        }
        mean_columns[i] = result / nb_traces;
    }
}

//------------------------------CPA Attack related functions------------------------------------------------------------------
double corr_coef(t_trace *traces, int nb_traces, int guess, int nb_samples, int bnum, int all) { // calculates the correlation coef of a guess
    
    double COV_X_Y[nb_samples]; init_array(COV_X_Y, nb_samples, 0.0);                   // start initializing vars
    double STD_DEV_X[nb_samples];   init_array(STD_DEV_X,   nb_samples, 0.0);
    double STD_DEV_Y[nb_samples];   init_array(STD_DEV_Y,   nb_samples, 0.0);
    
    double hypothesis_mean;
    double hypothesis[nb_traces];        init_array(hypothesis, nb_traces, 0.0);
    double traces_col_means[nb_samples]; init_array(traces_col_means, nb_samples, 0.0);

    double hypothesis_diff;
    double traces_col_diff[nb_samples];  init_array(traces_col_diff, nb_samples, 0.0);
    double result[nb_samples];           init_array(result, nb_samples, 0.0);           // end initializing vars

    for (int tnum=0; tnum<nb_traces; tnum++) 
        hypothesis[tnum] = HW[ intermediate(traces[tnum].textin[bnum], guess) ];        // defining our hypothesis : for all traces, calculate the HW using 'guess' and 'traces[i].plaintext[bnum]'
    
    hypothesis_mean = mean(hypothesis, nb_traces);                                      // calculating the mean of our hypothesis
    mean_columns(traces, traces_col_means, nb_traces, nb_samples, bnum, all);

    for (int tnum=0; tnum<nb_traces; tnum++) {                                          // https://eprint.iacr.org/2015/260.pdf  (4- Incremental Pearson)
        hypothesis_diff = (hypothesis[tnum] - hypothesis_mean);
        if (all == 1 )
            sub_arrays( traces[tnum].wave.all,  traces_col_means, traces_col_diff, nb_samples ); // ∑ni=1 yi 
        else 
            sub_arrays( traces[tnum].wave.intervals[bnum],  traces_col_means, traces_col_diff, nb_samples ); // ∑ni=1 yi 

        init_array(result, nb_samples, hypothesis_diff);                                             // ∑ni=1 xi
        mul_arrays(traces_col_diff, result, result, nb_samples);                                     // ∑ni=1 xi . ∑ni=1 yi
        add_arrays(COV_X_Y, result, COV_X_Y, nb_samples);                                            // n . ∑ni=1 xi . yi - ∑ni=1 xi . ∑ni=1 yi  = COV(X,Y)
             
        init_array(result, nb_samples, hypothesis_diff * hypothesis_diff );                          // ∑ni=1 xi^2 
        add_arrays(STD_DEV_X, result, STD_DEV_X, nb_samples);                                        // n . ∑ni=1 xi^2 − ( ∑ni=1 xi )^2     = Deviation(X)  


        mul_arrays(traces_col_diff, traces_col_diff, result, nb_samples);
        add_arrays(STD_DEV_Y, result, STD_DEV_Y, nb_samples);                                        // n . ∑ni=1 yi^2− ( ∑ni=1 yi )^2      = Deviation(Y)                   
    }

    mul_arrays(STD_DEV_X, STD_DEV_Y, result, nb_samples);                                            // Deviation(Y) . Deviation(Y)                                      
    sqrt_array(result, result, nb_samples);                                                          // SQRT( Deviation(Y) . Deviation(Y) ) 
    div_arrays(COV_X_Y, result, result, nb_samples ) ;                                               // COV(X,Y) /  SQRT( Deviation(Y) . Deviation(Y) ) 

    return max_array(result, nb_samples);
}

int cpa_attack_byte(t_trace *tr, int nb_traces, int bnum, int nb_samples, int all) {       // recover a subkey using cpa attack 
    
    double corr_array[256];
    int best_guess = -1;

    for (int guess = 0; guess < 256; guess++) 
        corr_array[guess] = corr_coef(tr, nb_traces, guess, nb_samples, bnum, all);      // for each guess calculate the best correlation

    best_guess = argmax_array(corr_array, 256);                                          // the correct subkey is the guess that has the maximum correlation
    return best_guess;
}

void cpa_attack(t_trace *tr, int nb_traces, int* intervals, int all) {                    // recover all the subkeys using cpa attack
    int recovered_key[KEY_SIZE];

    for (int bnum = 0; bnum < KEY_SIZE; bnum++)                                           // for each subkey 
        recovered_key[bnum] = cpa_attack_byte(tr, nb_traces, bnum, intervals[bnum], all); // apply cpa
    
    printf("Recovered key: ");
    print_array(recovered_key);
}

int dpa_attack_byte(t_trace *tr, int nb_traces, int bnum)
{

    double mean_diffs[256];  init_array(mean_diffs, 256, 0.0);
    double threshold = 4.0;

    double group1[nb_traces]; int g1_index; double g1_avg = 0;
    double group2[nb_traces]; int g2_index; double g2_avg = 0; 
    
    int avg_point = -1;
    double hw = 0;
    double maximum = 0;
    int best_guess = -1;

    for (int guess = 0; guess < 256; guess++) 
    {
       
        init_array(group1, nb_traces, 0.0);
        init_array(group2, nb_traces, 0.0);
        g1_index = 0;
        g2_index = 0;

        for (int tnum = 0; tnum < nb_traces; tnum++ )
        {
            
            avg_point = dpa_leakage_points[bnum];
            hw = HW[ intermediate(tr[tnum].textin[bnum], guess) ]; 
            
            if ( hw < threshold ) 
                group1[g1_index++] = tr[tnum].wave.all[avg_point];
            else 
                group2[g2_index++] = tr[tnum].wave.all[avg_point];
        }
        
        g1_avg = mean(group1, g1_index);
        g2_avg = mean(group2, g2_index);
        
        mean_diffs[guess] = fabs(g1_avg-g2_avg);
        if (mean_diffs[guess] > maximum ) {
            maximum = mean_diffs[guess];
            best_guess = guess;
        }      
                
    }
    
    return best_guess;
}

void dpa_attack(t_trace *tr, int nb_traces)
{     
    int recovered_key[KEY_SIZE];     

    for (int bnum = 0; bnum < KEY_SIZE; bnum++)
        recovered_key[bnum] =  dpa_attack_byte(tr, nb_traces, bnum);
    
    printf("Recovered key: ");
    print_array(recovered_key);
}