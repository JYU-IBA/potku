#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libgsto.h>
#include <gsto_masses.h>



int get_single_stop(gsto_table_t *table, isotope_t *incident, double E, int Z2) {
    double v;
    v=velocity(E, incident->mass);
    fprintf(stderr, "Printing stopping for %i in %i at v=%e m/s from file %s.\n", incident->Z, Z2, v, table->assigned_files[incident->Z][Z2]->name);
    printf("%e\n", gsto_sto_v(table, incident->Z, Z2, v));
    return 1; 
}

int main(int argc, char **argv) {
    int Z2=0;
    gsto_table_t *table;
    isotopes_t *isotopes;
    isotope_t *incident;
    double E;
    char *incident_name, *target_name, *E_unit_str;
    if(argc != 4) {
        fprintf(stderr, "Wrong number of arguments!\n");
        return 0;
    }
    incident_name=argv[1]; /* E.g. 4-He */
    target_name=argv[2]; /* E.g. Si */
    E=strtod(argv[3], &E_unit_str);
    if(strcmp(E_unit_str, "MeV")==0) {
        E *= MEV;
    }
    if(strcmp(E_unit_str, "keV")==0) {
        E *= KEV;
    }
    isotopes=load_isotope_table(XSTR(DATAPATH/masses.dat));
    if(!isotopes) {
        fprintf(stderr, "Could not load isotope table.\n");
        return 0;
    }
    incident=find_isotope_by_name(isotopes, incident_name);
    if(!incident) {
        fprintf(stderr, "No isotope %s found\n", incident_name);
        return 0;
    }
    Z2=find_Z_by_name(isotopes, target_name);
    if(!Z2) {
        fprintf(stderr, "No element %s found\n", target_name);
        return 0;
    }
    table=gsto_init(91, XSTR(STOPPING_DATA));
    gsto_auto_assign(table, incident->Z, Z2);
    gsto_load(table);
    get_single_stop(table, incident, E, Z2);
    gsto_deallocate(table);
    return 1;
}
