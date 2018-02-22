/* 
    Copyright (C) 2013 Jaakko Julin <jaakko.julin@jyu.fi>
    See file LICENCE for a copy of the GNU General Public Licence
*/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <math.h>
#include <unistd.h>
#include <gsto_masses.h>
#include <errno.h>

#ifdef WIN32
#include "win_compat.h"
#endif



#define SRIM_OUTPUT_N_HEADERS 4 /* this number of rows in the beginning of SR Module output are headers */
#define SRIM_OUTPUT_LINE_LENGTH 80 /* max length of line */

#ifdef WIN32
#define SR_MODULE_PATH "SRModule.exe"
#else
#define SR_MODULE_PATH "wine SRModule.exe"
#endif
#define SR_FILE_PATH "SR.IN"
#define SR_OUTPUT_FILE "stopping.dat"

#define XSTR(x) STR(x)
#define STR(x) #x

#define XSTEPS 101
#define Z_MAX 92

int generate_sr_in(char *out_filename, isotope_t *ion, isotope_t *target, int xsteps, double xmin, double xmax) {
    FILE *sr_file = fopen(out_filename, "w");
    int i;
    double x;
    if(!sr_file) {
        fprintf(stderr, "Could not open SR.IN for writing!\n");
        return 0;
    }
    fprintf(sr_file, "---Stopping/Range Input Data (Number-format: Period = Decimal Point)\r\n");
    fprintf(sr_file, "---Output File Name\r\n");
    fprintf(sr_file, "\"%s\"\r\n", SR_OUTPUT_FILE);
    fprintf(sr_file, "---Ion(Z), Ion Mass(u)\r\n");
    fprintf(sr_file, "%i   %lf\r\n", ion->Z, ion->mass/AMU);
    fprintf(sr_file, "---Target Data: (Solid=0,Gas=1), Density(g/cm3), Compound Corr.\r\n");
    fprintf(sr_file, "0    1      1\r\n");
    fprintf(sr_file, "---Number of Target Elements\r\n");
    fprintf(sr_file, "1\r\n");
    fprintf(sr_file, "---Target Elements: (Z), Target name, Stoich, Target Mass(u)\r\n");
    fprintf(sr_file, "%i   \"%s\"   100   %lf\r\n", target->Z, target->name, target->mass/AMU);
    fprintf(sr_file, "---Output Stopping Units (1-8)\r\n");
    fprintf(sr_file, "7\r\n");
    fprintf(sr_file, "---Ion Energy : E-Min(keV), E-Max(keV)\r\n");
    fprintf(sr_file, "0  0\r\n");
    for(i=0; i<xsteps; i++) {
        x=xmin*pow(xmax/xmin,1.0*i/(xsteps-1)); /* keV/amu in log scale */
        fprintf(sr_file, "%lf\r\n", x*ion->mass/AMU);
    }
    fclose(sr_file);
    return 1;
}

int run_srim(char *sr_module_path) {
    int result;
    result=system(sr_module_path);
    if(result==-1 || result==127) 
        return 0;
    return 1;
}

int parse_output(char *filename, FILE *stopping_output_file, isotope_t *ion, int xsteps) {
    int lineno=0, i=1;
    FILE *in_file=fopen(filename, "r");
    char *columns[3];
    char **col;
    if(!in_file)
        return 0;
    char *line=malloc(sizeof(char)*SRIM_OUTPUT_LINE_LENGTH);
    char *line_split;
    double energy, S_elec, S_nuc;
    while(fgets(line, SRIM_OUTPUT_LINE_LENGTH, in_file) != NULL) {
        lineno++;
        if(lineno<=SRIM_OUTPUT_N_HEADERS) /* Headers */
            continue;
        line_split=line; /* strsep will screw up line_split, reset for every new line */
        /*if(i>xsteps) 
            break;*/
        for (col = columns; (*col = strsep(&line_split, " \t")) != NULL;)
            if (**col != '\0')
                if (++col >= &columns[3])
                    break;
        energy=strtod(columns[0], NULL);
        S_elec=strtod(columns[1], NULL);
        S_nuc=strtod(columns[2], NULL);
        /*
        fprintf(stdout, "%e\t%e\t%e\t%e\t\n", energy/ion->mass, S_elec, S_nuc, S_elec+S_nuc);
        */
        fprintf(stopping_output_file, "%e\n", S_elec+S_nuc);
        i++;
    }
    fflush(stopping_output_file);
    free(line);
    fclose(in_file);
    return lineno;
}

void remove_newline(char *s) {
    int i;
    for(i=0; i<strlen(s); i++) {
        if(s[i] == '\n' || s[i] == '\r')
            s[i]='\0';
    }
}


