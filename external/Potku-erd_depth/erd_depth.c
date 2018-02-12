#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include <gsto_masses.h>
#include <libgsto.h>
#include "units.h"

#define NLINE 200
#define NAMELEN 1000 /* This is the maximum length for a filename. FIXME: Dynamic length! */
#define NELESYM 10
#define MAXELEMENTS 100 /* Default for general->maxelements */
#define MAXNUCMASSES 300 /* Default for general->maxnucmasses */
#define ERD 1
#define RBS 2
#define MAXEVENTS 10000000
#define MAXVSTEP 201
#define MAXDSTEP 201 /* Default for general->maxdstep */
#define MAXSTOCHANGE 0.05


#define TRUE  1
#define FALSE 0

#define TYPELEN 3

#define I_BEAM     0
#define I_ENERGY   1
#define I_DETANGLE 2
#define I_TARANGLE 3
#define I_DETDIST  4
#define I_STOSTEP  5
#define I_OUTSTEP  6
#define I_DENSITY  7
#define I_SCALE    8
#define I_CROSS_SECTION 9
#define I_MAXDSTEP 10
#define I_NITER 11

#define F_MASSES DATAPATH/masses.dat
#define NITER 4

#define NABOVE 10    /* Output steps above the surface */
#define WSCALE 4.0   /* change of the total conc (sigma) to stop scaling */

#define max(A,B)  (((A) > (B)) ? (A) : (B))
#define min(A,B)  (((A) < (B)) ? (A) : (B))

#define XSTR(x) STR(x)
#define STR(x) #x

static const char *inlines[] = {
   "Beam:",
   "Energy:",
   "Detector angle:",
   "Target angle:",
   "Detector distance:",
   "Depth step for stopping:",
   "Depth step for output:",
   "Target density:",
   "Depths for concentration scaling:",
   "Cross section:",
   "Number of depth steps:",
   "Number of iterations:"
};

enum cross_section {
    CS_NONE = 0,
    CS_RUTHERFORD = 1,
    CS_LECUYER = 2,
    CS_ANDERSEN = 3
};

typedef struct {
   double theta;
   double fii;
   double E;
   double v;
   int type;
   int n;
   int Z;
   int A;
   double M;
   double w0;
   double w;   
   double d;
} Event;

typedef struct {
   int Z;
   int A;
   double M;
   double E;
   double detector_angle;
   double target_angle;
   double det_dist;
} Measurement;

typedef struct {
   char eventfile[NAMELEN];
   char setupfile[NAMELEN];
   int nevents;
   double vmax;
   int *element; /* element[0..maxelements] */
   int **nuclide; /* nuclide[0..maxelements][0..maxnucmasses] */
   char prefix[NAMELEN]; 
   double *M; /* M[0..maxelements] */
   double outstep;
   double minscale,maxscale;
   int scale;
   enum cross_section cs;
   int maxdstep;
   int maxelements;
   int maxnucmasses;
   int niter;
} General;

typedef struct {
   double vstep;
   int vsteps;
   double dstep;
   double vdiv;
   double ddiv;
   double ***ele; /* ele[0..maxelements][0..maxelements] */
   double ***sum; /* sum[0..maxelements] */
} Stopping;

typedef struct {
   double dstep;
   double dmax;
   double **w; /* w[0..maxelements][0..maxdstep] */
   int **n; /* n[0..maxelements][0..maxdstep] */
   double *wsum; /* wsum[0..maxdstep] */
   double *mass; /* wsum[0..maxdstep] */
   int *nsum; /* wsum[0..maxdstep] */
   double *Ebeam;
   double density;
   double ***wprofile; /* wprofile[0..maxelements][0..maxnucmasses] */
   int ***nprofile; /* nprofile[0..maxelements][0..maxnucmasses] */
   double *wprofsum;
   double *profmass;   
   int *nprofsum;
} Concentration;

void read_command_line(int,char **,General *);
void read_setup(General *,Measurement *,Concentration *);
void read_events(General *,Measurement *,Event *,Concentration *);
char *read_inputline(char *,int);
void file_error(char *,int);
int get_nuclide(char *,int *,int *,double *);
double ipow(double,int);
double ipow2(double);
void calculate_stoppings(General *, Measurement *, Stopping *);
void create_sumsto(void);
void create_conc_profile(General *,Measurement *,Stopping *,
                         Concentration *);
void calculate_primary_energy(General *,Measurement *,Stopping *,
                              Concentration *);
double get_eloss(General *, int,double,double,double,double,Stopping *);
double inter_sto(General *,int,double,double,Stopping *);
void calculate_recoil_depths(General *,Measurement *,Event *,
                             Stopping *,Concentration *);
void output(General *,Concentration *,Event *);
void clear_conc(General *, Concentration *);
char *get_symbol(int);
double Lecuyer(int, int, double);
double Andersen(int, int, double, double);
double Serd(int,double,int,double,double,double, enum cross_section);
double Srbs(int,double,int,double,double,double, enum cross_section);
double Srbs_mc(double,double,double,double);
double mc2lab_scatc(double,double,double);
int allocate_general_sto_conc(General *, Measurement *, Stopping *, Concentration *);

