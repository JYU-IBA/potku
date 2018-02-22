/* 
    Copyright (C) 2013 Jaakko Julin <jaakko.julin@jyu.fi>
    See file LICENCE for a copy of the GNU General Public Licence
*/

#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <math.h>
#include <unistd.h>
#include "libsrim.h"



#define SRIM_OUTPUT_N_HEADERS 4 /* this number of rows in the beginning of SR Module output are headers */



#define SR_MODULE_PATH "wine SRModule.exe"
#define SR_FILE_PATH "SR.IN"
#define SR_OUTPUT_FILE "stopping.dat"
#define STOP_DATA_OUT DATAPATH/stopping.bin

#define XSTR(x) STR(x)
#define STR(x) #x

#define VSTEPS 1000
#define Z_MAX 113


#define V_MAX 0.05*SPEED_OF_LIGHT /* 5 % of the speed of light, should be enough for most of ERD. Not enough for everything! */





int generate_sr_in(char *out_filename, isotope_t *ion, isotope_t *target, int vsteps, double vmax) {
    FILE *sr_file = fopen(out_filename, "w");
    int i;
    if(!sr_file) return 0;
    fprintf(sr_file, "---Stopping/Range Input Data (Number-format: Period = Decimal Point)\r\n");
    fprintf(sr_file, "---Output File Name\r\n");
    fprintf(sr_file, "\"%s\"\r\n", SR_OUTPUT_FILE);
    fprintf(sr_file, "---Ion(Z), Ion Mass(u)\r\n");
    fprintf(sr_file, "%i   %lf\r\n", ion->Z, ion->mass);
    fprintf(sr_file, "---Target Data: (Solid=0,Gas=1), Density(g/cm3), Compound Corr.\r\n");
    fprintf(sr_file, "0    1      1\r\n");
    fprintf(sr_file, "---Number of Target Elements\r\n");
    fprintf(sr_file, "1\r\n");
    fprintf(sr_file, "---Target Elements: (Z), Target name, Stoich, Target Mass(u)\r\n");
    fprintf(sr_file, "%i   \"%s\"   100   %lf\r\n", target->Z, target->name, target->mass);
    fprintf(sr_file, "---Output Stopping Units (1-8)\r\n");
    fprintf(sr_file, "7\r\n");
    fprintf(sr_file, "---Ion Energy : E-Min(keV), E-Max(keV)\r\n");
    fprintf(sr_file, "0  0\r\n");
    double v;
    for(i=1; i<=vsteps; i++) {
        v=vmax*(1.0*i/(1.0*vsteps));
        fprintf(sr_file, "%lf\r\n", energy_from_velocity(v, ion->mass));
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

int parse_output(char *filename, double *total_stopping_out, isotope_t *ion, int vsteps, double vmax) {
    int lineno=0, i=1;
    FILE *in_file=fopen(filename, "r");
    char *columns[3];
    char **col;
    if(!in_file)
        return 0;
    char *line=malloc(sizeof(char)*LINE_LENGTH);
    char *line_split;
    double energy, S_elec, S_nuc;
    while(fgets(line, LINE_LENGTH-1, in_file) != NULL) {
        lineno++;
        if(lineno<=SRIM_OUTPUT_N_HEADERS) /* Headers */
            continue;
        line_split=line; /* strsep will screw up line_split, reset for every new line */
        if(i>vsteps) 
            break;
        for (col = columns; (*col = mystrsep(&line_split, " \t")) != NULL;)
            if (**col != '\0')
                if (++col >= &columns[3])
                    break;
        energy=strtod(columns[0], NULL);
        S_elec=strtod(columns[1], NULL);
        S_nuc=strtod(columns[2], NULL);
        *(total_stopping_out+(i-1)) = S_elec+S_nuc;
 /*     fprintf(stderr, "%e\t%e\t%e\t%e\t%e\t%e\n", vmax*(1.0*i/(1.0*vsteps)), energy_from_velocity(vmax*(1.0*i/(1.0*vsteps)), ion), energy, S_elec, S_nuc, S_elec+S_nuc);
   */     i++;
    }
    free(line);
    fclose(in_file);
    return lineno;
}

int main (int argc, char **argv) {
    isotopes_t *isotopes=load_isotope_table(XSTR(MASSES_FILE));
    if(!isotopes) {
        fprintf(stderr, "Could not load table of isotopes from %s!\n", XSTR(MASSES_FILE));
        return 0;
    }
    int Z1, Z2, i;
    /*
    for(i=0; i<isotopes->n_isotopes; i++) {
        isotope=&isotopes->i[i];
        if(isotope->abundance > 1e-4) {
            fprintf(stdout, "%i %i %i %s %lf %lf\n", isotope->N, isotope->A, isotope->Z, isotope->name, isotope->mass, isotope->abundance);
        }
    }
    */
    double vmax, vdiv;
    int vsteps=VSTEPS; /* steps numbered 1, 2, 3, ...., vsteps-1, vsteps */
    int z_max=Z_MAX; /* 1 < Z < z_max */ 
    double *stoppings=malloc(sizeof(double)*z_max*z_max*vsteps);
    for(Z1=0; Z1<z_max; Z1++) {
        for(Z2=0; Z2<z_max; Z2++) {
            for(i=1; i<=vsteps; i++) {
                *(stoppings+((Z1*z_max+Z2)*vsteps+(i-1)))=0.0;
            }
        }

    }
    vmax=V_MAX;
    vdiv=vmax/(1.0*vsteps); /* step number "vsteps" corresponds to vmax, while step number 1 is (1/vsteps)*vmax */
    fprintf(stderr, "v_max set to %e m/s (%lf%% c)\n", vmax, 100*vmax/SPEED_OF_LIGHT);
    fprintf(stderr, "number of v steps set to %i\n", vsteps);
    fprintf(stderr, "v_div therefore %e m/s\n", vdiv);
    isotope_t *ion, *target;
    i=0;
    for(Z1=1; Z1<z_max; Z1++) {
        ion = find_most_abundant_isotope(isotopes, Z1);
        /*if(!ion)
            ion = find_first_isotope(isotopes, Z1); */
        for(Z2=1; Z2<z_max; Z2++) {
            i++;
            target = find_most_abundant_isotope(isotopes, Z2);
            /*
            if(!target) 
                target = find_first_isotope(isotopes, Z2);
            */
            if(ion && target) {
                fprintf(stderr, "SR.IN will be generated for %s in %s.\n", ion->name, target->name);
                generate_sr_in(SR_FILE_PATH, ion, target, vsteps, vmax);
                fprintf(stderr, "Running SRModule, please wait.\n");
                fprintf(stderr, "Z1=%i. Z2=%i. OK. %i/%i.\n", Z1, Z2, i, (z_max-1)*(z_max-1));

#ifdef DEBUG
                sleep(1);
#endif
            }
        } 
    }
    FILE *output_file=fopen(XSTR(STOP_DATA_OUT), "w");
    double v;
    if(output_file) {
        fprintf(stderr, "Writing output, please wait!\n");
        fwrite(&z_max, sizeof(int), 1, output_file);
        fwrite(&vsteps, sizeof(int), 1, output_file);
        for(i=1; i<=vsteps; i++) {
            v=vmax*(1.0*i/(1.0*vsteps));
            fwrite(&v, sizeof(double), 1, output_file);
        }
        fwrite(stoppings, sizeof(double), z_max*z_max*vsteps, output_file);
        fclose(output_file);
        fprintf(stderr, "Done.\n");
    }
    free(stoppings);
    free(isotopes);
    return 1;
}
