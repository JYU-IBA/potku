#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

#include "zbl96.h"
#include "units.h"

#define NLINE 200
#define NAMELEN 100
#define NELESYM 10
#define MAXELEMENTS 100
#define MAXNUCMASSES 300
#define ERD 1
#define RBS 2
#define MAXEVENTS 1000000
#define MAXVSTEP 201
#define MAXDSTEP 101
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

#define F_MASSES ../Potku-data/masses.dat

#define NITER 3

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
   "Depths for concentration scaling:"
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
   int element[MAXELEMENTS];
   int nuclide[MAXELEMENTS][MAXNUCMASSES];
   char prefix[NAMELEN];
   double M[MAXELEMENTS];
   double outstep;
   double minscale,maxscale;
   int scale;
} General;

typedef struct {
   double vstep;
   double dstep;
   double vdiv;
   double ddiv;
   double *ele[MAXELEMENTS][MAXELEMENTS];
   double **sum[MAXELEMENTS];
} Stopping;

typedef struct {
   double dstep;
   double dmax;
   double w[MAXELEMENTS][MAXDSTEP];
   int n[MAXELEMENTS][MAXDSTEP];
   double wsum[MAXDSTEP];
   double mass[MAXDSTEP];
   int nsum[MAXDSTEP];
   double Ebeam[MAXDSTEP];
   double density;
   double *profile[MAXELEMENTS][MAXNUCMASSES];
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
void calculate_stoppings(General *,Measurement *,Stopping *);
void create_sumsto(void);
double *change_zblunits(double **,double,int);
void create_conc_profile(General *,Measurement *,Stopping *,
                         Concentration *);
void calculate_primary_energy(General *,Measurement *,Stopping *,
                              Concentration *);
double get_eloss(int,double,double,double,double,Stopping *);
double inter_sto(int,double,double,Stopping *);
void calculate_recoil_depths(General *,Measurement *,Event *,
                             Stopping *,Concentration *);
void output(General *,Concentration *,Event *);
void clear_conc(Concentration *);
char *get_symbol(int);
double Serd(int,double,int,double,double,double);
double Srbs(int,double,int,double,double,double);
double Srbs_mc(double,double,double,double);
double mc2lab_scatc(double,double,double);

/*void fpu(void);
void fpu_mask(void);*/

int main(int argc,char *argv[])
{
   General general;
   Stopping sto;
   Concentration conc;
   /*Event event[MAXEVENTS];*/ /* This might cause memory limit issues */
   Event *event;
   event=(Event *) malloc(MAXEVENTS*sizeof(Event));
   Measurement meas;
   int i;
   
   /*fpu();*/
   read_command_line(argc,argv,&general);
   read_setup(&general,&meas,&conc);
   clear_conc(&conc);
   read_events(&general,&meas,event,&conc);
   calculate_stoppings(&general,&meas,&sto);
   create_conc_profile(&general,&meas,&sto,&conc);

   for(i=0;i<NITER;i++){
      calculate_primary_energy(&general,&meas,&sto,&conc);
      clear_conc(&conc);
      calculate_recoil_depths(&general,&meas,event,&sto,&conc);
      create_conc_profile(&general,&meas,&sto,&conc);
   }

   output(&general,&conc,event);
   exit(0);
}
void output(General *general,Concentration *conc,Event *event)
{
   FILE *fp;
   char fname[NAMELEN],fnuc[NAMELEN];
   double max_change,nominal,wsum=0.0,dep,dep0,mdep,mdep0,d,r;
   int iz2,ia2,ie,z,a,ip,id,nprofile,minp,maxp;

   r = general->outstep/conc->dstep;

   nprofile = (MAXDSTEP*conc->dstep)/general->outstep + NABOVE;

   for(iz2=1;iz2<MAXELEMENTS;iz2++){
      if(general->element[iz2] > 0){
         for(ia2=1;ia2<MAXNUCMASSES;ia2++){
            if(general->nuclide[iz2][ia2]){
               conc->profile[iz2][ia2] = (double *) malloc(sizeof(double)*nprofile);
               for(ip=0;ip<nprofile;ip++)
                  conc->profile[iz2][ia2][ip] = 0.0;
            }
         }
      } else /* element exists */
         for(ia2=1;ia2<MAXNUCMASSES;ia2++)
	   conc->profile[iz2][ia2] = NULL;
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
      conc->profile[z][a][ip] += event[ie].w;
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
   
   for(iz2=1;iz2<MAXELEMENTS;iz2++){
      if(general->element[iz2] > 0){
         for(ia2=1;ia2<MAXNUCMASSES;ia2++){
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
                  fprintf(fp,"%10.3f %10.3f %10.3f ",d/(1.0e15/C_CM2),
                                                     (mdep-mdep0)/(C_UG/C_CM2),
                                                     (dep-dep0)/C_NM);
/*
                  fprintf(fp,"%10.3f ",(dep-dep0)/C_NM);
*/
                  fprintf(fp,"  %10.5f",conc->profile[iz2][ia2][ip]/wsum);
                  fprintf(fp,"  %14.5e\n",conc->profile[iz2][ia2][ip]);
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
         dE = get_eloss(Z,M,recE,d,dstep*dmult,sto);         
         rk = dE/dstep;
         bk = (conc->Ebeam[id+1]*K - conc->Ebeam[id]*K)/dstep;
         event[ie].d = 0.5*(d - dstep) + (conc->Ebeam[id]*K - (recE - dE))/(rk - bk);
         beamE = conc->Ebeam[0];
#ifdef DEBUG
         printf("A %8i %10.3f\n",Z,event[ie].d/(1.0e15/C_CM2));
#endif
      } else {
         while((id < MAXDSTEP) && (recE < beamE)){
            if(event[ie].type == ERD)
               dE = get_eloss(Z,M,recE,d,dstep*dmult,sto);
            else
               dE = get_eloss(meas->Z,meas->M,recE,d,dstep*dmult,sto);
            recE += dE;
            id++;
            d += dstep;
            beamE = conc->Ebeam[id]*K;
         }
         if(id < MAXDSTEP){
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

      if(id <  MAXDSTEP){
         if(event[ie].type == ERD){
            w = Serd(meas->Z,meas->M,event[ie].Z,event[ie].M,event[ie].theta,beamE);
         } else {
            w = Srbs(meas->Z,meas->M,event[ie].Z,event[ie].M,event[ie].theta,beamE);
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

double Serd(int z1,double m1,int z2,double m2,double t,double E)
{
   double value;

   value = ipow2(z1*z2*P_E*P_E/(8*PI*P_EPS0*E))*ipow2(1.0 + m1/m2)/
            ipow(cos(t),3);
                    
   return(value);
                       
}
double Srbs(int z1,double m1,int z2,double m2,double t,double E)
{
   double value,tcm,Ecm,r;

   Ecm = m2*E/(m1 + m2);
   r = m1/m2;

   tcm = t + asin(r*sin(t));;

   value = mc2lab_scatc(Srbs_mc(z1,z2,tcm,Ecm),tcm,t);
   
   return(value);
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
 
   while(id < MAXDSTEP){
#ifdef DEBUG
      printf("P %14.5e %14.5e\n",(d*C_CM2)/1.0e15,E/C_MEV);
#endif
      conc->Ebeam[id] = E;
      E -= get_eloss(meas->Z,meas->M,E,d,dstep*dmult,sto);
      d += dstep;
      id++;
   }
#ifdef DEBUG
   printf("%14.5e %14.5e\n",(d*C_CM2)/1.0e15,E/C_MEV);   
#endif
}
double get_eloss(int z,double m,double E,double d,double deltad,Stopping *sto)
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
         s1 = inter_sto(z,v,d,sto);
         if(E < s1*dstep)
            return(0.0);
         v2 = sqrt((2.0*(E - s1*dstep))/m);
         s2 = inter_sto(z,v2,d+dstep,sto);
   
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
double inter_sto(int z1,double v,double d,Stopping *sto)
{
   double **S;
   double value,s1,s2,vdiv,ddiv;
   int iv,id;
   
   S = sto->sum[z1];

   vdiv = sto->vdiv;
   ddiv = sto->ddiv;

   iv = (int) (v*vdiv);
   iv = min(max(0.0,iv),MAXVSTEP-2);

   id = (int) (d*ddiv);
   id = min(max(0.0,id),MAXDSTEP-2);

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
   for(id=0;id<MAXDSTEP;id++){
      for(iz2=1;iz2<MAXELEMENTS;iz2++){
         if(conc->wsum[id] > 0.0)
            conc->w[iz2][id] /= conc->wsum[id];
      }
      d += conc->dstep;
   }    

   n = 0;
   nsum = 0;
   for(id=0;id<MAXDSTEP;id++){
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
      for(iz2=1;iz2<MAXELEMENTS;iz2++)
         conc->w[iz2][id] = conc->w[iz2][n];

   for(id=1;id<MAXDSTEP;id++){
      if(conc->nsum[id] <= minn){
         for(iz2=1;iz2<MAXELEMENTS;iz2++)
            conc->w[iz2][id] = conc->w[iz2][id-1];
      }
   }

   for(iz1=1;iz1<MAXELEMENTS;iz1++){
      if(general->element[iz1] > 0){
         if(sto->sum[iz1] == NULL){
               p = (double **) malloc(sizeof(double *)*MAXVSTEP);
               for(iv=0;iv<MAXVSTEP;iv++)
                  p[iv] = malloc(sizeof(double)*MAXDSTEP);
               sto->sum[iz1] = p;         
         }
         for(id=0;id<MAXDSTEP;id++)
            for(iv=0;iv<MAXVSTEP;iv++)
               sto->sum[iz1][iv][id] = 0.0;         
      } 
   }
   
   for(iz1=1;iz1<MAXELEMENTS;iz1++){
      if(general->element[iz1] > 0){
         for(iz2=1;iz2<MAXELEMENTS;iz2++)
            if(general->element[iz2] > 0){
               for(id=0;id<MAXDSTEP;id++)
                  for(iv=0;iv<MAXVSTEP;iv++)
                     sto->sum[iz1][iv][id] += 
                          conc->w[iz2][id]*sto->ele[iz1][iz2][iv];
            }
               
      }   
   }

#ifdef DEBUG
   for(iv=0;iv<MAXVSTEP;iv++){
      printf("%3i %10.4f %14.5e\n",iv,conc->w[14][0],sto->sum[53][iv][0]);
   }
#endif

   printf("\n");

   for(id=0;id<MAXDSTEP/10;id++){
      printf("%6.1f ",(id*conc->dstep)/(1.0e15/C_CM2));
      for(iz2=1;iz2<MAXELEMENTS;iz2++){
         if(general->element[iz2] > 0){
            printf("%2i %4.1f ",iz2,conc->w[iz2][id]*100.0);
         }      
      }
      printf("\n");
   }

}
void clear_conc(Concentration *conc)
{
   int iz2,id;

   for(iz2=0;iz2<MAXELEMENTS;iz2++){
      for(id=0;id<MAXDSTEP;id++){
         conc->w[iz2][id] = 0.0;
         conc->n[iz2][id] = 0;
      }
   }
   for(id=0;id<MAXDSTEP;id++){
      conc->wsum[id] = 0.0;
      conc->nsum[id] = 0;
   }

}
void calculate_stoppings(General *general,Measurement *meas,
                         Stopping *sto)
{
   unsigned int zbl_flag;
   int i,j,z1,z2,n_zbl;
   double m1,m2,density,minv,maxv,vstep;
   double **stop;

   m1 = m2 = density = minv = 0.0;

   general->vmax *= 1.2;
   
   vstep = general->vmax/(MAXVSTEP - 1.0);
   maxv = general->vmax;
   
   sto->vstep = vstep;
   sto->vdiv = 1.0/vstep;   

   zbl_flag = (ZBL_EV_1E15ATOMS_CM2 | ZBL_M_S | ZBL_N_NO);
   
   for(i=1;i<MAXELEMENTS;i++){
      sto->sum[i] = NULL;
      for(j=1;j<MAXELEMENTS;j++){      
         sto->ele[i][j] = NULL;
      }
   }

   for(i=1;i<MAXELEMENTS;i++){
      if(general->element[i] > 0){
         z1 = i;
         for(j=1;j<MAXELEMENTS;j++){
            if(general->element[j] > 0){
               z2 = j;
               stop = zbl96(z1,z2,m1,m2,density,minv,maxv,vstep,zbl_flag,&n_zbl);     
               sto->ele[z1][z2] = change_zblunits(stop,C_EVCM2_1E15ATOMS,n_zbl);
            }
         }
      }
   }

}

double *change_zblunits(double **stop,double conv,int n)
{
   int i;
   
   for(i=0;i<n;i++)
      stop[1][i] *= conv;
      
   return(stop[1]);
   
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
   int cont=TRUE,c,i,j;

   general->vmax = 0.0;
   for(i=0;i<MAXELEMENTS;i++){
      general->element[i] = 0;
      for(j=0;j<MAXNUCMASSES;j++){
         general->nuclide[i][j] = 0;
      }
   }
      
   conc->dstep = 100*1.0e15/C_CM2;
   conc->density = 5.0*C_G_CM3;
   general->scale = FALSE;
  
   fp = fopen(general->setupfile,"r");
   if(fp == NULL){
      fprintf(stderr,"Could not open input file %s\n",general->setupfile);
      exit(6);
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
         general->element[meas->Z] ++;
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
         event[i].theta = meas->detector_angle - atan2(x,det_dist);
         event[i].fii = atan2(y,det_dist);
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

   for(i=0;i<MAXELEMENTS;i++){
      for(j=1;j<MAXNUCMASSES;j++)
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