int main(int argc,char *argv[])
{
   General general;
   Stopping sto;
   Concentration conc;
   Event *event;
   Measurement meas;
   int i;
   event=(Event *) malloc(MAXEVENTS*sizeof(Event));
   read_command_line(argc,argv,&general);
   read_setup(&general,&meas,&conc);
   allocate_general_sto_conc(&general, &meas, &sto, &conc);
   switch(general.cs) {
        default:
        case CS_RUTHERFORD:
            fprintf(stderr, "erd_depth is using Rutherford cross sections\n");
            break;
        case CS_LECUYER:
            fprintf(stderr, "erd_depth is using L'Ecuyer corrected Rutherford cross sections\n");
            break;
        case CS_ANDERSEN:
            fprintf(stderr, "erd_depth is using Andersen corrected Rutherford cross sections\n");
            break;
   }
   clear_conc(&general, &conc);
   read_events(&general,&meas,event,&conc);
   calculate_stoppings(&general, &meas, &sto);
   create_conc_profile(&general,&meas,&sto,&conc);
   for(i=0;i<general.niter;i++){
      calculate_primary_energy(&general,&meas,&sto,&conc);
      clear_conc(&general, &conc);
      calculate_recoil_depths(&general,&meas,event,&sto,&conc);
      create_conc_profile(&general,&meas,&sto,&conc);
   }

   output(&general,&conc,event);

   exit(0);
}

int allocate_general_sto_conc(General *general, Measurement *meas, Stopping *sto, Concentration *conc) {
    int i;
    fprintf(stderr, "Allocating stuff. %i %i %i\n", general->maxelements, general->maxnucmasses, general->maxdstep);
    general->element = (int *) calloc(general->maxelements, sizeof(int));
    general->element[meas->Z] ++;
    general->nuclide = (int **) calloc(general->maxelements, sizeof(int *));
    general->M = (double *) calloc(general->maxelements, sizeof(double));
    sto->ele = (double ***) calloc(general->maxelements, sizeof(double **));
    sto->sum = (double ***) calloc(general->maxelements, sizeof(double **));
    conc->w = (double **) calloc(general->maxelements, sizeof(double *));
    conc->n = (int **) calloc(general->maxelements,  sizeof(int *));
    conc->wsum = (double *) calloc(general->maxdstep, sizeof(double));
    conc->mass = (double *) calloc(general->maxdstep, sizeof(double));
    conc->nsum = (int *) calloc(general->maxdstep, sizeof(int));
    conc->Ebeam = (double *) calloc(general->maxdstep, sizeof(double));
    conc->wprofile = (double ***) calloc(general->maxelements*general->maxnucmasses, sizeof(double **));
    conc->nprofile = (int ***) calloc(general->maxelements, sizeof(int **));
    for(i=0; i<general->maxelements; i++) {
        general->nuclide[i]=(int *)calloc(general->maxnucmasses, sizeof(int));
        sto->ele[i] = (double **)calloc(general->maxelements, sizeof(double *));
        conc->w[i] = (double *) calloc(general->maxdstep, sizeof(double));
        conc->n[i] = (int *) calloc(general->maxdstep, sizeof(int));
        conc->wprofile[i] = (double **) calloc(general->maxnucmasses, sizeof(double *)); 
        conc->nprofile[i] = (int **) calloc(general->maxnucmasses, sizeof(int *));
    }
    if(general->element && general->nuclide && general->M && sto->ele && sto->sum) {
        return 0;
    } else {
        fprintf(stderr, "Could not allocate general tables etc.\n");
        exit(9);
    }
}

