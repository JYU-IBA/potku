#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
/* #include <dirent.h> */

#include "zbl96.h"

/*      Fundamental Physical Constants in SI-units      */

#define P_NA     6.0221367e23
#define P_ABOHR  0.529177249e-10
#define P_C      299792458
#define P_E      1.60217733e-19
#define P_EPS0   8.85419e-12

#ifndef PI
#ifdef M_PI
#define PI M_PI
#else
#define PI 3.14159265358979323846
#endif
#endif

/*      Conversion factors from non-SI units to SI-units        */
/*      Underline (_) in the constant name means division (/)   */

#define C_KEV_NM 1.6021773e-7   /* KeV/nm to J/m  */
#define C_U      1.6605402e-27  /* Atomic mass to kilograms */
#define C_V0     2187691.42     /* Bohr velocity to m/s */
#define C_EV     P_E            /* eV to J */
#define C_DEG    (PI/180.0)       /* degrees to radians */

/*      Dimensions of physical constants */

#define C_ANGSTROM  1.0e-10
#define C_NM        1.0e-9
#define C_UM        1.0e-6
#define C_MM        1.0e-3
#define C_CM        1.0e-2
#define C_FS        1.0e-15
#define C_PS        1.0e-12
#define C_NS        1.0e-09
#define C_KEV       (1000.0*C_EV)
#define C_MEV       (1000000.0*C_EV)
#define C_CM2       0.0001
#define C_CM3       0.000001

#define C_EVCM2_1E15ATOMS (C_EV*C_CM2/1.0e15) /* eVcm2/1e15 at. to Jm2/at. */

#define C_G_CM3     1000.0

#define C_BARN      1.0e-28

#define C_DEFAULT   1.0

#define ANGLE1      0.0
#define ANGLE2      0.0

#define C_MEVCM2_UG 1.0e-27

#define Z_C         6
#define M_C         12.0

#define ERD         1
#define RBS         0

#define TRUE        1
#define FALSE       0

#define STOPSTEP    0.1
#define CAL_ACC     0.02
#define MAX_FACTOR  2.0 //The makeup of makeup artists

#define EFF_MEV     C_MEV
#define EFF_KEV     C_KEV
#define EFF_FRAC    1
#define EFF_PCT     0

#define INPUT_FILE  "tof.in"
#define MASS_FILE   "../Potku-data/masses.dat"

#define WORD_LENGTH 30

#define max(A,B)  ((A) > (B)) ? (A) : (B)
#define min(A,B)  ((A) < (B)) ? (A) : (B)

typedef struct {
   char beam[3];
   double beamZ;
   double beamE;
   double theta;
   double target_angle;
   double tof;
   double foil_thick;
   double calib1;
   double calib2;
   double *ecalib;
} Input;

/*

# awk '{print ($1*-0.6339980E-10 + 0.5130320E-06)}' test2.out 
# | awk '{print (0.5*16*1.6605402e-27*(0.684/$1)^2)/1.6021773e-16}' 
# | hist 50 | xgra
 
# cat t307vs.H |awk '{if($2>0) print $0}'| 
# awk '{printf("%14.5e %14.5e\n",$1+(rand()-0.5),$2+(rand()-0.5))}' | 
# awk '{printf("%15.10e\n",($1*-0.6339980E-10 + 0.5130320E-06))}' | 
# awk '{printf("%15.10e\n",(0.001*0.5*1.0079*1.6605402e-27*(0.684/$1)^2)
# /1.6021773e-16)}' | hist 0.004 > t307vs.H.ene


tof.in
Beam:                   127I
Energy:                 53.0
Detector angle:         40
Target angle:           20
Toflen:                 0.684
Carbon foil thickness:  5.0 
TOF calibration:        -0.6339980e-10 0.5130320e-06
Efficiency:		1H 1H.eff

theta,fii,target angle,E,Z,M,ERD/RBS,w,#

*/

double **set_sto(double,double,double);
double **set_weight(char *,int);
double get_weight(double **,double);
double get_mass(char *,int *);
double get_energy(double,double,double);
double get_eloss(double,double **);
/* int get_step(double,double **); */
void read_input(Input *);
double ipow(double,int);

