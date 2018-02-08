#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "libgsto.h"
#include "win_compat.h"

#define C_KEV 1.6021917e-16 /* J */
#define C_AMU 1.66044e-27 /* kg */
#define C_C 2.9979246e+08 /* m/s */
#define C_C2 8.9875518e+16 /* m^2/s^2 */

#define STOPPING_DATA DATAPATH/stoppings.txt
#define MASSES_DATA DATAPATH/masses.dat
#define XSTR(x) STR(x)
#define STR(x) #x

static char *gsto_stopping_types[] ={ /* The first three characters are tested with e.g. strncmp(stopping_types[i], "tot", 3*sizeof(char)). So make them unique. */ 
    "none",
    "nuclear",
    "electronic",
    "total"
};

static char *sto_units[] = {
    "none",
    "eV/(1e15 atoms/cm2)"
};

static char *formats[] = {
    "none",
    "ascii",
    "binary"
};

static char *xscales[] = {
    "none",
    "linear",
    "log10"
};

static char *xunits[] = {
    "none",
    "m/s",
    "keV/u"
};

static char *gsto_headers[] = {
    "      ",
    "source",
    "z1-min",
    "z1-max",
    "z2-min",
    "z2-max",
    "sto-unit",
    "x-unit",
    "format",
    "x-min",
    "x-max",
    "x-points",
    "x-scale"
};

int gsto_add_file(gsto_table_t *table, char *name, char *filename, int Z1_min, int Z1_max, int Z2_min, int Z2_max, char *type) {
    int success=1;
    int i;
#ifdef DEBUG
    fprintf(stderr, "Adding file %s (%s), %i<=Z1<=%i, %i<=Z2<=%i to database.\n", name, filename, Z1_min, Z1_max, Z2_min, Z2_max);  
#endif
    table->files = realloc(table->files, sizeof(gsto_file_t)*(table->n_files+1));
    gsto_file_t *new_file=&table->files[table->n_files];
    new_file->name = calloc(strlen(name), sizeof(char));
    new_file->filename = calloc(strlen(filename), sizeof(char));
    strcpy(new_file->name, name);
    strcpy(new_file->filename, filename);    
    for(i=GSTO_N_STOPPING_TYPES-1; i >=0; i--) {
        if(strncmp(gsto_stopping_types[i], type, 3*sizeof(char))==0) {
            break;
        }
    }
    if(i<=0) {
        return 0; /* No stopping type specified or "none" specified. Perhaps it is not necessary to take this file into account... */
    }
    
    new_file->Z1_min=Z1_min;
    new_file->Z1_max=Z1_max;
    new_file->Z2_min=Z2_min;
    new_file->Z2_max=Z2_max;
    new_file->xmin=0; /* This will be read from the file when loaded */
    new_file->xmax=0; /* Same as this */
    new_file->xscale=0; /* and this */
    new_file->stounit=0;
    new_file->xunit=0;
    if(Z1_min > Z1_max) {
        success=0;
    }
    if(Z2_min > Z2_max) {
        success=0;
    }
    if(success) {
        table->n_files++;
    } else {
        fprintf(stderr, "Error in adding stopping file %s (%s) to database\n", name, filename);
        free(new_file->name);
        free(new_file->filename);
    }
    return success;
    
}

gsto_table_t *gsto_allocate(int Z1_max, int Z2_max) {
    int Z1;
    gsto_table_t *table = malloc(sizeof(gsto_table_t));
    table->Z1_max=Z1_max;
    table->Z2_max=Z2_max;
    table->n_files=0;
    table->files=NULL; /* These will be allocated by gsto_new_file */
    table->assigned_files = (gsto_file_t ***)calloc(Z1_max+1, sizeof(gsto_file_t **));
    table->ele = (double ***)calloc(Z2_max+1, sizeof(double *));
    for(Z1=0; Z1<=Z1_max; Z1++) {
            table->assigned_files[Z1] = (gsto_file_t **)calloc(Z2_max+1, sizeof(gsto_file_t *));
            table->ele[Z1] = (double **)calloc(Z2_max+1, sizeof(double *));
    }
    return table;
}