void output(General *general,Concentration *conc,Event *event)
{
   FILE *fp;
   char fname[NAMELEN],fnuc[NAMELEN];
   double max_change,nominal,wsum=0.0,dep,dep0,mdep,mdep0,d,r,relerr;
   int iz2,ia2,ie,z,a,ip,id,nprofile,minp,maxp;

   r = general->outstep/conc->dstep;

   nprofile = (general->maxdstep*conc->dstep)/general->outstep + NABOVE;

   for(iz2=1;iz2<general->maxelements;iz2++){
      if(general->element[iz2] > 0){
         for(ia2=1;ia2<general->maxnucmasses;ia2++){
            if(general->nuclide[iz2][ia2]){
               conc->wprofile[iz2][ia2] = (double *) malloc(sizeof(double)*nprofile);
               conc->nprofile[iz2][ia2] = (int *) malloc(sizeof(int)*nprofile);
               for(ip=0;ip<nprofile;ip++){
                  conc->wprofile[iz2][ia2][ip] = 0.0;
                  conc->nprofile[iz2][ia2][ip] = 0;
	       }
            }
         }
      } else /* element exists */
	for(ia2=1;ia2<general->maxnucmasses;ia2++){
	   conc->wprofile[iz2][ia2] = NULL;
	   conc->nprofile[iz2][ia2] = NULL;
	}
   }

   conc->wprofsum = (double *) malloc(sizeof(double)*nprofile);
   conc->profmass = (double *) malloc(sizeof(double)*nprofile);   
   conc->nprofsum = (int *) malloc(sizeof(double)*nprofile);
   for(ip=0;ip<nprofile;ip++){
      conc->wprofsum[ip] = 0.0;
      conc->profmass[ip] = 0.0;      
      conc->nprofsum[ip] = 0;
   }
   
   for(ie=0;ie<general->nevents;ie++){
      z = event[ie].Z;
      a = event[ie].A;
#ifdef DEBUG
      printf("A %8i %10.3e %14.5e\n",z,event[ie].d/(1.0e15/C_CM2),event[ie].w);
#endif
      ip = (int) (event[ie].d/general->outstep + NABOVE);
      ip = max(0,ip);
      ip = min(nprofile-1,ip);
#ifdef DEBUG
      printf("%8i %10.2f %14.5f %8i\n",ip,event[ie].d/(1.0e15/C_CM2),
              event[ie].w,event[ie].n);
#endif
      conc->wprofile[z][a][ip] += event[ie].w;
      conc->nprofile[z][a][ip] ++;
      conc->wprofsum[ip] += event[ie].w;
      conc->profmass[ip] += event[ie].M*event[ie].w;
      conc->nprofsum[ip] ++;    
   }

   for(ip=0;ip<nprofile;ip++){
      if(conc->wprofsum[ip] > 0.0)
         conc->profmass[ip] *= (general->outstep/conc->wprofsum[ip]);
      else
         conc->profmass[ip] = 0.0;
   }

   if(general->scale){
      minp = (int) (general->minscale/general->outstep + NABOVE);
      minp = max(0,min(minp,nprofile-1));
      maxp = (int) (general->maxscale/general->outstep + NABOVE);
      maxp = max(0,min(maxp,nprofile-1));
      for(ip=minp;ip<maxp;ip++)
         wsum += conc->wprofsum[ip];
      if(wsum <= 0.0 || minp >= maxp)
         wsum = 1.0;
       else
         wsum /= (maxp-minp);
   } else {
      ip = NABOVE + 2;
      nominal = conc->wprofsum[ip];
      max_change = WSCALE*nominal/sqrt(conc->nprofsum[ip]);

      while(ip < nprofile && fabs(conc->wprofsum[ip] - nominal) < max_change){
         wsum += conc->wprofsum[ip];
         ip++;
      }
      wsum /= (ip - 2 - NABOVE);
   }
   
   for(iz2=1;iz2<general->maxelements;iz2++){
      if(general->element[iz2] > 0){
         for(ia2=1;ia2<general->maxnucmasses;ia2++){
            if(general->nuclide[iz2][ia2] > 0){
               dep = mdep = dep0 = mdep0 = 0.0;
               strcpy(fname,general->prefix);
               strcat(fname,".");
               if(general->nuclide[iz2][0] > 1){ /* more than one isotope */
                  sprintf(fnuc,"%i",ia2);
                  strcat(fname,fnuc);
               }
               strcat(fname,get_symbol(iz2));
               fp = fopen(fname,"w");
               if(fp == NULL){
                  fprintf(stderr,"Could not open file %s\n for writing",fname);
                  exit(6);
               }
               for(ip=0;ip<NABOVE;ip++){
                  mdep0 += conc->profmass[ip];
                  dep0 += conc->profmass[ip]/conc->density;
               }
               for(ip=0;ip<nprofile;ip++){
                  d = (ip - NABOVE)*general->outstep;
                  d += 0.5*general->outstep;
		  if(conc->nprofile[iz2][ia2][ip] > 0)
		    relerr = 1.0/sqrt((double ) (conc->nprofile[iz2][ia2][ip]));
		  else
		    relerr = 1;
                  fprintf(fp,"%10.3f %10.3f %10.3f ",d/(1.0e15/C_CM2),
                                                     (mdep-mdep0)/(C_UG/C_CM2),
                                                     (dep-dep0)/C_NM);
/*
                  fprintf(fp,"%10.3f ",(dep-dep0)/C_NM);
*/
                  fprintf(fp,"  %10.5f",conc->wprofile[iz2][ia2][ip]/wsum);
                  fprintf(fp,"  %14.5e",conc->wprofile[iz2][ia2][ip]);
                  fprintf(fp,"  %10.5f",relerr*conc->wprofile[iz2][ia2][ip]/wsum);
                  fprintf(fp,"  %10i",conc->nprofile[iz2][ia2][ip]);
		  fprintf(fp,"\n");
                  mdep += conc->profmass[ip]; 
                  dep += conc->profmass[ip]/conc->density;
               }
               fclose(fp);               
            } /* nuclide exists */
         } /* loop through nuclides */
      } /* element exists */
   } /* loop though elements */
   
   strcpy(fname,general->prefix);
   strcat(fname,".");
   strcat(fname,"total");
   fp = fopen(fname,"w");
   if(fp == NULL){
      fprintf(stderr,"Could not open file %s\n for writing",fname);
      exit(6);
   }      
   dep = mdep = dep0 = mdep0 = 0.0;
   for(ip=0;ip<NABOVE;ip++){
      mdep0 += conc->profmass[ip]; 
      dep0 += conc->profmass[ip]/conc->density;
   }
   for(ip=0;ip<nprofile;ip++){
      d = (ip - NABOVE)*general->outstep;
      id = max(0,(int) (d/conc->dstep));
      d += 0.5*general->outstep;
      fprintf(fp,"%7.2f %10.3f %10.3f ",d/(1.0e15/C_CM2),
                                        (mdep-mdep0)/(C_UG/C_CM2),
                                        (dep-dep0)/C_NM);
      fprintf(fp,"%10.4e\n",conc->wprofsum[ip]/wsum);
      mdep += conc->profmass[ip]; 
      dep += conc->profmass[ip]/conc->density;

   }
   fclose(fp);

}
char *get_symbol(int z)
{
   FILE *fp;
   char *sym;
   int cont=TRUE,Z,c;

   sym = (char *) malloc(sizeof(char)*NELESYM);
   
   fp = fopen(XSTR(F_MASSES),"r");

   if(fp == NULL){
      fprintf(stderr,"Could not open mass file %s\n",XSTR(F_MASSES));
      exit(4);
   }

   while(cont){
      c = fscanf(fp,"%*i %i %*i %s %*f %*f\n",&Z,sym);
      if(c == 2){
         if(z == Z){
            fclose(fp);
            return(sym);
         }
      } else {
         cont = FALSE;
         fprintf(stderr,"Could not find elemental symbol for Z=%i\n",z);
         exit(7);
      }
   }
   return(sym);
      
}
void calculate_recoil_depths(General *general,Measurement *meas,Event *event,
                             Stopping *sto,Concentration *conc)
{
   double K,dmult,recE,beamE,d,dstep,M,dE=0,w,bk,rk;
   int Z,id,ie;

   for(ie=0;ie<general->nevents;ie++){
      Z = event[ie].Z;
      M = event[ie].M;
      
      dmult = 1.0/sin(event[ie].theta - meas->target_angle);

      if(event[ie].type == ERD)
         K = (4.0*meas->M*event[ie].M*ipow2(cos(event[ie].theta)))/
             ipow2(meas->M + event[ie].M);
      else {   /* RBS */
         K = sqrt(ipow2(event[ie].M) - ipow2(meas->M*sin(event[ie].theta)));
         K += meas->M*cos(event[ie].theta);
         K /= (meas->M + event[ie].M);
         K = ipow2(K);
      }
   
      d = 0.0;
      id = 0;
      dstep = conc->dstep;
      
      recE = event[ie].E;
      beamE = conc->Ebeam[0]*K;
      
      if(recE >= beamE){
         dE = get_eloss(general, Z,M,recE,d,dstep*dmult,sto);         
         rk = dE/dstep;
         bk = (conc->Ebeam[id+1]*K - conc->Ebeam[id]*K)/dstep;
         event[ie].d = 0.5*(d - dstep) + (conc->Ebeam[id]*K - (recE - dE))/(rk - bk);
         beamE = conc->Ebeam[0];
#ifdef DEBUG
         printf("A %8i %10.3f\n",Z,event[ie].d/(1.0e15/C_CM2));
#endif
      } else {
         while((id < general->maxdstep) && (recE < beamE)){
            if(event[ie].type == ERD)
               dE = get_eloss(general, Z,M,recE,d,dstep*dmult,sto);
            else
               dE = get_eloss(general, meas->Z,meas->M,recE,d,dstep*dmult,sto);
            recE += dE;
            id++;
            d += dstep;
            beamE = conc->Ebeam[id]*K;
         }
         if(id < general->maxdstep){
            bk = (beamE - conc->Ebeam[id-1]*K)/dstep;
            rk = dE/dstep;
            event[ie].d = (d - dstep) + (conc->Ebeam[id-1]*K - (recE - dE))/(rk - bk);
            recE = (recE - dE) + rk*(event[ie].d - (d - dstep));
         }
         beamE = conc->Ebeam[id] + (event[ie].d - id*dstep)*
                 (conc->Ebeam[id] - conc->Ebeam[id-1])/dstep;
#ifdef DEBUG
         printf("B %8i %10.3f\n",Z,event[ie].d/(1.0e15/C_CM2));
#endif
      }

      if(id <  general->maxdstep){
         if(event[ie].type == ERD){
            w = Serd(meas->Z,meas->M,event[ie].Z,event[ie].M,event[ie].theta,beamE, general->cs);
         } else {
            w = Srbs(meas->Z,meas->M,event[ie].Z,event[ie].M,event[ie].theta,beamE, general->cs);
         }
         event[ie].w = event[ie].w0/w;
#ifdef DEBUG
         printf("W %i %10.4f %10.4f\n",event[ie].type,w/C_BARN,beamE/C_MEV);
         printf("%3i %14.5e %14.5e\n",Z,(event[ie].d*C_CM2)/1.0e15,event[ie].w);
#endif                                      
         if(event[ie].d < 0.0)
            id = 0.0;
         else
            id = (int) (event[ie].d/conc->dstep);
         conc->w[Z][id] += event[ie].w;
         conc->n[Z][id] ++;
         conc->wsum[id] += event[ie].w;
         conc->nsum[id] ++;
      } else {
         event[ie].w = 0.0;
      }
      
   }
}