int main(int argc, char *argv[])
{
   FILE **fp,*fp2;
   Input input;
/* struct dirent **files; */

   char **symbol,*tmp;
   int count,evnum,i,j,noweight=FALSE,stop=0,tech=ERD,tmpi,*Z,ZZ;
   int e,tof;
/* int *step; */
   double beamM,energy,*emax,*M,tmpd,***sto,***weight;

   if(argc == 1){
      printf("Usage: tof_list [filename] [filename] ...\n");
      exit(1);
   }

   fp = (FILE **) malloc(sizeof(FILE *)*(argc-1));
   input.ecalib = (double *) malloc(sizeof(double)*(argc-1));
   symbol = (char **) malloc(sizeof(char *)*(argc-1));
   tmp = (char *) malloc(sizeof(char)*WORD_LENGTH);
/*   evnum = (int *) malloc(sizeof(int)*(argc-1)); */
/* step = (int *) malloc(sizeof(int)*(argc-1)); */
   Z = (int *) malloc(sizeof(int)*(argc-1));
/*   e = (double *) malloc(sizeof(double)*(argc-1)); */
   emax = (double *) malloc(sizeof(double)*(argc-1));
   M = (double *) malloc(sizeof(double)*(argc-1));
/*   tof = (double *) malloc(sizeof(double)*(argc-1)); */
   sto = (double ***) malloc(sizeof(double **)*(argc-1));
   weight = (double ***) malloc(sizeof(double **)*(argc-1));

   read_input(&input);

/* Useless filename.* feature

   for(i=0; (*tmp++ = *argv[1]++) != '.'; i++);
   for(j=i; j>0; j--,tmp--);
   if(*argv[1] == '*'){
      argc = 1;
      for(j=scandir(".",&files,0,alphasort); j>0; j--)
         if(!strncmp(files[j]->d_name,tmp,i))
            sscanf(files[j]->d_name,"%s",argv[argc++]);
   }
   else for(; i>-1; i--,argv[1]--);

*/

   for(i=0; i<argc-1; i++){
      input.ecalib[i] = 0.0;
      symbol[i] = (char *) malloc(sizeof(char)*3);
      fp[i] = fopen(argv[i+1],"r");
      if(fp[i] == NULL){
         fprintf(stderr,"Could not open data file %s\n",argv[i+1]);
         exit(2);
      }
      while(*argv[i+1]++ != '.');
      Z[i]=0; /* In Windows GCC, Z[i] is initialized with a large number as it's content, so this had to be done */
      while(isdigit(*argv[i+1])) Z[i] = Z[i]*10 + *argv[i+1]++ - '0';
      while(isalpha(*argv[i+1])) *symbol[i]++ = *argv[i+1]++; *symbol[i] = '\0';
      while(!isupper(*--symbol[i]));
      ZZ = Z[i]; //isotope
      M[i] = get_mass(symbol[i],&ZZ);
      tmpi = input.beamZ;
      beamM = get_mass(input.beam,&tmpi);
      emax[i] = input.beamE*4.0*ipow(cos(input.theta*C_DEG),2)*beamM*M[i]/ipow(beamM+M[i],2);
      sto[i] = set_sto((Z[i])?Z[i]:ZZ,M[i],emax[i]*MAX_FACTOR);
/*    step[i] = get_step(emax[i]*MAX_FACTOR,sto[i]); */
      weight[i] = set_weight(symbol[i],(Z[i])?Z[i]:ZZ);
      Z[i] = ZZ;
      if(*argv[i+1] == '.'){
         if(*++argv[i+1] == 'e'){
            tmp = strcpy(tmp,symbol[i]);
            if((fp2 = fopen(strcat(tmp,".calib"),"r")) == NULL){
               fprintf(stderr,"Could not locate calibration file %s\n",tmp);
               exit(3);
            }
            fscanf(fp2,"%lf",&input.ecalib[i]);
            fclose(fp2);
         }
      }
   }
   for(i=0; i<argc-2; i++)
      for(j=i+1; j<argc-1; j++)
         if(!strcmp(symbol[i],symbol[j])) noweight = TRUE;

   char herp_c [100];
   int derp_n;
   char herpderp_1 [10];
   char herpderp_2 [10];
   float user_weight = 1.0;
   for(i=0;i<argc-1;i++){
   
      /* Don't read the first ten lines, except the one line which 
         contains the user-specified weight factor which is memorized. */
      for(derp_n=0;derp_n<10;derp_n++){
	     fgets(herp_c, 100, fp[i]);
         if(derp_n == 2){
            sscanf(herp_c, "%s %s %f", &herpderp_1, &herpderp_2, &user_weight);
         }
         
	  }
      while(fscanf(fp[i], "%i %i %i", &tof, &e, &evnum) == 3){
         if(e > 0){
            if(tof == 0){
               energy  = e + ((double)(rand())/RAND_MAX) - 0.5;
               energy *= input.ecalib[i];
               energy *= C_MEV;
            } else {
               energy = tof +  ((double)(rand())/RAND_MAX) - 0.5;
               energy = get_energy(input.tof,energy*input.calib1 + input.calib2,M[i]);
            }
            tmpd = get_eloss(energy,sto[i]);
            energy = (tmpd > -0.1)?energy + tmpd*input.foil_thick:-1.0;
            if(energy > -0.1 && energy < emax[i]*MAX_FACTOR){
               printf("%5.1f %5.1f ",ANGLE1,ANGLE2);
               printf("%10.5lf %3d %8.4f ",energy/C_MEV,Z[i],M[i]/C_U);
               printf("%s %6.3f %5d\n",(tech)?"ERD":"RBS",(noweight)?1.0:get_weight(weight[i],energy)*user_weight,evnum);
            }
         }
      }
      fclose(fp[i]);
   }

#if 0
   for(i=0; i<argc-1; i++)
      fscanf(fp[i],"%lf %lf %d",&tof[i],&e[i],&evnum[i]);

   for(count=0; stop<argc-1; count++){
      stop = 0;
      for(i=0; i<argc-1; i++){
         if(!evnum[i]) stop++;
         else if(count == evnum[i]){
            if((int)(e[i])){
               if(!(int)(tof[i])) tof[i] = e[i];
               /* Randomize input channel */
                  tof[i] += -0.5 + ((double)(rand())/RAND_MAX);
               /* Calculate energy from channel */
                  tof[i] = (input.ecalib[i]>0.00001)?tof[i]*input.ecalib[i]:get_energy(input.tof,tof[i]*input.calib1 + input.calib2,M[i]);
               /* Calculate and add energy loss in carbon foil */
                  tmpd = get_eloss(tof[i],sto[i]);
                  tof[i] = (tmpd>-0.1)?tof[i]+tmpd*input.foil_thick:-1.0;
/*             for(j=0; j<step[i]; j++)
                  tof[i] += get_eloss(tof[i],sto[i])*input.foil_thick/step[i]; */
               if(tof[i]>-0.1 && tof[i]<emax[i]*MAX_FACTOR){
                  printf("%5.1f %5.1f ",ANGLE1,ANGLE2);
                  printf("%10.5lf %3d %8.4f ",tof[i]/C_MEV,Z[i],M[i]/C_U);
                  printf("%s %6.3f %5d\n",(tech)?"ERD":"RBS",(noweight)?1.0:get_weight(weight[i],tof[i]),evnum[i]);
               }
            }
            if(fscanf(fp[i],"%lf %lf %d",&tof[i],&e[i],&evnum[i]) != 3)
               evnum[i] = 0;
         }
      }
   }
#endif

   for(i=0; i<argc-1; i++)
      fclose(fp[i]);

   exit(0);

}