int gsto_deallocate(gsto_table_t *table) {
    int Z1, i;
    gsto_file_t *file;
    if(!table) {
        return 0;
    }
    for(i=0; i<table->n_files; i++) {
        file=&table->files[i];
        /*free(file->filename);
        free(file->name);*/
    }
    /*free(table->files);*/
    for(Z1=0; Z1<=table->Z1_max; Z1++) {
        free(table->assigned_files[Z1]);
        free(table->ele[Z1]);
    }
    free(table);
    return 1;
}

int gsto_assign(gsto_table_t *table, int Z1, int Z2, gsto_file_t *file) { /* Used internally, can be used after init to override autoinit */
    table->assigned_files[Z1][Z2] = file;
    return 1;
}

int gsto_load_binary_file(gsto_table_t *table, gsto_file_t *file) {
    int Z1, Z2;
#ifdef DEBUG
    fprintf(stderr, "Loading binary data.\n");
#endif
    for (Z1=file->Z1_min; Z1<=file->Z1_max; Z1++) {
        for (Z2=file->Z2_min; Z2<=file->Z2_max; Z2++) {
            if (table->assigned_files[Z1][Z2] == file) {
                table->ele[Z1][Z2] = malloc(sizeof(double)*file->xpoints);
                fread(&table->ele[Z1][Z2], sizeof(double), file->xpoints, file->fp);
            } else {
                fseek(file->fp, sizeof(double)*file->xpoints, SEEK_CUR);
            }
        }
    }
    return 1;
}

int gsto_load_ascii_file(gsto_table_t *table, gsto_file_t *file) { 
    int Z1, Z2, previous_Z1=file->Z1_min, previous_Z2=file->Z2_min-1, skip, i;
    char *line = calloc(GSTO_MAX_LINE_LEN, sizeof(char));
    int actually_skipped=0;
#ifdef DEBUG
    fprintf(stderr, "Loading ascii data.\n");
#endif
    
    for (Z1=file->Z1_min; Z1<=file->Z1_max && Z1<=table->Z1_max; Z1++) {
        for (Z2=file->Z2_min; Z2<=file->Z2_max && Z2<=file->Z2_max; Z2++) {
            if (table->assigned_files[Z1][Z2] == file) { /* This file is assigned to this Z1, Z2 combination, so we have to load the stopping in. */
                skip=file->xpoints*((Z1-previous_Z1)*(file->Z2_max-file->Z2_min+1)+(Z2-previous_Z2)-1); /* Not sure if correct */
#ifdef DEBUG
                fprintf(stderr, "Skipping %i lines.\n", skip);
                actually_skipped=0;
#endif

                while (skip--) {
                    file->lineno++;
                    if(!fgets(line, GSTO_MAX_LINE_LEN, file->fp))
                        break;
                    
                    if(*line == '#') {
                        skip++; /* Undoing skip-- */
#ifdef DEBUG
                        fprintf(stderr, "Comment on line %i: %s", file->lineno, line+1);
#endif
                    } 
                    actually_skipped++;
                }
#ifdef DEBUG
                fprintf(stderr, "actually skipped %i lines\n", actually_skipped);
#endif
                table->ele[Z1][Z2] = malloc(sizeof(double)*file->xpoints);
                for(i=0; i<file->xpoints; i++) {
                    if(!fgets(line, GSTO_MAX_LINE_LEN, file->fp)) {
#ifdef DEBUG
                        fprintf(stderr, "File %s ended prematurely when reading Z1=%i Z2=%i stopping point=%i/%i.\n", file->filename, Z1, Z2, i+1, file->xpoints);
#endif
                        break;
                    }
                    file->lineno++;
                    if(*line == '#') { /* This line is a comment. Ignore. */
                        i--;
                    } else {
                        table->ele[Z1][Z2][i] = strtod(line, NULL);
                    }
                }
                previous_Z1=Z1;
                previous_Z2=Z2;
                
            }
        }
    }
    free(line);
    return 1;
}