double Lecuyer(int z1, int z2, double E) { /* E in CM coordinates */
    return (1-48.73*C_EV*z1*pow(z2,4.0/3.0)/E);
}
double Andersen(int z1, int z2, double E, double theta) { /* E in CM coordinates, theta is scattering angle (of scattered particle) in CM also */
    double r_VE=48.73*C_EV*z1*z2*sqrt(pow(z1,2.0/3)+pow(z2,2.0/3))/E;
    double F=ipow2(1+0.5*r_VE)/ipow2(1+r_VE+ipow2(0.5*r_VE/(sin(theta/2.0))));
    return F;
}

double Serd(int z1,double m1,int z2,double m2,double t,double E, enum cross_section cs) /* t is recoil angle in lab, E lab energy of incident particle */
{
    double E_cm = m2*E/(m1+m2);
    double t_sc=PI-2*t;
    double sigma_r = ipow2(z1*z2*P_E*P_E/(8*PI*P_EPS0*E))*ipow2(1.0 + m1/m2)/ipow(cos(t),3);
    double F;
    switch(cs) {
        case CS_RUTHERFORD:
        default:
            F=1.0;
            break;
        case CS_ANDERSEN:
            F=Andersen(z1, z2, E_cm, t_sc);
            break;
        case CS_LECUYER:
            F=Lecuyer(z1, z2, E_cm);
            break;
    }
    return(F*sigma_r);
 }

