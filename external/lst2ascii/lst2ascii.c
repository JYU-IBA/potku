/*
 * lst2ascii - Convert FAST ComTec list-mode files to ascii
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2012-2014 Cristiano L. Fontana
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 * To compile: clang -Wall -Wextra -pedantic -o lst2ascii lst2ascii.c
 * 
 * Change log:
 * 15/08/2014 - Fixed a visualization problem for the final summary
 *              and added some displays.
 * 31/12/2014 - Changed all the reading modes of fopen to binary for Windows
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>

#define readmpa3_DEBUG 0

enum
{
    FALSE = 0,
    TRUE = 1
};

const short int BUFFER_SIZE = 0xFF;
const char *LINE_TERMINATOR = "\r\n";

char *my_getline(FILE *input_file);

short int compare_active_adcs(short int *array, uint16_t word);
short int count_adcs(uint16_t word);

#define MAX_ADC 16

const uint16_t timer_mask = 0x4000;
const uint16_t sync_mask = 0xffff;
const uint16_t dummy_mask = 0x8000;

const uint16_t required_active_adcs_count = 1;
/*
const uint16_t required_active_adcs[] = {0, 1};
*/

int main(const int argc, const char* argv[])
{
    char *ascii_output_filename = NULL;
    FILE *ascii_output_file = NULL;
    FILE *input_file = NULL;

    short int end_of_header = FALSE;

    int bytes_read = 0;
    /*int byte_counter = 0;*/

    short int in_adc_header = FALSE;
    short int adc_index = 0;
    short int active_adc[MAX_ADC];
    short int adc_range[MAX_ADC];
    short int active_adcs_number = 0;

    unsigned int event_counter = 0;
    unsigned int adc_event_counter[MAX_ADC];

    int timerreduce = 1;
    unsigned int timer_counter = 0;
    unsigned int adc_timer_counter[MAX_ADC];

    short int at_eof = FALSE;

    memset(active_adc, 0, sizeof(short int)*MAX_ADC);
    memset(adc_range, 0, sizeof(short int)*MAX_ADC);
    memset(adc_event_counter, 0, sizeof(short int)*MAX_ADC);
    memset(adc_timer_counter, 0, sizeof(short int)*MAX_ADC);

    if  (argc < 2)
    {
        printf("Usage: %s <file_name.lst> [output_file]\n\n", argv[0]);
        printf("If no [output_file] is given, a \".lst\" file extension is assumed.\n");
        printf("Output will be: file_name.txt\n");
        printf("No extension on [output_file], \".txt\" will be added.\n");
        return 0;
    }

    if (argc == 2)
    {
        ascii_output_filename = calloc(sizeof(char), strlen(argv[1]));
        strcpy(ascii_output_filename, argv[1]);
        strcpy(ascii_output_filename + strlen(ascii_output_filename)-4, ".txt");
    }
    else if (argc >= 3)
    {
        ascii_output_filename = calloc(sizeof(char), strlen(argv[2]) + 4);
        strcpy(ascii_output_filename, argv[2]);
        strcpy(ascii_output_filename + strlen(ascii_output_filename), ".txt");
    }

    printf("Output file: %s\n", ascii_output_filename);

    input_file = fopen(argv[1], "rb");

    if (input_file == NULL)
    {
        printf("Unable to read: %s\n", argv[1]);

        return 1;
    }

    /*
     * Parse the file header.
     */
    do
    {
        char *line = my_getline(input_file);

        #if readmpa3_DEBUG >= 4
        printf("line: %s", line);
        #endif

        /*
         * Summing all line lengths we will get the number of bytes to skip.
         */
        bytes_read += strlen(line);

        /*
         * Parsing each line.
         */
        if (strstr(line, "[ADC") != NULL)
        {
            /*
             * Isolating the number of the ADC from the string
             */
            char *start_index = strstr(line, "[ADC");
            char *end_index = strstr(line, "]");

            *end_index = '\0';

            adc_index = atoi(start_index+4);

            in_adc_header = TRUE;

            #if readmpa3_DEBUG >= 1
            printf("adc_index: %s %d\n", start_index+4, adc_index);
            #endif
        }
        else if ((strstr(line, "range=") != NULL) && (in_adc_header == TRUE))
        {
            /*
             * Reading the range of the current ADC.
             */
            int range = 0;
            const char *string = "range=";
            const int length = strlen(string);
            char *start_index = strstr(line, string);
            char *end_index = strstr(line, LINE_TERMINATOR);

            *end_index = '\0';

            range = atoi(start_index + length);

            /*
             * Store the ADCs ranges
             */
            adc_range[adc_index-1] = range;

            #if readmpa3_DEBUG >= 1
            printf("range: %s %d\n", start_index + length, range);
            #endif
        }
        else if ((strstr(line, "active=") != NULL) && (in_adc_header == TRUE))
        {
            int active = 0;
            const char *string = "active=";
            const int length = strlen(string);
            char *start_index = strstr(line, string);
            char *end_index = strstr(line, LINE_TERMINATOR);

            *end_index = '\0';

            active = atoi(start_index + length);

            /*
             * Store which ADCs are active and count them.
             */
            active_adc[adc_index-1] = (active > 0) ? 1 : 0;
            active_adcs_number += (active > 0) ? 1 : 0;

            in_adc_header = FALSE;

            #if readmpa3_DEBUG >= 1
            printf("active: %s %d\n", start_index+7, active);
            #endif
        }
        else if (strstr(line, "timerreduce=") != NULL)
        {
            char *start_index = strstr(line, "timerreduce=");
            char *end_index = strstr(line, LINE_TERMINATOR);

            *end_index = '\0';

            timerreduce = atoi(start_index+12);

            #if readmpa3_DEBUG >= 1
            printf("timerreduce: %s %d\n", start_index+12, timerreduce);
            #endif
        }
        else if (strstr(line, "[LISTDATA]") != NULL)
        {
            end_of_header = TRUE;
        }

        free(line);
    } while (end_of_header == FALSE);

    #if readmpa3_DEBUG >= 1
    for (adc_index = MAX_ADC; adc_index > 0; adc_index--)
    {
        printf("active_adc[%d]: %d\n", \
               MAX_ADC-adc_index, \
               active_adc[MAX_ADC-adc_index]);
        printf("adc_range[%d]: %d\n", \
               MAX_ADC-adc_index, \
               adc_range[MAX_ADC-adc_index]);
    }
    printf("active_adcs_number: %d\n", active_adcs_number);

    printf("Bytes read: %d\n", bytes_read);
    #endif

    /*
     * Open the ascii output file.
     */
    ascii_output_file = fopen(ascii_output_filename, "w");
    if (ascii_output_file == NULL)
    {
        printf("Unable to open file for writing: %s\n", ascii_output_filename);

        return 3;
    }

    /*
     * Put a header on the first line
     */
    fprintf ( ascii_output_file, "# Event\tTime [ms]\tADC\tdatum\n" );

    /*
     * Close the input file in order to reopen it in binary mode.
     * This became obsolete with the 31/12/2014 change
     */
    /*
    fclose(input_file);

    input_file = fopen(argv[1], "rb");
    if (input_file == NULL)
    {
        printf("Unable to re-read: %s\n", argv[1]);

        return 2;
    }
     */
    
    /*
     * Read data part of the file.
     * First: Pass through the header part.
     */
    /*
    fseek(input_file, bytes_read, SEEK_SET);
     */
    
    /*
     * This part is to be used in case fseek does not work.
     */
    /*
    for (byte_counter = 0; byte_counter < bytes_read; byte_counter++)
    {
        #if readmpa3_DEBUG >= 3
        char temp_char = getc(input_file);
        putc(temp_char,stdout);
        #else
        getc(input_file);
        #endif
    }
     */

    /*
     * Second: Parse binary part.
     */
    do
    {
        /*
         * Read two 16 bit words
         */
        uint16_t lword = 0;
        uint16_t hword = 0;
        
        size_t low_result = fread(&lword, sizeof(uint16_t), 1, input_file);
        size_t high_result = fread(&hword, sizeof(uint16_t), 1, input_file);

        #if readmpa3_DEBUG >= 2
        printf("lword: %d, hword: %d\n", lword, hword);
        #endif

        /*
         * If the results are not 1, either an error occurred or we reached EOF.
         */
        if (low_result != 1 || high_result != 1)
        {
            #if readmpa3_DEBUG >= 2
            printf("Unable to read the two words\n");
            #endif
            at_eof = TRUE;
            continue;
        }

        /*
         * Looking for a timer event, one every 1 ms / timerreduce.
         */
        if (hword == timer_mask)
        {
            #if readmpa3_DEBUG >= 2
            printf("Found a timer mark\n");
            #endif

            /*
             * Determine the indices of the active ADCs
             */
            for (adc_index = 0; adc_index < MAX_ADC; adc_index++)
            {
                if (((lword >> adc_index) & 1) > 0)
                {
                    adc_timer_counter[adc_index]++;

                    #if readmpa3_DEBUG >= 3
                    printf("Active ADC index: %d\n", adc_index);
                    #endif
                }
            }

            timer_counter++;

            continue;
        }
        /*
         * Looking for a synchron mark, if it is the case do nothing.
         */
        else if (lword == sync_mask && hword == sync_mask)
        {
            #if readmpa3_DEBUG >= 3
            printf("Found a synchron mark\n");
            #endif
            continue;
        }
        /*
         * Looking for a signal mark, bit 30 has to be 0.
         * 0x4000000 == 1 << 30
         */
        else if ((hword & timer_mask) == 0)
        {
            short int event_active_adcs = 0;
            short int active_adcs_indices[MAX_ADC];
            uint16_t adc_values[MAX_ADC];
            short int required_adcs_flag = TRUE;

            #if readmpa3_DEBUG >= 2
            printf("Found an event mark\n");
            #endif

            /*
             * Determine the indices of the active ADCs
             */
            for (adc_index = 0; adc_index < MAX_ADC; adc_index++)
            {
                if (((lword >> adc_index) & 1) > 0)
                {
                    active_adcs_indices[event_active_adcs] = adc_index;
                    event_active_adcs++;

                    adc_event_counter[adc_index]++;

                    #if readmpa3_DEBUG >= 2
                    printf("Active ADC index: %d\n", adc_index);
                    #endif
                }
            }

            memset(adc_values, 0, sizeof(uint16_t)*MAX_ADC);

            #if readmpa3_DEBUG >= 2
            printf("event_active_adcs: %d\n", event_active_adcs);
            #endif

            /*
             * If a different number of ADCs is active there is an error
             */
            /*if (compare_active_adcs(active_adc, lword) == FALSE)*/
            if ((active_adcs_number < event_active_adcs) \
                || \
                (event_active_adcs < required_active_adcs_count))
            {
                #if readmpa3_DEBUG >= 2
                printf("Active ADCs do not match requirements, count: %d\n", event_active_adcs);

                for (adc_index = MAX_ADC; adc_index > 0; adc_index--)
                {
                    printf("active_adcs_indices[%d]: %d\n", MAX_ADC-adc_index, active_adcs_indices[MAX_ADC-adc_index]);
                }
                #endif
                continue;
            }

            if (required_adcs_flag == FALSE)
            {
                continue;
            }

            /*
             * Shall we read a dummy event?
             * Looking for a dummy flag, bit 31 has to be 1.
             * 0x8000000 == 1 << 31
             */
            if (hword & dummy_mask)
            {
                uint16_t dummy_word = 0;

                #if readmpa3_DEBUG >= 2
                size_t result = fread(&dummy_word, \
                                      sizeof(uint16_t), \
                                      1, \
                                      input_file);
                printf("Dummy value read: %d (result: %d)\n", dummy_word, (int)result);
                #else
                fread(&dummy_word, sizeof(uint16_t), 1, input_file);
                #endif
            }

            /*
             * Read each ADC value
             */
            for (adc_index = 0; adc_index < event_active_adcs; adc_index++)
            {
                uint16_t adc_word = 0;
                /*
                 * If a datum is not available stop this loop.
                 */
                size_t result = fread(&adc_word, \
                                      sizeof(uint16_t), \
                                      1, \
                                      input_file);

                #if readmpa3_DEBUG >= 2
                printf("ADC value read: %d (result: %d)\n", adc_word, (int)result);
                #endif

                if (result != 1)
                {
                    break;
                }

                adc_values[adc_index] = adc_word;

                #if readmpa3_DEBUG >= 2
                printf("adc_value: %d, index: %d, adc_index: %d\n", adc_word, adc_index, active_adcs_indices[adc_index]);
                #endif
            }

            event_counter++;

            for (adc_index = 0; adc_index < event_active_adcs; adc_index++)
            {
                int write_result = fprintf(ascii_output_file, \
                                          "%u\t%g\t%hu\t%hu\n", \
                                          event_counter, \
                                          (float)timer_counter / timerreduce, \
                                          active_adcs_indices[adc_index], \
                                          adc_values[adc_index]);

                if (write_result < 0)
                {
                    fprintf( stderr, "ERROR: Unable to write to output file");
                }
            }

            #if readmpa3_DEBUG >= 2
            printf("%d\t%d\n", adc_values[0], adc_values[1]);
            #endif
        }
    } while (at_eof == FALSE);

    printf("Written events: %d\n", event_counter);
    printf("Run time: %g s\n", (float)timer_counter / timerreduce / 1000);
    printf("Average rate: %g Hz\n", \
           event_counter * timerreduce * 1000 / (float)timer_counter);

    for (adc_index = 0; adc_index < MAX_ADC; adc_index++)
    {
        if (active_adc[adc_index])
        {
            printf("\nADC %d:\n", \
                   adc_index);
            printf("Run time: %g s\n", \
                   (float)adc_timer_counter[adc_index] / timerreduce / 1000);
            printf("Events: %d\n", \
                   adc_event_counter[adc_index]);
            printf("Average rate: %g Hz\n", \
                  (float)adc_event_counter[adc_index] * timerreduce * 1000 / \
                  (float)adc_timer_counter[adc_index]);
            printf("Dead time: %g%%\n", \
                   100 - 100 * \
                   (float)adc_timer_counter[adc_index] / timer_counter);
            printf("Range: %d\n", \
                   adc_range[adc_index]);
        }
    }

    free(ascii_output_filename);

    fclose(input_file);
    fclose(ascii_output_file);

    return 0;
}

