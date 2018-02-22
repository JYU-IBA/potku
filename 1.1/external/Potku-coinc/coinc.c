/*
   Copyright (C) 2013 Jaakko Julin <jaakko.julin@jyu.fi>
   See file LICENCE for a copy of the GNU General Public Licence
*/



#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define N_ADCS_MAX 128
#define COINC_TABLE_SIZE_DEFAULT 20
#define N_ADCS_DEFAULT 8
#define SKIP_LINES_DEFAULT 0
#define TIMING_WINDOW_HIGH_DEFAULT 0
#define TIMING_WINDOW_LOW_DEFAULT 0
#define TRIGGER_ADC_DEFAULT 0
#define HELP_TEXT "Usage: ./coinc [OPTION] infile outfile\n\nIf no infile or outfile is specified, standard input or output is used respectively.\nValid options:\n\t--timestamps\toutput timestamps\n\t--both\t\toutput both data and timestamps (2 col/ch)\n\t--timediff\toutput both data and time difference to trigger time\n\t--nadc=NUM\tProcess a maximum of NUM ADCs (only valid when no calibrations are used)\n\t--skip=NUM\tskip first NUM lines from the beginning of the input\n\t--tablesize=NUM\tuse a coincidence table of NUM events\n\t--nevents=NUM\toutput maximum of NUM events\n\t--trigger=NUM\tuse ADC NUM as the triggering ADC\n\t--verbose\tVerbose output\n\t--low=ADC,NUM\tset timing window for ADC low (NUM ticks)\n\t--high=ADC,NUM\tset timing window for ADC high (NUM ticks)\n\n"
int verbose=0;
int silent=0;

struct list_event {
    unsigned int adc;
    unsigned int channel;
    unsigned long long int timestamp;
};

typedef struct list_event event;

typedef enum OUTPUT_MODE_E {
	MODE_RAW = 0,
    MODE_TIMESTAMPS = 1,
    MODE_TIME_AND_CHANNEL = 2,
    MODE_TIMEDIFF_AND_CHANNEL = 3
} output_mode;

void insert_blank_event(event *event) {
    event->adc=N_ADCS_MAX-1;
    event->channel=-1;
    event->timestamp=0;
}

int read_event_from_file(FILE *file, event *event, int n_adcs) {
    if(fscanf(file,"%u %u %llu\n",&event->adc, &event->channel, &event->timestamp) == 3) {
        if(event->adc < n_adcs) {
            return 1;
        } else {
            fprintf(stderr, "ADC value %u too high, aborting. Check input file or try increasing number of ADCs (currently %i).\n", event->adc, n_adcs);
            return 0;
        }

    } else {
		if(!feof(file)) {
			fprintf(stderr, "\nError in input data.\n");
		}
		return 0;
	}
}