double Srbs(int z1,double m1,int z2,double m2,double t,double E, enum cross_section cs)
{
    double sigma_r,tcm,Ecm,r,F;
    Ecm = m2*E/(m1 + m2);
    r = m1/m2;
 
    tcm = t + asin(r*sin(t));;
 
    sigma_r = mc2lab_scatc(Srbs_mc(z1,z2,tcm,Ecm),tcm,t);
    switch(cs) {
        case CS_RUTHERFORD:
        default:
            F=1.0;
            break;
        case CS_ANDERSEN:
            F=Andersen(z1, z2, Ecm, tcm);
            break;
        case CS_LECUYER:
            F=Lecuyer(z1, z2, Ecm);
            break;
    }
    return(F*sigma_r);
}

double Srbs_mc(double z1,double z2,double t,double E)
{
   double value;
   value = ipow2((z1*z2*P_E*P_E)/(4.0*PI*P_EPS0))*ipow2(1.0/(4.0*E))*
           ipow(1.0/sin(t/2.0),4);
   return(value);
}
double mc2lab_scatc(double mcs,double tcm,double t)
{
   double value;

   value = (mcs*ipow2(sin(tcm)))/(ipow2(sin(t))*cos(tcm - t));

   return(value);
}

void calculate_primary_energy(General *general,Measurement *meas,Stopping *sto,
                              Concentration *conc)
{
   double E,Emin,dmult,d,dstep;
   int id=0;
   
   E = meas->E;

   d = 0.0;
   
   Emin = 0.1*meas->E;
   dmult = 1.0/sin(meas->target_angle);

   dstep = conc->dstep;
 
   while(id < general->maxdstep){
#ifdef DEBUG
      printf("P %14.5e %14.5e\n",(d*C_CM2)/1.0e15,E/C_MEV);
#endif
      conc->Ebeam[id] = E;
      E -= get_eloss(general, meas->Z,meas->M,E,d,dstep*dmult,sto);
      d += dstep;
      id++;
   }
#ifdef DEBUG
   printf("%14.5e %14.5e\n",(d*C_CM2)/1.0e15,E/C_MEV);   
#endif
}
double get_eloss(General *general, int z,double m,double E,double d,double deltad,Stopping *sto)
{
   double dstep,dE,s1=0,s2=0,v,v2,r,dmin,dmax;

   dE = 0.0;
   dstep = deltad;

   if(E <= 0.0)
      return(0.0);

   v = sqrt((2.0*E)/m);

   dmin = d;
   dmax = (d + deltad)*1.000001;

   while((dmax - d) >= dstep){
      do {
         s1 = inter_sto(general, z,v,d,sto);
         if(E < s1*dstep)
            return(0.0);
         v2 = sqrt((2.0*(E - s1*dstep))/m);
         s2 = inter_sto(general, z,v2,d+dstep,sto);
   
         r = fabs(s2 - s1)/s1;
   
         if(r > MAXSTOCHANGE){
            dstep /= 2.0;
         }
      } while(r > MAXSTOCHANGE);
      dE += 0.5*(s1 + s2)*dstep;
      d += dstep;
   }

   dE += (dmax - d)*0.5*(s1 + s2);

   return(dE);

}
double inter_sto(General *general, int z1,double v,double d,Stopping *sto)
{
   double **S;
   double value,s1,s2,vdiv,ddiv;
   int iv,id;
   
   S = sto->sum[z1];

   vdiv = sto->vdiv;
   ddiv = sto->ddiv;

   iv = (int) (v*vdiv);
   iv = min(max(0.0,iv),sto->vsteps-2);

   id = (int) (d*ddiv);
   id = min(max(0.0,id),general->maxdstep-2);

   s1 = S[iv][id] + (v*vdiv - iv)*(S[iv+1][id] - S[iv][id]);
   s2 = S[iv][id+1] + (v*vdiv - iv)*(S[iv+1][id+1] - S[iv][id+1]);   
   
   value = s1 + (d*ddiv - id)*(s2 - s1);
   
   return(value);
  
}
void create_conc_profile(General *general,Measurement *meas,
                         Stopping *sto,Concentration *conc)
{
   double d=0.0,**p;
   int iz1,iz2,id,iv,minn,n,nsum;

   sto->dstep = conc->dstep;
   sto->ddiv = 1.0/conc->dstep;   
   for(id=0;id<general->maxdstep;id++){
      for(iz2=1;iz2<general->maxelements;iz2++){
         if(conc->wsum[id] > 0.0)
            conc->w[iz2][id] /= conc->wsum[id];
      }
      d += conc->dstep;
   }    

   n = 0;
   nsum = 0;
   for(id=0;id<general->maxdstep;id++){
      if(conc->nsum[id] > 0){
         n++;
         nsum += conc->nsum[id];        
      }      
   }

   minn = max(1,nsum/(20*n));

   id = 0;
   while(conc->nsum[id] <= minn)
      id++;
   n = id;

   for(id=0;id<n;id++)
      for(iz2=1;iz2<general->maxelements;iz2++)
         conc->w[iz2][id] = conc->w[iz2][n];

   for(id=1;id<general->maxdstep;id++){
      if(conc->nsum[id] <= minn){
         for(iz2=1;iz2<general->maxelements;iz2++)
            conc->w[iz2][id] = conc->w[iz2][id-1];
      }
   }

   for(iz1=1;iz1<general->maxelements;iz1++){
      if(general->element[iz1] > 0){
         if(sto->sum[iz1] == NULL){
               p = (double **) malloc(sizeof(double *)*sto->vsteps);
               for(iv=0;iv<sto->vsteps;iv++)
                  p[iv] = malloc(sizeof(double)*general->maxdstep);
               sto->sum[iz1] = p;         
         }
         for(id=0;id<general->maxdstep;id++)
            for(iv=0;iv<sto->vsteps;iv++)
               sto->sum[iz1][iv][id] = 0.0;         
      } 
   }
   
   for(iz1=1;iz1<general->maxelements;iz1++){
      if(general->element[iz1] > 0){
         for(iz2=1;iz2<general->maxelements;iz2++)
            if(general->element[iz2] > 0){
               for(id=0;id<general->maxdstep;id++)
                  for(iv=0;iv<sto->vsteps;iv++)
                     sto->sum[iz1][iv][id] += 
                          conc->w[iz2][id]*sto->ele[iz1][iz2][iv];
            }
               
      }   
   }

#ifdef DEBUG
   for(iv=0;iv<sto->vsteps;iv++){
      printf("%3i %10.4f %14.5e\n",iv,conc->w[14][0],sto->sum[53][iv][0]);
   }
#endif

   printf("\n");

   for(id=0;id<general->maxdstep/10;id++){
      printf("%6.1f ",(id*conc->dstep)/(1.0e15/C_CM2));
      for(iz2=1;iz2<general->maxelements;iz2++){
         if(general->element[iz2] > 0){
            printf("%2i %4.1f ",iz2,conc->w[iz2][id]*100.0);
         }      
      }
      printf("\n");
   }

}
void clear_conc(General *general, Concentration *conc)
{
   int iz2,id;

   for(iz2=0;iz2<general->maxelements;iz2++){
      for(id=0;id<general->maxdstep;id++){
         conc->w[iz2][id] = 0.0;
         conc->n[iz2][id] = 0;
      }
   }
   for(id=0;id<general->maxdstep;id++){
      conc->wsum[id] = 0.0;
      conc->nsum[id] = 0;
   }

}