/*
 * Get a line from input_file, the line has to be freed by the user.
 */
char *my_getline(FILE *input_file)
{
    char *buffer;
    short int counter = 0;

    buffer = calloc(sizeof(char), BUFFER_SIZE);

    for (counter = 0; counter < BUFFER_SIZE; counter++)
    {
        buffer[counter] = getc(input_file);

        #if readmpa3_DEBUG >= 5
        printf("buffer: %s\n", buffer);
        /*printf("LINE_TERMINATOR: %s\n", LINE_TERMINATOR);
        printf("strcmp(): %d\n", strstr(buffer, LINE_TERMINATOR));*/
        #endif

        /*
         * If we reached an end of a line, return the buffer.
         */
        if (strstr(buffer, LINE_TERMINATOR) != NULL)
        {
            return buffer;
        }
    }

    return buffer;
}

short int compare_active_adcs(short int *array, uint16_t word)
{
    int i = 0;
    for (i = 0; i < MAX_ADC; i++)
    {
        #if readmpa3_DEBUG >= 4
        printf("compare_active_adcs(), i: %d, array[]: %d, word: %d, comparison: %d\n", i, array[i], ((word >> i) & 1),  array[i] != ((word >> i) & 1));
        #endif

        if (array[i] != ((word >> i) & 1))
        {
            return FALSE;
        }
    }

    return TRUE;
}

short int count_adcs(uint16_t word)
{
    int i = 0;
    int counter = 0;

    #if readmpa3_DEBUG >= 4
    printf("count_adcs(), word: %d\n", word);
    #endif

    for (i = 0; i < MAX_ADC; i++)
    {
        counter += (word >> i) & 1;

        #if readmpa3_DEBUG >= 4
        printf("count_adcs(), counter: %d\n", counter);
        #endif
    }

    return counter;
}