int main (int argc, char **argv) {
    unsigned int i=0;
    unsigned int j=0,k=0;

    unsigned int coinc_table_size=COINC_TABLE_SIZE_DEFAULT, coinc_table_size_argument;
    unsigned int coincs_found=0;
    unsigned int lines_read=0;
    unsigned int trigger_adc=TRIGGER_ADC_DEFAULT,trigger_adc_argument;
	unsigned int n_adcs_argument=0,n_adcs=N_ADCS_DEFAULT;
	unsigned int adc;
	unsigned int adcs_in_coinc;
	output_mode output_mode=MODE_RAW;
	int *coinc_events = (int *)malloc(n_adcs*(sizeof(int)));
	int *n_adc_events = (int *)malloc(n_adcs*(sizeof(int)));
	int *n_coinc_adc_events = (int *)malloc(n_adcs*(sizeof(int)));
	for(adc=0; adc < n_adcs; adc++) {
		n_adc_events[adc]= 0; 
		n_coinc_adc_events[adc]= 0; 
	}
	long long int time_difference;
	long long int *time_window_high=malloc(N_ADCS_MAX*sizeof(long long int));
	long long int *time_window_low=malloc(N_ADCS_MAX*sizeof(long long int));;
    long long int time_window_argument=0;
    int adc_argument=0;
	int endgame=0;
	int skip_lines_argument=0,skip_lines=SKIP_LINES_DEFAULT;
    int output_n_events=0;
	char buffer[100];
	
    event *coinc_table = (event *)malloc(coinc_table_size*(sizeof(event)));
	FILE *read_file=stdin;
	FILE *output_file=stdout;
	if(argc==1) {
		fprintf(stderr, HELP_TEXT);
		return 0;
	}
    for(i=0; i<N_ADCS_MAX; i++) {
        time_window_low[i]=TIMING_WINDOW_LOW_DEFAULT;
        time_window_high[i]=TIMING_WINDOW_HIGH_DEFAULT;
    }
	for(i=1; i<(unsigned int)argc; i++) {
		if(verbose) fprintf(stderr, "Scanning argument no %i/%i (\"%s\")...\n", i, argc-1, argv[i]);
		if(strcmp(argv[i], "--verbose")==0) {
			fprintf(stderr, "Verbose output mode active.\n");
			verbose=1;
			continue;
		}
        if(strcmp(argv[i], "--timestamps")==0) {
            output_mode=MODE_TIMESTAMPS;
            if(verbose) fprintf(stderr, "Outputting timestamp values.\n");
            continue;
        }
        if(strcmp(argv[i], "--silent")==0) {
            silent=1;
            continue;
        }
        if(strcmp(argv[i], "--both")==0) {
            output_mode=MODE_TIME_AND_CHANNEL;
            if(verbose) fprintf(stderr, "Outputting both channel and timestamp values.\n");
            continue;
        }
        if(strcmp(argv[i], "--timediff")==0) {
            output_mode=MODE_TIMEDIFF_AND_CHANNEL;
            if(verbose) fprintf(stderr, "Outputting both channel and time diff to trigger time.\n");
            continue;
        }

		if(sscanf(argv[i], "--skip=%u", &skip_lines_argument)==1) {
			skip_lines=skip_lines_argument;
			if(verbose) fprintf(stderr, "Skipping first %u lines of input file...\n", skip_lines); 
			continue;
		}
		if(sscanf(argv[i], "--nadc=%u", &n_adcs_argument)==1) {
			if(n_adcs_argument > 1 && n_adcs_argument < N_ADCS_MAX-1) {
				if (verbose) {
					fprintf(stderr, "Number of ADCs set to be %u\n", n_adcs_argument);
				}
				n_adcs=n_adcs_argument;
			} else {
				fprintf(stderr, "Number of ADCs must be higher than 1 but lower than %i!\n", N_ADCS_MAX-1);
				return 0;
			}
			continue;
		}
		if(sscanf(argv[i], "--tablesize=%u", &coinc_table_size_argument)==1) {
			if(coinc_table_size_argument>1) {
				coinc_table_size=coinc_table_size_argument;
				if(verbose) {
					fprintf(stderr, "Coinc table size set to be %u\n", coinc_table_size_argument);
				}
			} else {
				fprintf(stderr, "Coinc table size must be larger than 1!\n");
				return 0;
			}
            continue;
		}
		
		if(sscanf(argv[i], "--trigger=%u", &trigger_adc_argument)==1) {
			trigger_adc=trigger_adc_argument;
            continue;
		}
        
        if(sscanf(argv[i],"--low=%i,%lli", &adc_argument, &time_window_argument)==2) {
            if(verbose) {
                fprintf(stderr, "Set low value %lli for adc %i\n", time_window_argument, adc_argument);
            }
			time_window_low[adc_argument]=time_window_argument;
            continue;
		}
        
        if(sscanf(argv[i], "--high=%i,%lli", &adc_argument, &time_window_argument)==2) {
			time_window_high[adc_argument]=time_window_argument;
            continue;
		}
        if(sscanf(argv[i], "--nevents=%i", &output_n_events)==1) {
            if(output_n_events < 0) {
                output_n_events=0;
            }
            continue;
        }

		if(strcmp(argv[i], "--")==0) {
			fprintf(stderr, "Unrecognized option \"%s\"\n", argv[i]);
			return 0;
		}
        if(strcmp(argv[i], "-")==0) {
            if(read_file!=stdin) {
                read_file=stdin;
            } else {
                output_file=stdout;
            }
            continue;
        }

		if(read_file != stdin) { /* Reading from file already, this parameter must be output filename */
			if(verbose) fprintf(stderr, "Assuming argument no %i \"%s\" is output filename\n",i,argv[i]); 
			fflush(stderr);
			output_file=fopen(argv[i], "w");
			if(!output_file) {
				fprintf(stderr, "Could not open file \"%s\" for output.\n", argv[i]);
				return 0;
			}
		} else { /* This parameter is interpret as input filename */
			if(verbose) fprintf(stderr, "Assuming argument no %i \"%s\" is input filename\n",i,argv[i]);
			fflush(stderr);
			read_file=fopen(argv[i],"r");
			if(!read_file) {
				fprintf(stderr, "Could not open file \"%s\" for input.\n", argv[i]);
				return 0;
			}
		}
		
 	}
	
	if(trigger_adc >= n_adcs) {
		fprintf(stderr, "Number of ADCS set too low or trigger ADC number is too high!\n");
		return 0;
	}
	
	if(verbose) {
		fprintf(stderr, "OPTIONS:\n\tverbose=%i\n\toutput_mode=%i\n\tskip_lines=%i\n\tn_adcs=%i\n\tcoinc_table_size=%u\n\n", verbose, output_mode, skip_lines, n_adcs, coinc_table_size);
	}
	skip_lines++;
	while(skip_lines--) {
		if(!fgets(buffer, 100, read_file)) {
			fprintf(stderr, "Can't skip more lines than there are in the input!\n");
			return 0;
		}
	}
    if(!read_file) {
        fprintf(stderr, "Error: input file could not be read.\n");
        return 0;
    }
	
	for(i=0; i < coinc_table_size/2; i++) {
        insert_blank_event(&coinc_table[i]);
    }
    for(i=coinc_table_size/2; i < coinc_table_size; i++) {
        if(read_event_from_file(read_file, &coinc_table[i], n_adcs)) {
			lines_read++;
			n_adc_events[coinc_table[i].adc]++; 
		} else {
			coinc_table_size=i;
		}

    }

    i=coinc_table_size/2;

	while(coinc_table_size > 1) {
        if(((!(lines_read%1000)) || endgame) && !silent) {
            fprintf(stderr,"%10u LINES READ: %10u coincs\r", lines_read, coincs_found);
        }
        if(coinc_table[i].adc == trigger_adc) {
			adcs_in_coinc=0;
			for(adc=0; adc < n_adcs; adc++) {
				coinc_events[adc]= -1; 
			}
			coinc_events[trigger_adc]=i;
			for(j=1; j<coinc_table_size; j++) {
				k=(i+j)%coinc_table_size;
				time_difference=coinc_table[k].timestamp-coinc_table[i].timestamp;
				if(time_difference >= time_window_low[coinc_table[k].adc] && time_difference <= time_window_high[coinc_table[k].adc] && coinc_table[k].adc!=trigger_adc  && i != k && coinc_table[k].adc != N_ADCS_MAX-1) {
					coinc_events[coinc_table[k].adc]=k;
                }
            }
			for(adc=0; adc < n_adcs; adc++) {
				if (coinc_events[adc] != -1) {
					adcs_in_coinc++;
				}
			}
			if(adcs_in_coinc > 1) {
				for (adc=0; adc < n_adcs; adc++) {
					if(coinc_events[adc] != -1) {
                        n_coinc_adc_events[adc]++;
						switch (output_mode) {
							case MODE_RAW:
								fprintf(output_file, "%u\t", coinc_table[coinc_events[adc]].channel);
								break;
                            case MODE_TIMESTAMPS:
                                fprintf(output_file, "%llu\t", coinc_table[coinc_events[adc]].timestamp);
                                break;
                            case MODE_TIMEDIFF_AND_CHANNEL:
                                fprintf(output_file, "%u\t%i\t", coinc_table[coinc_events[adc]].channel, (int)(coinc_table[coinc_events[adc]].timestamp-coinc_table[coinc_events[trigger_adc]].timestamp));
							    break;
                            case MODE_TIME_AND_CHANNEL:
                                fprintf(output_file, "%u\t%llu\t",coinc_table[coinc_events[adc]].channel, coinc_table[coinc_events[adc]].timestamp);
                                break;
                            default:
								break;
						}

					} else {
                        switch (output_mode) {
                            case MODE_TIME_AND_CHANNEL:
                            case MODE_TIMEDIFF_AND_CHANNEL:
                                fprintf(output_file, "0\t0\t");
                                break;
                            default:
						        fprintf(output_file, "0\t");
                                break;
                            }
					}

				}
                fprintf(output_file, "\n");
				fflush(stdout);
				coincs_found++;
                if(coincs_found == output_n_events)
                    break;
			}
        }
        
        if(endgame) {
            if(endgame==(int)coinc_table_size) {break;}
            endgame++;
            insert_blank_event(&coinc_table[(i+coinc_table_size/2)%coinc_table_size]);
        } else {
			if(!read_event_from_file(read_file, &coinc_table[(i+coinc_table_size/2)%coinc_table_size], n_adcs)) {
				endgame=1;
				if(verbose) fprintf(stderr, "\nEntering endgame (not reading input anymore)\n");
			}
            if(!endgame) {
                lines_read++;
				n_adc_events[coinc_table[i].adc]++;
            }
        }

        i++;
        if(i==coinc_table_size) {
            i=0;
        }
    }
    if(!silent) {
    	fprintf(stderr,"%10u LINES READ: %10u coincs\nDone.\n", lines_read, coincs_found);
	    for(adc=0; adc < n_adcs; adc++) {
            if(n_adc_events[adc]) {
    		    fprintf(stderr, "ADC%i: %i events, %i in coincs (%.1f%%)\n", adc, n_adc_events[adc], n_coinc_adc_events[adc], n_coinc_adc_events[adc]/(0.01*n_adc_events[adc]));
            }
	    }
    }
    return 1;
}