int gsto_load(gsto_table_t *table) { /* For every file, load combinations from file */
    int i;
    gsto_file_t *file;
    char *line=calloc(GSTO_MAX_LINE_LEN, sizeof(char));
    char *line_split;
    char *columns[3];
    char **col;
    int header=0, property;
    for(i=0; i<table->n_files; i++) {
        file=&table->files[i];
        file->fp=fopen(file->filename, "r");
        if(!file->fp) {
            fprintf(stderr, "Could not open file %s for reading.\n", file->filename);
            return 0;
        }
        /* parse headers, stop when end of headers found */
        while (fgets(line, GSTO_MAX_LINE_LEN, file->fp) != NULL) {
            file->lineno++;
            if(strncmp(line, GSTO_END_OF_HEADERS, strlen(GSTO_END_OF_HEADERS))==0) {
#ifdef DEBUG
                fprintf(stderr, "End of headers on line %i of settings file.\n", file->lineno);
#endif
                break;
            }
            line_split=line;
            for (col = columns; (*col = strsep(&line_split, "=\n\r\t")) != NULL;)
                if (**col != '\0')
                    if (++col >= &columns[3])
                        break;
#ifdef DEBUG
            fprintf(stderr, "Line %i, property %s is %s.\n", file->lineno, columns[0], columns[1]);
#endif 
            for(header=0; header < GSTO_N_HEADER_TYPES; header++) {
#ifdef DEBUG
                fprintf(stderr, "Does \"%s\" match \"%s\"? ", columns[0], gsto_headers[header]);
#endif
                if(strncmp(columns[0], gsto_headers[header], strlen(gsto_headers[header]))==0) {
#ifdef DEBUG
                    fprintf(stderr, "Yes.\n");
#endif
                    switch (header) {
                        case GSTO_HEADER_FORMAT:
                            for(property=0; property<GSTO_N_STO_UNITS; property++) {
                                if(strncmp(formats[property], columns[1], strlen(formats[property]))==0) {
                                    file->data_format=property;
                                }
                            }
                            break;
                        case GSTO_HEADER_STOUNIT:
                            for(property=0; property<GSTO_N_STO_UNITS; property++) {
                                if(strncmp(sto_units[property], columns[1], strlen(sto_units[property]))==0) {
                                    file->stounit=property;
                                }
                            }
                            break;
                        case GSTO_HEADER_XSCALE:
                            for(property=0; property<GSTO_N_X_SCALES; property++) {
                                if(strncmp(xscales[property], columns[1], strlen(xscales[property]))==0) {
                                    file->xscale=property;
                                }
                            }
                            break;
                        case GSTO_HEADER_XUNIT:
                            for(property=0; property<GSTO_N_X_UNITS; property++) {
                                if(strncmp(xunits[property], columns[1], strlen(xunits[property]))==0) {
                                    file->xunit=property;
                                }
                            }
                            break;
                        case GSTO_HEADER_XPOINTS:
                            file->xpoints=strtol(columns[1], NULL, 10);
#ifdef DEBUG
                            fprintf(stderr, "Set number of x points to %i\n", file->xpoints);
#endif
                            break;
                        case GSTO_HEADER_XMIN:
                            file->xmin=strtod(columns[1], NULL);
#ifdef DEBUG
                            fprintf(stderr, "Set minimum value of table to be %lf\n", file->xmin);
#endif
                            break;
                        case GSTO_HEADER_XMAX:
                            file->xmax=strtod(columns[1], NULL);
#ifdef DEBUG
                            fprintf(stderr, "Set maximum value of table to be %lf\n", file->xmax);
#endif
                            break;
                        default:
                            break;
                    }
                    break;
                } else {
#ifdef DEBUG
                    fprintf(stderr, "No.\n");
#endif
                }
            } 
        }
        switch (file->data_format) {
            case GSTO_DF_DOUBLE:
                gsto_load_binary_file(table, file);
                break;
            case GSTO_DF_ASCII:
            default:
                gsto_load_ascii_file(table, file);
                break;
        }
        fclose(file->fp);
    }
    free(line);
    return 1;
}

int gsto_print_files(gsto_table_t *table) {
    int i, Z1, Z2;
    int assignments;
    gsto_file_t *file;
    fprintf(stderr, "LIST OF AVAILABLE STOPPING FILES FOLLOWS\n=====\n");
    
    for(i=0; i<table->n_files; i++) {
        assignments=0;
        file=&table->files[i];
        for (Z1=1; Z1<=table->Z1_max; Z1++) {
            for (Z2=1; Z2<=table->Z2_max; Z2++) {
                if(table->assigned_files[Z1][Z2]==file) {
                    assignments++;
                }
            }        
        }
        fprintf(stderr, "%i: %s (%s), %i assignments, %i<=Z1<=%i, %i<=Z2<=%i. x-points=%i, x-scale=%s, x-unit=%s, stopping unit=%s, format=%s\n", i, file->name, file->filename, assignments, file->Z1_min, file->Z1_max, file->Z2_min, file->Z2_max, file->xpoints, xscales[file->xscale], xunits[file->xunit], sto_units[file->stounit], formats[file->data_format]);  
    }
    fprintf(stderr, "=====\n");
    return 1;
}

