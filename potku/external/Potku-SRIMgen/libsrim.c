#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include "libsrim.h"

char* mystrsep(char** stringp, const char* delim)
{
  char* start = *stringp;
  char* p;

  p = (start != NULL) ? strpbrk(start, delim) : NULL;

  if (p == NULL)
  {
    *stringp = NULL;
  }
  else
  {
    *p = '\0';
    *stringp = p + 1;
  }

  return start;
}

int herpasprintf(char **ret, const char *format, ...)
{
    va_list ap;

    *ret = NULL;  /* Ensure value can be passed to free() */

    va_start(ap, format);
    int count = vsnprintf(NULL, 0, format, ap);
    va_end(ap);

    if (count >= 0)
    {
        char* buffer = malloc(count + 1);
        if (buffer == NULL)
            return -1;

        va_start(ap, format);
        count = vsnprintf(buffer, count + 1, format, ap);
        va_end(ap);

        if (count < 0)
        {
            free(buffer);
            return count;
        }
        *ret = buffer;
    }

    return count;
}

isotopes_t *load_isotope_table(char *filename) {
    char *line, *line_split;
    char *columns[6];
    char **col;
    int i=0;
    isotope_t *isotope;
    FILE *in_file=fopen(filename, "r");
    if(!in_file) 
        return NULL;
    line=malloc(sizeof(char)*LINE_LENGTH);
    if(!line) 
        return NULL;
    isotopes_t *isotopes=malloc(sizeof(isotopes_t));
    if(!isotopes)
        return NULL;
    isotopes->i = malloc(sizeof(isotope_t)*MAX_ISOTOPES);
    if(!isotopes->i)
        return NULL;
    while(fgets(line, LINE_LENGTH-1, in_file) != NULL) {
        line_split=line; /* strsep will screw up line_split, reset for every new line */
        if(i>=MAX_ISOTOPES) 
            break;
        for (col = columns; (*col = mystrsep(&line_split, " \t")) != NULL;)
            if (**col != '\0')
                if (++col >= &columns[6])
                    break;
        isotope=&isotopes->i[i];
        isotope->N=strtoimax(columns[0], NULL, 10);
        isotope->Z=strtoimax(columns[1], NULL, 10);
        isotope->A=strtoimax(columns[2], NULL, 10);
        herpasprintf(&isotope->name, "%i-%s", isotope->A, columns[3]);
        isotope->mass=strtod(columns[4], NULL)/1e6;
        isotope->abundance=strtod(columns[5], NULL)/1e2;
        isotopes->n_isotopes++;
        i++;
    }
    return isotopes;
}

isotope_t *find_first_isotope(isotopes_t *isotopes, int Z) {
    int i;
    isotope_t *isotope;
    for(i=0; i<isotopes->n_isotopes; i++) {
        isotope=&isotopes->i[i];
        if(isotope->Z == Z) { /* The right element */
            return isotope;
        }
    }
    return NULL; /* Nothing found */
}


isotope_t *find_most_abundant_isotope(isotopes_t *isotopes, int Z) {
fprintf(stderr, "Running SRModule, please wait.\n");
    int i;
    isotope_t *isotope;
    isotope_t *most_abundant_isotope=NULL;
    double abundance=0;
    for(i=0; i<isotopes->n_isotopes; i++) {
        isotope=&isotopes->i[i];
        if(isotope->Z == Z) { /* The right element */
            if(isotope->abundance > abundance) { /* Has higher abundance than anything found so far */
                abundance=isotope->abundance;
                most_abundant_isotope=isotope;
            }
        }
    }
    printf("herpa");
    return most_abundant_isotope;
}

isotope_t *find_isotope(isotopes_t *isotopes, int Z, int A) {
    isotope_t *isotope;
    int i;
    for(i=0; i<isotopes->n_isotopes; i++) {
        isotope=&isotopes->i[i];
        if(isotope->Z == Z && isotope->A == A) {
            return isotope;
        }
    }
    return NULL;
}

isotope_t *find_isotope_by_name(isotopes_t *isotopes, char *name) {
    isotope_t *isotope;
    int i;
    for(i=0; i<isotopes->n_isotopes; i++) {
        isotope=&isotopes->i[i];
        if(strcmp(isotope->name, name) == 0) {
            return isotope;
        }
    }
    return NULL;
}

double velocity(double E, double mass) { /* E in keV, mass in amu */
    double gamma=1+(E*KEV)/(mass*AMU*SPEED_OF_LIGHT_SQUARED);
    return sqrt((1-pow(gamma,-2.0))*SPEED_OF_LIGHT_SQUARED);
}

double energy_from_velocity(double v, double mass) { /* v in m/s, mass in amu */
    return (mass*AMU*SPEED_OF_LIGHT_SQUARED*(pow(1-pow(v/SPEED_OF_LIGHT,2.0),-0.5)-1))/KEV;
}