void calculate_stoppings(General *general, Measurement *meas, Stopping *sto) {
    int z1, z2;
    int s;
    gsto_table_t *table;
    for(z1=1;z1<general->maxelements;z1++){
        sto->sum[z1] = NULL;
        for(z2=1;z2<general->maxelements;z2++){      
            sto->ele[z1][z2] = NULL;
        }
    }
    table=gsto_init(general->maxelements, XSTR(STOPPING_DATA));
    if(!table) {
        fprintf(stderr, "Could not init stopping table.\n");
        return;
    }
    sto->vsteps=1001; /* FIXME: Dynamically set parameter. Verify v_max and v_steps and everything... */
    for(z1=0;z1<general->maxelements;z1++){
             for(z2=0;z2<general->maxelements;z2++){
                if(general->element[z1] > 0 && general->element[z2]>0) {
                    gsto_auto_assign(table, z1, z2);
                }
             }
    }
    if(!gsto_load(table)) {
        fprintf(stderr, "Error in loading stopping.\n");
        return;
    }
    gsto_print_assignments(table);
    
    general->vmax *= 1.2;
    sto->vstep = general->vmax/(sto->vsteps - 1.0);
    sto->vdiv = 1.0/sto->vstep;
    
    for(z1=0;z1<general->maxelements;z1++){
        for(z2=0;z2<general->maxelements;z2++){
            if(general->element[z1] > 0 && general->element[z2]>0) {
                sto->ele[z1][z2]=gsto_sto_v_table(table, z1, z2, 0, general->vmax, sto->vsteps); /* 0 as a v_min, does it give any trouble? */
                for(s=0; s<sto->vsteps; s++) {
                    sto->ele[z1][z2][s] *= C_EVCM2_1E15ATOMS; /* Units conversion */
                }
            }
        }
    }
    gsto_deallocate(table);
}

