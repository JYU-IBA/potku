#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <inttypes.h>
#include <math.h>

#define MAX_ISOTOPES 1900
#define MASSES_FILE DATAPATH/masses.dat

#define LINE_LENGTH 80
#define SPEED_OF_LIGHT 299792458 /* m/s */
#define SPEED_OF_LIGHT_SQUARED 8.9875518e+16 /* m^2/s^2 */
#define AMU 1.66044e-27 /* kg */
#define KEV 1.6021917e-16 /* J */
typedef struct {
    char *name; /* "A-Xx eg. 239-Pu" */
    int N;
    int Z;
    int A; /* A=Z+N */
    double mass;
    double abundance;
} isotope_t;

typedef struct {
    int n_isotopes;
    isotope_t *i;
} isotopes_t;

typedef struct {
    double v_max;
    int vsteps;
    int z_max;
    double ***sto; /* sto[Z1][Z2][v_index] */
    double *v; /* v=v[v_index] */
} stopping_t;

isotopes_t *load_isotope_table(char *filename);
isotope_t *find_first_isotope(isotopes_t *isotopes, int Z);
isotope_t *find_most_abundant_isotope(isotopes_t *isotopes, int Z);
isotope_t *find_isotope(isotopes_t *isotopes, int Z, int A);
isotope_t *find_isotope_by_name(isotopes_t *isotopes, char *name);
stopping_t *init_stopping_table(char *filename);
int delete_stopping_table(stopping_t *stopping);
double velocity(double E, double mass);
double energy_from_velocity(double v, double mass);

char* mystrsep(char** stringp, const char* delim); /* Custom strsep for Windows */
int herpasprintf(char **ret, const char *format, ...); /* Custom asprintf for Windows */
double srim_stop(stopping_t *stopping, int Z1, int Z2, double velocity); /* velocity in m/s */
double srim_stop_E(stopping_t *stopping, int Z1, int Z2, double mass, double E); /* energy in keV */
double srim_stop_isotope(stopping_t *stopping, isotope_t *incident, int Z2, double E); /* energy in keV*/

double **srim_table_E(stopping_t *stopping, int Z1, int Z2, double mass, double E_max, double E_step, int *nsteps);