int gsto_print_assignments(gsto_table_t *table) {
    int Z1, Z2;
    fprintf(stderr, "LIST OF ASSIGNED STOPPING FILES FOLLOWS\n=====\n");
    for (Z1=1; Z1<=table->Z1_max; Z1++) {
        for (Z2=1; Z2<=table->Z2_max; Z2++) {
            if(table->assigned_files[Z1][Z2]) {
                fprintf(stderr, "Stopping for Z1=%i in Z2=%i assigned to file %s.\n", Z1, Z2, table->assigned_files[Z1][Z2]->name);
            } else {
#ifdef DEBUG
                fprintf(stderr, "Stopping for Z1=%i in Z2=%i not assigned.\n", Z1, Z2);
#endif
            }
        }        
    }
    fprintf(stderr, "=====\n");
    return 1;
}

int gsto_auto_assign_range(gsto_table_t *table, int Z1_min, int Z1_max, int Z2_min, int Z2_max) {
    int Z1, Z2;
    if(Z1_max > table->Z1_max)
        Z1_max=table->Z1_max;
    if(Z2_max > table->Z2_max)
        Z2_max=table->Z2_max;
    for(Z1=Z1_min; Z1<=Z1_max; Z1++) {
        for(Z2=Z2_min; Z2<=Z2_max; Z2++) {
            gsto_auto_assign(table, Z1, Z2);
        }
    }
    return 1;
}

int gsto_auto_assign(gsto_table_t *table, int Z1, int Z2) {
    gsto_file_t *file;
    int success=0, i;
    for (i=0; i<table->n_files; i++) {
        file=&table->files[i];
        if (file->Z1_min<=Z1 && file->Z1_max >= Z1 && file->Z2_min <= Z2 && file->Z2_max >= Z2) { /*File includes this Z1, Z2 combination*/
            gsto_assign(table, Z1, Z2, file);
            success=1;
            break; /* Stop when the first file to include this combination is found */
        }
    }
    return success;
}

gsto_table_t *gsto_init(int Z_max, char *stoppings_file_name) {
    int i=0, n_files=0, n_errors=0;
    char *line=calloc(GSTO_MAX_LINE_LEN, sizeof(char));
    char *line_split;
    char *columns[8];
    char **col;
    FILE *settings_file=NULL;
    gsto_table_t *table;
    table = gsto_allocate(Z_max, Z_max); /* Allocate memory for assignment table, initialize some variables */
    if(stoppings_file_name) { /* If filename given (not NULL), attempt to load settings file */
        settings_file=fopen(stoppings_file_name, "r");
    } else {
#ifdef DEBUG
        fprintf(stderr, "GSTO: No settings file given.\n");
#endif
    }
    if(settings_file) { /* If file could be opened, try to read it */
        while (fgets(line, GSTO_MAX_LINE_LEN, settings_file) != NULL) {
            i++;
            if(line[0] == '#') /* Strip comments */
                continue;
            line_split=line; /* strsep will screw up line_split, reset for every new line */
            for (col = columns; (*col = strsep(&line_split, " \t\r\n")) != NULL;)
                if (**col != '\0')
                    if (++col >= &columns[8])
                        break;
            if(gsto_add_file(table, columns[7], columns[0], strtol(columns[2], NULL, 10), strtol(columns[3], NULL, 10), strtol(columns[4], NULL, 10), strtol(columns[5], NULL, 10), columns[1])) {
                n_files++;
            } else {
                n_errors++;
            }
            
        }
#ifdef DEBUG
        fprintf(stderr, "GSTO: Read %i lines from settings file, added %i files, attempt to add %i files failed.\n", i, n_files, n_errors);
#endif
        fclose(settings_file);
    } else {
        fprintf(stderr, "GSTO: Could not open settings file! No stopping files added.\n");
    }
    return table;
}

