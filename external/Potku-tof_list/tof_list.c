#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#ifdef WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#else
#include <libgen.h> /* for basename() */
#include <sys/param.h> /* for MAXPATHLEN */
#endif
/* #include <dirent.h> */


#include <libgsto.h>
#include <gsto_masses.h>
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
#define MAX_FACTOR  1.2

#define EFF_MEV     C_MEV
#define EFF_KEV     C_KEV
#define EFF_FRAC    1
#define EFF_PCT     0

#define MAXELEMENTS 100

#define MASS_FILE   DATAPATH/masses.dat
#define STOP_DATA   DATAPATH/stopping.bin

#define WORD_LENGTH 256
#define EFF_DIR_LENGTH 1024

#define max(A,B)  ((A) > (B)) ? (A) : (B)
#define min(A,B)  ((A) < (B)) ? (A) : (B)

#define XSTR(x) STR(x)
#define STR(x) #x

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
    double acalib1;
    double acalib2;
   double *ecalib;
   char eff_dir[EFF_DIR_LENGTH];
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

double **set_sto(gsto_table_t *, double, double, double);
double **set_weight(char *,int,Input *);
double get_weight(double **,double);
double get_mass(char *,int *);
double get_energy(double,double,double);
double get_eloss(double,double **);
/* int get_step(double,double **); */
void read_input(const char *, Input *);
double ipow(double,int);
char *filename_extension(const char *);

