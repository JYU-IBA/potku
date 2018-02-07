/*
        Zbl96 is a program for calculating electronic and nuclear
        stopping powers according to the semiempirical model of
        Ziegler, Biersack and Littmark.

        This program is based on the version 96 of Srim-code.

        Version 0.94 written by K. Arstila 29.7.1998
        Version 0.99 written by K. Arstila 10.11.1999
        Version 0.99a written by K. Arstila 3.2.2000
                       
        DO NOT DISTRIBUTE OUTSIDE THE UNIVERSITY OF 
        JYVASKYLA WITHOUT PERMISSION OF THE AUTHOR

                        Kai.Arstila@Helsinki.FI

*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include "zbl96.h"
#include "general.h"

double **zbl96(int z1,int z2,double m1,double m2,double rho,
              double min,double max,double step,unsigned int flag,int *num)
{
   static double scoef[ROWS][COLS];
   double E,x,sunit=1.0,xunit=1.0;
   double **S;
   int i,n;

   readscoef(scoef);
   
   switch(flag & ZBL_SUNIT){
      case ZBL_EV_A:
         sunit = 100.0*NA*rho/(m2*1.0e25);      
         break;
      case ZBL_KEV_NM:
         sunit = NA*rho/(m2*1.0e25);
         break;
      case ZBL_KEV_UM:
         sunit = 1000.0*NA*rho/(m2*1.0e25);
         break;
      case ZBL_MEV_MM:
         sunit = 1000.0*NA*rho/(m2*1.0e25);
         break;
      case ZBL_KEV_UG_CM2:
         sunit = NA/(m2*1e24);
         break;
      case ZBL_MEV_MG_CM2:
         sunit = NA/(m2*1e24);
         break;
      case ZBL_KEV_MG_CM2:
         sunit = 1000.0*NA/(m2*1e24);
         break;
      case ZBL_EV_1E15ATOMS_CM2:
         sunit = 1.0;
         break;
      case ZBL_EFFCHARGE:
         sunit = 1.0;
         break;
   }
   switch(flag & ZBL_XUNIT){
      case ZBL_EV:
         xunit = 1000.0;
         break;
      case ZBL_KEV:
         xunit = 1.0;
         break;
      case ZBL_MEV:
         xunit = 0.001;
         break;
      case ZBL_V0:
         xunit = 1.0;
         break;
      case ZBL_BETA:
         xunit = 0.0072974;
         break;
      case ZBL_M_S:
         xunit = 2187673.0;
         break;
      case ZBL_CM_S:
         xunit = 218767300.0;
         break;
   }

   for(x=min,i=0;x<=max;x+=step,i++);
   n = max(1,i);

   S = (double **) malloc(sizeof(double *)*2);
   S[0] = (double *) malloc(sizeof(double)*n);
   S[1] = (double *) malloc(sizeof(double)*n);

   if(S[0] == NULL || S[1] == NULL){
      fprintf(stderr,"Could not allocate memory for %i stopping values\n",n);
      exit(10);
   }
     
   for(x=min,i=0;x<=max;x+=step,i++){
      switch(flag & ZBL_ENERGY){
         case FALSE:
            E = 25.0*x*x/(xunit*xunit);
            break;            
         default:
            E = x/(xunit*m1);
            break;
      }
      switch(z1){
         case 1:
            if((flag & ZBL_SUNIT) == ZBL_EFFCHARGE)
               S[1][i] = 1.0;
            else
               S[1][i] = pstop(z2,E,scoef);
            break;
         case 2:
            if((flag & ZBL_SUNIT) == ZBL_EFFCHARGE)
               S[1][i] = heeff(z2,E);
            else
               S[1][i] = hestop(z2,E,scoef);
            break;
         default:
            if((flag & ZBL_SUNIT) == ZBL_EFFCHARGE)
               S[1][i] = hieff(z1,z2,E,scoef);
            else
               S[1][i] = histop(z1,z2,E,scoef);
            break;
      }
      switch(flag & ZBL_NUCLEAR){
         case ZBL_N_ONLY:
            S[1][i] = nuclear(z1,z2,m1,m2,E*m1);
            break;
         case ZBL_N_BOTH:
            S[1][i] += nuclear(z1,z2,m1,m2,E*m1);
            break;
         case ZBL_N_NO:
            break;            
      }
      S[1][i] *= sunit;
      S[0][i] = x;
   }

   *num = n;   
   return(S);
}