void read_command_line(int argc,char *argv[],General *general)
{

   if(argc > 1)
      strcpy(general->prefix,argv[1]);
   else
      strcpy(general->prefix,"depth");

   if(argc > 2)
      strcpy(general->setupfile,argv[2]);
   else
      strcpy(general->setupfile,"erd_depth.in");

   if(argc > 3)
      strcpy(general->eventfile,argv[3]);
   else
      strcpy(general->eventfile,"-");
}

void read_setup(General *general,Measurement *meas,Concentration *conc)
{
   FILE *fp;
   char buf[NLINE],*value,beam[NELESYM];
   double v_beam;
   int cont=TRUE,c,i;

   general->vmax = 0.0; 
   conc->dstep = 100*1.0e15/C_CM2;
   conc->density = 5.0*C_G_CM3;
   general->scale = FALSE;
   general->niter=NITER;
   general->maxdstep = MAXDSTEP;
   general->maxelements = MAXELEMENTS;
   general->maxnucmasses = MAXNUCMASSES;

   fp = fopen(general->setupfile,"r");
   
   if(fp == NULL){
      fprintf(stderr,"Could not open input file %s\n",general->setupfile);
      exit(6);
   } else {
      fprintf(stderr,"Using setup file %s\n", general->setupfile);
   }

   i = 0;
   while(fgets(buf,NLINE,fp) != NULL && cont){
      value = read_inputline(buf,I_BEAM);
      if(value != NULL){
         c = sscanf(value,"%s",beam);
         if(c != 1)
            file_error(general->setupfile,i+1);
         c = get_nuclide(beam,&(meas->Z),&(meas->A),&(meas->M));
         if(!c){
            fprintf(stderr,"Nuclide not found for projectile %s\n",beam);
         }
      }
      value = read_inputline(buf,I_ENERGY);
      if(value != NULL){
         c = sscanf(value,"%lf",&(meas->E));
         if(c != 1)
            file_error(general->setupfile,i+1);
         meas->E *= C_MEV;
      }
      value = read_inputline(buf,I_DETANGLE);
      if(value != NULL){
         c = sscanf(value,"%lf",&(meas->detector_angle));
         if(c != 1)
            file_error(general->setupfile,i+1);
         meas->detector_angle *= C_DEG;
      }
      value = read_inputline(buf,I_TARANGLE);
      if(value != NULL){
         c = sscanf(value,"%lf",&(meas->target_angle));
         if(c != 1)
            file_error(general->setupfile,i+1);
         meas->target_angle *= C_DEG;
      }
      value = read_inputline(buf,I_DETDIST);
      if(value != NULL){
         c = sscanf(value,"%lf",&(meas->det_dist));
         if(c != 1)
            file_error(general->setupfile,i+1);
         meas->det_dist *= C_MM;
      }
      value = read_inputline(buf,I_STOSTEP);
      if(value != NULL){
         c = sscanf(value,"%lf",&(conc->dstep));
         if(c != 1)
            file_error(general->setupfile,i+1);
         conc->dstep *= 1.0e15/C_CM2;
      }
      value = read_inputline(buf,I_OUTSTEP);
      if(value != NULL){
         c = sscanf(value,"%lf",&(general->outstep));
         if(c != 1)
            file_error(general->setupfile,i+1);
         general->outstep *= 1.0e15/C_CM2;
      }
      value = read_inputline(buf,I_DENSITY);      
      if(value != NULL){
         c = sscanf(value,"%lf",&(conc->density));
         if(c != 1)
            file_error(general->setupfile,i+1);
         conc->density *= C_G_CM3;
      }
      value = read_inputline(buf,I_SCALE);
      if(value != NULL){
         c = sscanf(value,"%lf %lf",&(general->minscale),&(general->maxscale));
         if(c != 2)
            file_error(general->setupfile,i+1);
         general->minscale *= 1.0e15/C_CM2;
         general->maxscale *= 1.0e15/C_CM2;
         general->scale = TRUE;
      }
      value = read_inputline(buf, I_CROSS_SECTION);
      if(value != NULL) {
         c = sscanf(value, "%i", (int *) &(general->cs));
         if( c != 1)
            file_error(general->setupfile, i+1);
      }
      value = read_inputline(buf, I_MAXDSTEP);
      if(value != NULL) {
        c = sscanf(value, "%i", (int *) &(general->maxdstep));
        if( c != 1)
           file_error(general->setupfile, i+1);
      }
      value = read_inputline(buf, I_NITER);
      if(value != NULL) {
        c = sscanf(value, "%i", (int *) &(general->niter));
        if( c != 1)
           file_error(general->setupfile, i+1);
      }
      i++;
   }

   v_beam = sqrt((2.0*meas->E)/meas->M);
   if(v_beam > general->vmax)
      general->vmax = v_beam;
   
   fclose(fp); 
}