int main(int argc, char *argv[])
{
   FILE **fp,*fp2;
   Input input;
/* struct dirent **files; */

   char **symbol,*tmp;
   int evnum,i,noweight=FALSE,tech=ERD,tmpi,*Z,ZZ;
   int e,tof;
/* int *step; */
   double beamM,energy,*emax,*M,*M2,tmpd,***sto,***weight;
   gsto_table_t *table;

   if(argc < 3){
      printf("Usage: tof_list [config_file] [filename] [filename] ...\n");
      exit(1);
   }
   const char *tofin_filename = argv[1];

   fprintf(stderr, "%s: config from %s, %i cut files to process.\n", argv[0], argv[1], argc-2);
#ifdef DEBUG
   int argi;
   for(argi=0; argi < argc; argi++) {
        fprintf(stderr, "argv[%i] = \"%s\"\n", argi, argv[argi]);
   }
   fprintf(stderr, "\n");
#endif
   argv += 2;
   argc -= 2;

   fp = (FILE **) malloc(sizeof(FILE *)*(argc));
   input.ecalib = (double *) malloc(sizeof(double)*(argc));
   symbol = (char **) malloc(sizeof(char *)*(argc));
   tmp = (char *) malloc(sizeof(char)*WORD_LENGTH);
/*   evnum = (int *) malloc(sizeof(int)*(argc)); */
/* step = (int *) malloc(sizeof(int)*(argc)); */
   Z = (int *) malloc(sizeof(int)*(argc));
/*   e = (double *) malloc(sizeof(double)*(argc)); */
   emax = (double *) malloc(sizeof(double)*(argc));
   M = (double *) malloc(sizeof(double)*(argc));
   M2 = (double *) malloc(sizeof(double)*(argc));
/*   tof = (double *) malloc(sizeof(double)*(argc)); */
   sto = (double ***) malloc(sizeof(double **)*(argc));
   weight = (double ***) malloc(sizeof(double **)*(argc));

   read_input(tofin_filename, &input);

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
    table=gsto_init(MAXELEMENTS, XSTR(STOPPING_DATA));
    if(!table) {
        fprintf(stderr, "Could not init stopping table.\n");
        return 0;
    }
    gsto_auto_assign_range(table, 1, MAXELEMENTS, 6, 6); /* TODO: only assign relevant stopping */
    if(!gsto_load(table)) {
        fprintf(stderr, "Error in loading stopping.\n");
        return 0;
    }
    for(i=0; i<argc; i++){
      char *filename=argv[i];
      fprintf(stderr, "file %i is \"%s\"\n", i, filename);
      input.ecalib[i] = 0.0;
      symbol[i] = (char *) malloc(sizeof(char)*3);
      fp[i] = fopen(filename, "r");
      if(fp[i] == NULL){
         fprintf(stderr,"Could not open data file %s\n", filename);
         exit(2);
      }
      char *extension = filename_extension(filename);
      fprintf(stderr, "extension: %s\n", extension);
      char *extension_orig=extension;
      Z[i]=0;
      while(isdigit(*extension)) Z[i] = Z[i]*10 + *extension++ - '0';
      while(isalpha(*extension)) *symbol[i]++ = *extension++; *symbol[i] = '\0';
      while(!isupper(*--symbol[i]));
      ZZ = Z[i];
      fprintf(stderr, "ZZ=%i (mass number), symbol[%i]=%s\n", ZZ, i, symbol[i]);
      M[i] = get_mass(symbol[i],&ZZ);
      fprintf(stderr, "ZZ=%i (the proton number corresponding to %s\n", ZZ, symbol[i]);
	  M2[i] = 0;
      tmpi = input.beamZ;
      beamM = get_mass(input.beam,&tmpi);
      emax[i] = input.beamE;
      sto[i] = set_sto(table, (Z[i])?Z[i]:ZZ,M[i],emax[i]*MAX_FACTOR);
      fprintf(stderr, "For stopping purposes (in carbon foil), this is Z=%i and mass is %g u\n", ZZ, M[i]/C_U);
/*    step[i] = get_step(emax[i]*MAX_FACTOR,sto[i]); */
      weight[i] = set_weight(symbol[i],Z[i],&input);
      Z[i] = ZZ;
      if(*extension == '.'){
         if(*++extension == 'e'){
            tmp = strcpy(tmp,symbol[i]);
            if((fp2 = fopen(strcat(tmp,".calib"),"r")) == NULL){
               fprintf(stderr,"Could not locate calibration file %s\n",tmp);
               exit(3);
            }
            fscanf(fp2,"%lf",&input.ecalib[i]);
            fclose(fp2);
         }
      }
      free(extension_orig);
   }
   gsto_deallocate(table); /* Stopping data loaded in already, this is not used anymore */
   int derp_n;
   float user_weight = 1.0;
   char *herp_c = malloc(sizeof(char)*WORD_LENGTH); 
   char *herpderp_1=malloc(sizeof(char)*WORD_LENGTH);
   char *herpderp_2=malloc(sizeof(char)*WORD_LENGTH);
   char *herp_type=malloc(sizeof(char)*WORD_LENGTH);
   char *herp_scatter=malloc(sizeof(char)*WORD_LENGTH);
   char *herp_d = malloc(sizeof(char)*WORD_LENGTH);
   int herp_isotope=0;
   for(i=0; i < argc; i++){
      fprintf(stderr, "Processing file %i.\n", i);
	  tech = ERD;
      /* Don't read the first ten lines, except the one line which
         contains the user-specified weight factor which is memorized. */
      for(derp_n=0;derp_n<10;derp_n++){
	     fgets(herp_c, 256, fp[i]);
         if(derp_n == 1){//line number2 in cut file = RBS or ERD
            sscanf(herp_c, "%s %s", herpderp_1, herp_type);
			if (strcmp(herp_type, "RBS") == 0) {
                tech = RBS;
                fprintf(stderr, "This is RBS\n");
            }
         }
         if(derp_n == 2){ //line number3 in cut file = user weight factor
			sscanf(herp_c, "%s %s %f", herpderp_1, herpderp_2, &user_weight);
         }
		 if(derp_n == 5 && tech == RBS) { //line number6 in cut file = scatter element
            sscanf(herp_c, "%s %s %s", herpderp_1, herpderp_2, herp_d);

			// Parse isotope from string -separate mass from element (from line 6)
            herp_isotope=0;
			while(isdigit(*herp_d)) herp_isotope = herp_isotope*10 + *herp_d++ - '0';

			// Parse element
			sscanf(herp_d, "%5s", herp_scatter);

			fprintf(stderr, "Scatter element: %s\n", herp_scatter);
			fprintf(stderr, "Scatter isotope: %i\n", herp_isotope);
			double m_scatter=get_mass(herp_scatter, &herp_isotope);
            fprintf(stderr, "Scatter isotope mass: %8.4f\n", m_scatter/C_U);
			M2[i] = m_scatter;
			Z[i] = herp_isotope;  // here herp_isotope is proton number, not isotope number A
            fprintf(stderr, "M2[%i]=%g u and Z[%i]=%i\n", i, M2[i]/C_U, i, Z[i]);
			/*
			emax[i] = input.beamE*4.0*ipow(cos(input.theta*C_DEG),2)*beamM*M[i]/ipow(beamM+M[i],2);
#ifdef ZBL96
			sto[i] = set_sto((Z[i])?Z[i]:ZZ,M[i],emax[i]*MAX_FACTOR);
#else
			sto[i] = set_sto(stopping, (Z[i])?Z[i]:ZZ,M[i],emax[i]*MAX_FACTOR);
#endif
			*/
         }

	  }
       char *line = (char *) malloc(sizeof(char)*WORD_LENGTH);
       int ang1;
       double angle1;
       while(fgets(line, WORD_LENGTH, fp[i])) {
           if(sscanf(line, "%i %i %i %i", &tof, &e, &ang1, &evnum) == 4) {
                angle1=ang1*input.acalib1+input.acalib2;
           } else if(sscanf(line, "%i %i %i", &tof, &e, &evnum) == 3) {
                angle1=0.0;
           } else {
               fprintf(stderr, "Error in scanning input file.\n");
               break;
           }
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
               printf("%e %e ",angle1,ANGLE2);
               //printf("%10.5lf %3d %8.4f ",energy/C_MEV,Z[i],M[i]/C_U); // Original
               printf("%10.5lf %3d %8.4f ",energy/C_MEV, Z[i], (tech == RBS)?M2[i]/C_U:M[i]/C_U);
               printf("%s %6.3f %5d\n",(tech)?"ERD":"RBS",(noweight)?1.0:get_weight(weight[i],energy)*user_weight,evnum);
            }
         }
      }
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

   for(i=0; i < argc; i++)
      fclose(fp[i]);

   exit(0);

}

