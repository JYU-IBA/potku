/*
   Copyright (C) 2013 Jaakko Julin <jaakko.julin@jyu.fi>
   See file LICENCE for a copy of the GNU General Public Licence
*/


#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include "libsrim.h"

#ifdef ZBL96
#include "zbl96.h"
#endif


#define STOP_DATA DATAPATH/stopping.bin
#define XSTR(x) STR(x)
#define STR(x) #x

#define P_NA     6.0221367e23
#define P_E      1.60217733e-19
#define C_EV     P_E
#define C_MEV       (1000000.0*C_EV)
#define C_MEVCM2_UG 1.0e-27

#define Z_C 6 /* Carbon */
#define M_C 12.0


int main (int argc, char **argv) {
   if(argc != 2) {
        fprintf(stderr, "%s: Wrong number of arguments (%i)!\nUsage: %s foil_thickness\n", argv[0], argc, argv[0]);
        return 0;
    }
    char *incident_name=malloc(sizeof(char)*32);
    double foil_thickness=strtod(argv[1], NULL);
    isotopes_t *isotopes=load_isotope_table(XSTR(MASSES_FILE));
#ifndef ZBL96
    stopping_t *stopping=init_stopping_table(XSTR(STOP_DATA));
    if(!stopping)
        return 0;
#endif
    double S,E;
#ifdef ZBL96
    int n;
    double **sto;
#endif
    unsigned int flag = (ZBL_EV_1E15ATOMS_CM2 | ZBL_MEV | ZBL_N_BOTH);
    while(fscanf(stdin, "%s %lf", incident_name, &E)==2) {
        isotope_t *incident=find_isotope_by_name(isotopes, incident_name);
        if(!incident) {
            fprintf(stderr, "No such isotope exists!\n");
            return 0;
        }

#ifdef ZBL96
        sto = zbl96(incident->Z,Z_C,incident->mass,M_C,0.0,0.0,E,E,flag,&n); /* stopping from 0 to E, every E => table of two rows */
        S=sto[1][1]; /* S(E) */
        free(sto);
#else  
        S=srim_stop_isotope(stopping, incident, Z_C, E*1000.0);
#endif
        fprintf(stdout, "%i %i %e %e %e\n", incident->Z, incident->A, E, S, S*C_MEVCM2_UG*P_NA/M_C*foil_thickness);  
    }
    return 1;
}
