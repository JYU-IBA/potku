/*
   Copyright (C) 2013 Jaakko Julin <jaakko.julin@jyu.fi>
   See file LICENCE for a copy of the GNU General Public Licence
*/


#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

#include "libsrim.h"

#define STOP_DATA DATAPATH/stopping.bin
#define XSTR(x) STR(x)
#define STR(x) #x


int main (int argc, char **argv) {
   if(argc != 6) {
        fprintf(stderr, "%s: Wrong number of arguments (%i)!\nUsage: %s [incident isotope] [target isotope] [E_low] [E_step] [E_high]\n", argv[0], argc, argv[0]);
        return 0;
    }

    isotopes_t *isotopes=load_isotope_table(XSTR(MASSES_FILE));
    isotope_t *incident=find_isotope_by_name(isotopes, argv[1]);
    isotope_t *target=find_isotope_by_name(isotopes, argv[2]);
    double E_low = strtod(argv[3], NULL);
    double E_step = strtod(argv[4], NULL);
    double E_high = strtod(argv[5], NULL);
    if(!incident || !target) {
        fprintf(stderr, "No such isotope exists!\n");
    }
    stopping_t *stopping=init_stopping_table(XSTR(STOP_DATA));
    if(!stopping)
        return 0;
    double E;
    for(E=E_low; E<E_high; E += E_step) {
        fprintf(stdout, "%e %e\n", E, srim_stop_isotope(stopping, incident, target->Z, E));  
    }
    return 1;
}