double **set_sto(gsto_table_t *table, double z, double m, double e)
{
    int i,n;
    double **sto;
    double E, S;
    fprintf(stderr, "set_sto(%p, z=%g, m=%g u, e=%g keV)\n", table, z, m/C_U, e/C_KEV);
    n=(int) (e/(STOPSTEP*C_MEV))+1;
    sto = malloc(sizeof(double *)*2);
    sto[0]=calloc(n, sizeof(double));
    sto[1]=calloc(n, sizeof(double));
    for(i=0; i<n; i++){
        E=i*STOPSTEP*C_MEV;
        S=gsto_sto_v(table, z, 6, velocity(E, m));
        sto[0][i] = E;
        sto[1][i] = S*C_MEVCM2_UG*C_MEV*P_NA/M_C;
    }

   return(sto);

}

double **set_weight(char *symbol, int z, Input *input)
{
   FILE *fp;
   char *file,*tmp,*yx,*kax;
   int i=0,multp=EFF_FRAC;
   double energy=0.0,pct=0.0,multe=EFF_MEV,**ret;

   tmp = file = (char *) malloc(sizeof(char)*WORD_LENGTH);
   yx = (char *) malloc(sizeof(char)*WORD_LENGTH);
   kax = (char *) malloc(sizeof(char)*WORD_LENGTH);
   ret = (double **) malloc(sizeof(double *)*2);
   fprintf(stderr, "set_weight(%s, %i, %p)\n", symbol, z, input);
   if(z){
      for(i=1; z/(i*10)>0; i*=10);
      for(; i>0; i/=10){
         *file++ = z/i + '0';
         z %= i;
      }
   }
   while((*file++ = *symbol++));
   file = strcat(tmp,".eff");
   //fprintf(stderr,"Directory: %s\n", input->eff_dir);
	if (strlen(input->eff_dir) > 0) {
		tmp = (char *) malloc(sizeof(char)*EFF_DIR_LENGTH+strlen(file)+2);
		strcpy(tmp, input->eff_dir);
		strcat(tmp, "/");
		strcat(tmp, file);
		file = tmp;
	}
   fp = fopen(file, "r");
   if(fp != NULL){
    fprintf(stderr,"Used efficiency file: %s\n", file);
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
      fprintf(stderr, "Got %i points from efficiency file. Highest energy %g MeV\n",i, ret[0][i-1]/C_MEV);
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

double get_mass(char *symbol, int *z) /* The second parameter (int *z) is actually mass number A as an input (with *z==0 we assume natural isotopic distribution) and simultaneously this function stores the proton number (Z) into z. So the same variable acts both as an input and an output and has different meanings. Whoever programmed this will be first against the wall when the revolution comes. */
{
   FILE *fp;
   char S[3];
   int A,N,Z;
   double C,M,MC=0.0,MM=0.0;
   fprintf(stderr, "Trying to find mass for \"%s\" (mass number A is %i)\n", symbol, *z);

   fp = fopen(XSTR(MASS_FILE),"r");
   if(fp == NULL){
      fprintf(stderr,"Could not open element mass file %s\n",XSTR(MASS_FILE));
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
	  //printf("else osa");
	  //printf("%i", *z);
      while(fscanf(fp,"%i %i %i %s %lf %lf\n",&N,&Z,&A,S,&M,&C) == 6)
         if(strcmp(symbol,S) == 0 && *z == A){
            fclose(fp);
			//printf("%i", *z);
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

void read_input(const char *input_file, Input *input)
{
   FILE *fp;
   char *read;
   int Z=0;

   fp = fopen(input_file, "r");
   if(fp == NULL){
      fprintf(stderr,"Could not open input file %s\n", input_file);
      exit(6);
   }
    char *line = (char *) malloc(sizeof(char)*WORD_LENGTH);
   read = (char *) malloc(sizeof(char)*WORD_LENGTH);

    input->acalib1=0.0;
    input->acalib2=0.0;

    while(fgets(line, WORD_LENGTH, fp)) {
        sscanf(line, "Angle calibration: %lf %lf", &input->acalib1, &input->acalib2);
    }
    fclose(fp);

    fp = fopen(input_file, "r");
   /* The loop here (word by word) is rediculous. I'm not going to touch it. */
   while(fscanf(fp, "%s", read)==1) {
      if(!strcmp(read,"Beam:")){
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         while(isdigit(*read)) Z = Z*10 + *read++ - '0';
         sscanf(read,"%s",input->beam);
         input->beamZ = Z;
      }
      else if(!strcmp(read,"Energy:")){
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->beamE = atof(read)*C_MEV;
      }
      else if(!strcmp(read,"Detector")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"angle:")){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->theta = atof(read);
      }
      else if(!strcmp(read,"Target")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"angle:")){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->target_angle = atof(read);
      }
      else if(!strcmp(read,"Toflen:")){
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->tof = atof(read);
      }
      else if(!strcmp(read,"Carbon")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"foil")){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"thickness")){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->foil_thick = atof(read);
      }
      else if(!strcmp(read,"TOF")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"calibration:")){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->calib1 = atof(read);
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         input->calib2 = atof(read);
      }
      else if(!strcmp(read,"Efficiency")){
         if(fscanf(fp,"%s",read) == 0 && strcmp(read,"directory:")){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
         if(fscanf(fp,"%s",read) == 0){
            fprintf(stderr,"Faulty input file %s\n",input_file);
            exit(7);
         }
		 sscanf(read,"%s",input->eff_dir);
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

char *filename_extension(const char *path) { /*  e.g. /bla/bla/tofe2363.O.ERD.0.cut => O.ERD.0.cut */
#ifdef WIN32
    char *fname = malloc(_MAX_FNAME);
    char *fname_orig = fname;
    char *ext = malloc(_MAX_EXT);
    _splitpath(path, NULL, NULL, fname, ext);
    while(*fname++ != '.');
    char *out = malloc(_MAX_FNAME+_MAX_EXT);
    *out = '\0';
    strcat(out, fname);
    strcat(out, ext);
    free(fname_orig);
    free(ext);
    return out;
#else
    char *ext;
    char *base = strdup(path);
    char *base_orig=base;
    base=basename(base);
    while(*base++ != '.');
    ext = strdup(base);
    free(base_orig);
#endif
    return ext;
}