double gsto_sto_raw(gsto_table_t *table, int Z1, int Z2, int point_number) {
    if (Z1 <= 0 || Z1 > table->Z1_max) {
        fprintf(stderr, "Z1=%i out of range!\n", Z1);
        return 0;
    }
    if (Z2 <= 0 || Z2 > table->Z2_max) {
        fprintf(stderr, "Z2=%i out of range!\n", Z2);
        return 0;
    }
    /* Now Z1 and Z2 should be sane, let's check if point_number is */
    if(point_number <= 0 || point_number >= table->assigned_files[Z1][Z2]->xpoints) {
        fprintf(stderr, "Stopping point = %i out of range!\n", point_number);
        return 0;
    }
    /* No stopping loaded */
    if(table->assigned_files[Z1][Z2] == NULL) {
        fprintf(stderr, "No stopping file assigned to Z1=%i Z2=%i\n", Z1, Z2);
        return 0;
    }
    /* Sanity checked, just return the value */
    return table->ele[Z1][Z2][point_number];
}

double gsto_sto_v(gsto_table_t *table, int Z1, int Z2, double v) { /* Simplest way to access stopping data */
    int i;
    double i_float, x, gamma, sto_low, sto_high, sto;
    gsto_file_t *file;
    if (Z1 <= 0 || Z1 > table->Z1_max) {
        fprintf(stderr, "Z1=%i out of range!\n", Z1);
        return 0;
    }
    if (Z2 <= 0 || Z2 > table->Z2_max) {
        fprintf(stderr, "Z2=%i out of range!\n", Z2);
        return 0;
    }
    /* Now Z1 and Z2 should be sane */
    file = table->assigned_files[Z1][Z2];
    /* No stopping loaded */
    if(table->assigned_files[Z1][Z2] == NULL) {
        fprintf(stderr, "No stopping file assigned to Z1=%i Z2=%i\n", Z1, Z2);
        return 0;
    }
    
    
    /* Scale v to "native" velocity, i.e. units of the file. */
    switch (file->xunit) {
        case GSTO_X_UNIT_KEV_U:
            gamma=1.0/(sqrt(1-pow(v,2.0)/C_C2));
            x=(gamma-1)*C_C2/(C_KEV/C_AMU);
            /* x=0.5*1.0363554e-11*pow(v,2.0);*/ /* conversion from m/s to keV/amu (classical) */
            break;
        case GSTO_X_UNIT_M_S:
        default:
            x=v;
            break;
    }
    if(x <= file->xmin) {
#ifdef DEBUG
        fprintf(stderr, "Velocity out of range (too low, requested %e, min %e)!\n", x, file->xmin);
#endif
        return 0.0;
        return table->ele[Z1][Z2][0];
    }
    if(x >= file->xmax) {
#ifdef DEBUG
        fprintf(stderr, "Velocity out of range (too high, requested %e, max %e)!\n", x, file->xmax);
#endif
        return 0.0;
        return table->ele[Z1][Z2][file->xpoints-1];
    }

    /* Apply scaling of x to indices of tabulated stopping */

    switch (file->xscale) {
        case GSTO_XSCALE_LOG10:
            i_float = (log10(x)-log10(file->xmin))/(log10(file->xmax)-log10(file->xmin)) * (file->xpoints-1);
            break;
        case GSTO_XSCALE_LINEAR:
        default:
            i_float = (x-file->xmin)/(file->xmax-file->xmin) * (file->xpoints-1);
            break;
    }
    i = (int) floor(i_float);
    sto_low = table->ele[Z1][Z2][i];
    sto_high = table->ele[Z1][Z2][i+1];
    sto = ((sto_high-sto_low)*(i_float-1.0*i))+sto_low;
    return sto;
}

double *gsto_sto_v_table(gsto_table_t *table, int Z1, int Z2, double v_min, double v_max, int points) {
    double *stoppings_out = malloc(sizeof(double)*points);
    double v_step=(v_max-v_min)/(points-1.0);
    double v;
    int i;
    for(i=0; i<points; i++) {
        v=v_step*i+v_min;
        stoppings_out[i]=gsto_sto_v(table, Z1, Z2, v);
#ifdef DEBUG
        fprintf(stderr, "%i/%i Calculating stopping for Z1=%i Z2=%i v=%e. Got %e.\n", i, points, Z1, Z2, v, stoppings_out[i]);
#endif
    }
    return stoppings_out;
}