double **set_sto(double z, double m, double e)
{
   unsigned int flag;
   int i,n;
   double **sto;

   flag = (ZBL_EV_1E15ATOMS_CM2 | ZBL_MEV | ZBL_N_BOTH);

   sto = zbl96(z,Z_C,m/C_U,M_C,0.0,0.0,e/C_MEV,STOPSTEP,flag,&n);

   for(i=0; i<n; i++){
      sto[0][i] *= C_MEV;
      sto[1][i] *= C_MEVCM2_UG*C_MEV*P_NA/M_C;
   }

   return(sto);

}

double **set_weight(char *symbol, int z)
{
   FILE *fp;
   char *file,*tmp,*yx,*kax;
   int i=0,multp=EFF_FRAC;
   double energy=0.0,pct=0.0,multe=EFF_MEV,**ret;

   tmp = file = (char *) malloc(sizeof(char)*WORD_LENGTH);
   yx = (char *) malloc(sizeof(char)*WORD_LENGTH);
   kax = (char *) malloc(sizeof(char)*WORD_LENGTH);
   ret = (double **) malloc(sizeof(double *)*2);

   if(z){
      for(i=1; z/(i*10)>0; i*=10);
      for(; i>0; i/=10){
         *file++ = z/i + '0';
         z %= i;
      }
   }
   while((*file++ = *symbol++));
   file = strcat(tmp,".eff");

   while((fp = fopen(file,"r")) == NULL && isdigit(*file)) file++;
   if(fp != NULL){
      fscanf(fp,"%s %s",yx,kax);
      if(!strcmp(yx,"keV")) multe = EFF_KEV;
      else if(!strcmp(yx,"MeV")) multe = EFF_MEV;
      if(!strcmp(kax,"frac")) multp = EFF_FRAC;
      else if(!strcmp(kax,"pct")) multp = EFF_PCT;
      for(i=(isdigit(*yx)?1:0); fscanf(fp,"%lf %lf",&energy,&pct) == 2; i++);
      fclose(fp);
      ret[0] = (double *) malloc(sizeof(double)*(i+1));
      ret[1] = (double *) malloc(sizeof(double)*(i+1));
      fp = fopen(file,"r");
      if(!isdigit(*yx)) fscanf(fp,"%s %s",yx,kax);
      for(i=0; fscanf(fp,"%lf %lf",&energy,&pct) == 2; i++){
         ret[0][i] = energy*multe;
         ret[1][i] = (multp?1.0:100.0)/pct;
      }
      fclose(fp);
   } else {
      ret[0] = (double *) malloc(sizeof(double)*2);
      ret[1] = (double *) malloc(sizeof(double)*2);
      ret[0][0] = 0.0;
      ret[0][1] = 10.0;
      ret[1][0] = ret[1][1] = 1.0;
   }

   return(ret);

}

