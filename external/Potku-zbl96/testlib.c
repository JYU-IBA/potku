#include <stdio.h>
#include <stdlib.h>

#include "zbl96.h"

int main(int argc,char *argv[])
{
   double **S,m1,m2,den,mine,maxe,estep;
   unsigned int flag;
   int i,n,z1,z2;

   z1 = 14;
   z2 = 14;
   m1 = 27.977;
   m2 = 28.086;
   den = 2.321;
   mine = 0.0;
   maxe = 50.0;
   estep = 0.1;
   
   /* We calculate the effective charge fraction as a function of energy */
         
   flag =  (ZBL_EFFCHARGE | ZBL_MEV | ZBL_N_NO);
      
   S = zbl96(z1,z2,m1,m2,den,mine,maxe,estep,flag,&n);
   
   for(i=0;i<n;i++)
      printf("%12.5f %12.5f\n",S[0][i],S[1][i]);

   free(S[0]);
   free(S[1]);
   free(S);   
         
   exit(0);
}