stopping_t *init_stopping_table(char *filename) {
    int i,j, z_max, vsteps;
    FILE *stop_file = fopen(filename, "r");
    if(!stop_file)
        return NULL;
    stopping_t *stopping = malloc(sizeof(stopping_t));
    fread(&z_max, sizeof(int), 1, stop_file);
    stopping->z_max=z_max;
    fread(&vsteps, sizeof(int), 1, stop_file); /* e.g. 100 steps stored in file */
    vsteps++; /* v[0] not stored in the file, increase number of steps by one */
    stopping->vsteps=vsteps; /* e.g. 101 steps stored in memory */
    stopping->v=malloc(sizeof(double)*vsteps); /* allocate space for e.g. 101 steps, v[0...100] */
    stopping->v[0]=0.0;
    for(i=1; i<vsteps; i++) {
        fread(stopping->v+i, sizeof(double), 1, stop_file);
    } 
    stopping->v_max=stopping->v[i-1]; /* e.g. v_max=v[100] */
    stopping->sto=malloc(sizeof(double **)*z_max);
    
    double *S = malloc(sizeof(double)*vsteps);
    for(i=0; i<z_max; i++) {
        stopping->sto[i] = malloc(sizeof(double *)*z_max);
        for(j=0; j<z_max; j++) {
            S[0]=0.0;
            fread(S+1, sizeof(double), vsteps-1, stop_file); /* vsteps-1 e.g. 100 steps, amount stored in memory */
            stopping->sto[i][j] = S;
            S=malloc(sizeof(double)*vsteps);
        }
    }
    fclose(stop_file);
    return stopping;
}

int delete_stopping_table(stopping_t *stopping) {
    int i,j;
    int z_max=stopping->z_max;
    for(i=0; i<z_max; i++) {
        for(j=0; j<z_max; j++) {
            if(stopping->sto[i][j])
                free(stopping->sto[i][j]);
        }
        free(stopping->sto[i]);
    } 
    free(stopping);
    return 1;
}

double srim_stop_isotope(stopping_t *stopping, isotope_t *incident, int Z2, double E) {
    return srim_stop(stopping, incident->Z, Z2, velocity(E, incident->mass));
}


double srim_stop_E(stopping_t *stopping, int Z1, int Z2, double mass, double E) {
    return srim_stop(stopping, Z1, Z2, velocity(E, mass));
}

double **srim_table_E(stopping_t *stopping, int Z1, int Z2, double mass, double E_max, double E_step, int *nsteps) {
    (*nsteps) = (E_max/E_step)+1+1; /* +1 for inclusion of zero energy (i.e. 10 MeV/100 keV = 100, we want E=0, 100 keV, 200 keV, ..., 10 MeV, the other just for safety (rounding) */
    int i;
    double E;
    double **out_table=malloc(sizeof(double *)*2); /* two column data */
    double *out_energies=malloc(sizeof(double)*(*nsteps));
    double *out_stopping=malloc(sizeof(double)*(*nsteps));;
    out_table[0] = out_energies;
    out_table[1] = out_stopping;
    out_table[0][0] = 0.0; /* First energy is zero */
    out_table[0][1] = 0.0; /* First stopping for zero energy is zero, doesn't really make sense but we're ok with it */
    for(i=1; i< (*nsteps); i++) {
        E=E_step*i;
        out_table[0][i] = E;
        out_table[1][i] = srim_stop_E(stopping, Z1, Z2, mass, E);
    }
    return out_table;
}

double srim_stop(stopping_t *stopping, int Z1, int Z2, double v) { /* velocity in m/s */
    int i;
    if(Z1 >= stopping->z_max || Z2 >= stopping->z_max) {
        return 0.0;
    }
    if (v>=stopping->v_max) { /* Velocity too high */
        return 0.0;
    }
    for(i=0; i<=stopping->vsteps; i++) {
        if(stopping->v[i] >= v)
            break; /* Found the index at which velocities[i] is just above the velocity we are interested in */ 
    }
    int i_v_lo=i-1;
    int i_v_hi=i;
    if(i==stopping->vsteps+1) {
#ifdef DEBUG
        fprintf(stderr, "You're asking for stopping at too high energy!\n"); /* This shouldn't happen */
#endif
        return 0.0;
    } /* There is not enough stopping data, the particle velocity is higher, abort.*/
    if(i_v_lo==0) return 0.0;
    
    /* Now at this point we (should) have velocities[i_v_lo] < v <= velocities[i_v_hi] */  
    
    double S_v_lo=stopping->sto[Z1][Z2][i_v_lo];
    double S_v_hi=stopping->sto[Z1][Z2][i_v_hi];
    double dS=S_v_hi-S_v_lo;
    
    double v_lo=stopping->v[i_v_lo];
    double v_hi=stopping->v[i_v_hi];
    double dv=v_hi-v_lo;
    
    /* dS and dv give the local derivatives of the stopping power curve */
    
    double S=S_v_lo+(dS/dv)*(v-v_lo); /* Linear interpolation */
    
    return S;
}