double get_weight(double **table, double e)
{
   int i;
   double ret;

   for(i=0; table[0][i]<e && table[0][i]; i++);

   i -= (table[0][i]?1:2);
   i = max(0,i);
   ret = table[1][i]+(table[1][i+1]-table[1][i])*(e-table[0][i])/(table[0][i+1]-table[0][i]);

   return(ret);

}

double get_mass(char *symbol, int *z)
{
   FILE *fp;
   char S[3];
   int A,N,Z;
   double C,M,MC=0.0,MM=0.0;

   fp = fopen(MASS_FILE,"r");
   if(fp == NULL){
      fprintf(stderr,"Could not open element mass file %s\n",MASS_FILE);
      exit(4);
   }

   if(*z == 0){
      while(fscanf(fp,"%i %i %i %s %lf %lf\n",&N,&Z,&A,S,&M,&C) == 6){
         if(strcmp(symbol,S) == 0){
            MM += M*C;
            if(C>MC){
               MC = C;
               *z = Z;
            }
         }
      }
      MM /= 100.0;
      if((int)(MM)){
         fclose(fp);
         return(MM*C_U/1.0e6);
      }
   } else
      while(fscanf(fp,"%i %i %i %s %lf %lf\n",&N,&Z,&A,S,&M,&C) == 6)
         if(strcmp(symbol,S) == 0 && *z == A){
            fclose(fp);
            *z = Z;
            return(M*C_U/1.0e6);
         }

   fprintf(stderr,"Could not find element %s\n",symbol);
   exit(5);

}

double get_energy(double s, double t, double m)
{
   double v,ret;

   v = s/t;
   ret = 0.5*m*v*v;

   return(ret);

}

double get_eloss(double e, double **sto)
{
   double s;
   int i;

   i = (int) (e/(STOPSTEP*C_MEV));

   i = max(0,i);

   if(e < sto[0][i])
      i--;

   if(e >= sto[0][i+1])
      i++;

   s = sto[1][i] + (sto[1][i+1] - sto[1][i])*(e - sto[0][i])/(sto[0][i+1] - sto[0][i]);

   if(s < 0 || s > e) s = -1.0;

   return(s);

}

/*

int get_step(double e, double **sto)
{
   int i=2,j;
   double esect,next,prev;

   prev = get_eloss(e,sto); next = prev*2;
   while(((next>prev)?next/prev:prev/next)>1.0+CAL_ACC){
      next = 0.0; esect = e;
      for(j=0; j<i; j++){
         next += get_eloss(esect,sto)/i;
         esect = e + prev/i;
      }
      i *= 2;
   }

   return(i);

}

*/

void read_input(Input *input)
{
   FILE *fp;
   char *read;
   int Z=0;

   fp = fopen(INPUT_FILE,"r");
   if(fp == NULL){
      fprintf(stderr,"Could not open input file %s\n",INPUT_FILE);
      exit(6);
   }

   read = (char *) malloc(sizeof(char)*WORD_LENGTH);

   while(fscanf(fp,"%s",read) == 1){
      if(!strcmp(read,"Beam:")){
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         while(isdigit(*read)) Z = Z*10 + *read++ - '0';
         sscanf(read,"%s",input->beam);
         input->beamZ = Z;
      }
      else if(!strcmp(read,"Energy:")){
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->beamE = atof(read)*C_MEV;
      }
      else if(!strcmp(read,"Detector")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"angle:")){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->theta = atof(read);
      }
      else if(!strcmp(read,"Target")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"angle:")){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->target_angle = atof(read);
      }
      else if(!strcmp(read,"Toflen:")){
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->tof = atof(read);
      }
      else if(!strcmp(read,"Carbon")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"foil")){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"thickness")){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->foil_thick = atof(read);
      }
      else if(!strcmp(read,"TOF")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"calibration:")){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->calib1 = atof(read);
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",INPUT_FILE);
            exit(7);
         }
         input->calib2 = atof(read);
      }
   }

   fclose(fp);

}

double ipow(double b, int e)
{
   double ret=1.0;

   while(e-->0) ret *= b;

   return (ret);

}
