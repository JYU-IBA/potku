#define MASSES_LINE_LENGTH 80
#define MAX_ELEMENT_NAME 8 /* A-XX, i.e. 241-Am, max size = 3+1+3+1 = 8 */
#define MASSES_MAX_ISOTOPES 1900
#define SPEED_OF_LIGHT 299792458 /* m/s */
#define SPEED_OF_LIGHT_SQUARED 8.9875518e+16 /* m^2/s^2 */
#define AMU 1.66044e-27 /* kg */
#define KEV 1.6021917e-16 /* J */
#define MEV 1.6021917e-13 /* J */

#define STOPPING_DATA DATAPATH/stoppings.txt
#define MASSES_DATA DATAPATH/masses.dat
#define XSTR(x) STR(x)
#define STR(x) #x


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


double find_average_mass(isotopes_t *isotopes, int Z);
int find_Z_by_name(isotopes_t *isotopes, char *name); 
double find_mass(isotopes_t *isotope, int Z, int A); /* find isotope mass, but if A=0 calculate average mass of elem. */

isotopes_t *load_isotope_table(char *filename);
isotope_t *find_first_isotope(isotopes_t *isotopes, int Z);
isotope_t *find_most_abundant_isotope(isotopes_t *isotopes, int Z);
isotope_t *find_isotope(isotopes_t *isotopes, int Z, int A);
isotope_t *find_isotope_by_name(isotopes_t *isotopes, char *name);
stopping_t *init_stopping_table(char *filename);
int delete_stopping_table(stopping_t *stopping);


double velocity(double E, double mass); /* Use SI units */
double energy(double v, double mass); 