char *read_inputline(char *buf,int input_type)
{
   char *p;
   
   p = strstr(buf,inlines[input_type]);
   
   if(p != NULL)
      p = buf + strlen(inlines[input_type]);
      
   return(p);
      
}
void file_error(char *fname,int line)
{
   fprintf(stderr,"Error in input file %s at line %i\n",fname,line);
   exit(3);
   
}
void read_events(General *general,Measurement *meas,Event *event,
                 Concentration *conc)
{
   FILE *fp;
   char buf[NLINE],type[TYPELEN];
   double x,y,E,M,w,det_dist;
   int c,Z,A,n,i=0,cont=TRUE,j,k;

   if(!strncmp(general->eventfile,"-",1) && strlen(general->eventfile) == 1)
      fp = stdin;
   else
      fp = fopen(general->eventfile,"r");

   if(fp == NULL){
      fprintf(stderr,"Could not open file %s\n",general->eventfile);
      exit(1);
   }

   det_dist = meas->det_dist/C_MM;
   
   while(fgets(buf,NLINE,fp) != NULL && cont){
      c = sscanf(buf,"%lf %lf %lf %i %lf %s %lf %i",
                 &x,&y,&E,&Z,&M,type,&w,&n);
      if(c != 8){
         fprintf(stderr,"Problems at input line %i\n",i+1);
      }
      if(i < MAXEVENTS){
         event[i].theta = meas->detector_angle + x;
         event[i].fii = y;
         event[i].E = E*C_MEV;
         event[i].Z = Z;
#ifdef DEBUG
         printf("%5i %10.3f %10.3f\n",Z,event[i].theta/C_DEG,event[i].E/C_MEV);
#endif
         event[i].M = M*C_U;
         event[i].A = (int) (M + 0.5);
         A = event[i].A;
         event[i].w0 = w;
         event[i].w = w/ipow2(Z*(1.0 + meas->M/event[i].M));
         event[i].n = n;
         event[i].v = sqrt(2.0*event[i].E/event[i].M);
         if(event[i].v > general->vmax)
            general->vmax = event[i].v;
         event[i].d = 0.0;
         k = (int) (event[i].d/conc->dstep);
         conc->w[Z][k] += event[i].w;
         conc->n[Z][k] ++;
         conc->wsum[k] += event[i].w;
         conc->nsum[k] ++;
         (general->element[Z])++;
         (general->nuclide[Z][A])++;
         general->M[Z] = M*C_U;
         if(!strncmp(type,"ERD",TYPELEN)){
            event[i].type = ERD;           
         } else if(!strncmp(type,"RBS",TYPELEN)){
            event[i].type = RBS;
         } else {
            fprintf(stderr,"Event type neither ERD nor RBS!\n");
            exit(2);
         }
         i++;
      } else {
         cont = FALSE;
         fprintf(stderr,"Too many events, reading stopped at line %i\n",i+1);
      }   
   }
   fclose(fp);
   general->nevents = i;

/* We calculate the number of different isotopes for each element */

   for(i=0;i<general->maxelements;i++){
      for(j=1;j<general->maxnucmasses;j++)
         if(general->nuclide[i][j] > 0)
            (general->nuclide[i][0])++;
   }

   fprintf(stderr,"%i events read\n",general->nevents);
   
}
int get_nuclide(char *symbol,int *Z,int *A,double *M)
{
   FILE *fp;
   char S0[NELESYM];
   double M0,C0,maxC=0.0;
   int c=0,len,N0,Z0,A0,cont=TRUE;
   
   len = strlen(symbol);
   
   fp = fopen(XSTR(F_MASSES),"r");
   
   if(fp == NULL){
      fprintf(stderr,"Could not open mass file %s\n",XSTR(F_MASSES));
      exit(4);
   }
   
   while(isdigit(symbol[c]) && c < len)
      c++;
  
   if(c == len){
      fprintf(stderr,"Only digits in nuclide symbol %s\n",symbol);
      exit(5);
   }

   if(c > 0){
      *A = atoi(symbol);
      symbol += c;
   } else
      *A = 0;
               
   while(cont){
      c = fscanf(fp,"%i %i %i %s %lf %lf\n",&N0,&Z0,&A0,S0,&M0,&C0);
      if(c == 6){
         if(*A > 0){
            if(strcmp(symbol,S0) == 0 && *A == A0){
               *Z = Z0;
               *M = M0*1e-6*C_U;
               cont = FALSE;
            }
         } else {
            if(strcmp(symbol,S0) == 0 && C0 > maxC){
               *Z = Z0;
               *A = A0;
               *M = M0*1e-6*C_U;
               maxC = C0;
            }
         }
      } else 
         cont = FALSE;
   }
   
   fclose(fp);                    

   if(c == EOF)
      return(FALSE);
   else
      return(TRUE);
 
}
double ipow2(double x)
{
   return(x*x);
}
double ipow(double x,int a)
{
   int i;
   double value=1.0;
   
   for(i=0;i<a;i++)
      value *= x;

   return(value);
}