int main (int argc, char **argv) {
    isotopes_t *isotopes=load_isotope_table(XSTR(MASSES_DATA));
    if(!isotopes) {
        fprintf(stderr, "Could not load table of isotopes from %s!\n", XSTR(MASSES_DATA));
        return 0;
    }
    int Z1, Z2, i, j;
    double xmin=10.0; /* keV/amu */
    double xmax=10000.0; 
    int xsteps=XSTEPS; /* steps numbered 0, 1, 2, ...., vsteps-1 */
    int z1_min=1;
    int z2_min=1;
    int z1_max=Z_MAX; 
    int z2_max=Z_MAX;
    int n_combinations;
    isotope_t *ion, *target;
    FILE *stopping_output_file;
    i=0;
    char *input=malloc(sizeof(char)*1000);
    fprintf(stderr, "Please enter output filename, e.g. \"srim.tot\": ");
    fgets(input, 1000, stdin);
    remove_newline(input); 
    stopping_output_file = fopen(input, "w");
    if(!stopping_output_file) {
        fprintf(stderr, "Could not open file \"%s\" for output", input);
        return 0;
    }
#ifdef WIN32 
    fprintf(stderr, "Please enter SRIM path, e.g. \"C:\\SRIM\\SR Module\\\": ");
#else
    fprintf(stderr, "Please enter SRIM path, e.g. \"/home/user/.wine/drive_c/SRIM/SR Module/\"\n> ");
#endif
    char *srim_path=malloc(sizeof(char)*2000);
    fgets(srim_path, 2000, stdin);
    remove_newline(srim_path);
    fprintf(stderr, "Attempting to chdir to \"%s\"\n", srim_path);
    if(chdir(srim_path) != 0) {
        fprintf(stderr, "Could not chdir to given path. Error number %i.\n", errno);
        return 0;
    }
    fprintf(stderr, "Input minimum energy in keV/u (e.g. 10): ");
    fgets(input, 1000, stdin);
    xmin=strtod(input, NULL);
    fprintf(stderr, "Input maximum energy in keV/u (e.g. 10000): ");
    fgets(input, 1000, stdin);
    xmax=strtod(input, NULL);
    fprintf(stderr, "Input number of stopping steps to calculate between xmin and xmax in log scale (e.g. 101): ");
    fgets(input, 1000, stdin);
    xsteps=strtol(input, NULL, 10);
    fprintf(stderr, "Input Z1 minimum (e.g. 1): ");
    fgets(input, 1000, stdin);
    z1_min=strtol(input, NULL, 10);
    fprintf(stderr, "Input Z1 maximum (e.g. 92): ");
    fgets(input, 1000, stdin);
    z1_max=strtol(input, NULL, 10);
    fprintf(stderr, "Input Z2 minimum (e.g. 1): ");
    fgets(input, 1000, stdin);
    z2_min=strtol(input, NULL, 10);
    fprintf(stderr, "Input Z2 maximum (e.g. 92): ");
    fgets(input, 1000, stdin);
    z2_max=strtol(input, NULL, 10);
    n_combinations = (z1_max-z1_min+1)*(z2_max-z2_min+1);

    fprintf(stopping_output_file, "source=srim\nz1-min=%i\nz1-max=%i\nz2-min=%i\nz2-max=%i\nsto-unit=eV/(1e15 atoms/cm2)\nx-unit=keV/u\nformat=ascii\nx-min=%e\nx-max=%e\nx-points=%i\nx-scale=log10\n==END-OF-HEADER==\n", z1_min, z1_max, z2_min, z2_max, xmin, xmax, xsteps);
    i=0;
    for(Z1=z1_min; Z1<=z1_max; Z1++) {
        ion = find_most_abundant_isotope(isotopes, Z1);
        for(Z2=z2_min; Z2<=z2_max; Z2++) {
            i++;
            target = find_most_abundant_isotope(isotopes, Z2);
            fprintf(stopping_output_file, "#STOPPING IN Z1=%i Z2=%i\n", Z1, Z2);
            if(ion && target) {
                fprintf(stderr, "SR.IN will be generated for %s in %s.\n", ion->name, target->name);
                generate_sr_in(SR_FILE_PATH, ion, target, xsteps, xmin, xmax);
                fprintf(stderr, "Running SRModule, please wait.\n");
                if(run_srim(SR_MODULE_PATH)) {
                    if(parse_output(SR_OUTPUT_FILE, stopping_output_file, ion, xsteps)) {
                        fprintf(stderr, "Z1=%i. Z2=%i. OK. %i/%i.\n", Z1, Z2, i, n_combinations);
                    } else {
                        fprintf(stderr, "Z1=%i. Z2=%i. Not OK %i/%i.\n", Z1, Z2, i, n_combinations);
                    }
                } else {
                    fprintf(stderr, "Error in running SRModule. You should really consider running this program in the working directory of SR Module.\n");
                    exit(0);
                }
            } else {
                for(j=0; j<xsteps; j++) {
                    fprintf(stopping_output_file, "%e\n", 0.0); /* no isotopes found for either Z1 or Z2, fill with zeros */
                }
                fflush(stdout);
            }
        }
        sleep(1);
    }
    free(isotopes);
    return 1;
}
