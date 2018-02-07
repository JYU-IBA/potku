/*
        Zbl96 is a program for calculating electronic and nuclear
        stopping powers according to the semiempirical model of
        Ziegler, Biersack and Littmark.
        
        This program is based on the version 96 of Srim-code.
        
        Version 0.9 written by K. Arstila 16.10.1996
        Version 0.99 written by K. Arstila 10.11.1999
        Version 0.99a written by K. Arstila 3.2.2000
        
        DO NOT DISTRIBUTE OUTSIDE THE ACCELERATOR LABORATORY OF THE
        UNIVERSITY OF HELSINKI WITHOUT PERMISSION OF THE AUTHOR

                        Kai.Arstila@Helsinki.FI

*/

#define ZBL_EV_A                 0x0001
#define ZBL_KEV_NM               0x0002
#define ZBL_KEV_UM               0x0003
#define ZBL_MEV_MM               0x0004
#define ZBL_KEV_UG_CM2           0x0005
#define ZBL_MEV_MG_CM2           0x0006
#define ZBL_KEV_MG_CM2           0x0007
#define ZBL_EV_1E15ATOMS_CM2     0x0008
#define ZBL_EFFCHARGE            0x0009

#define ZBL_SUNIT                0x000f

#define ZBL_EV                   0x0010
#define ZBL_KEV                  0x0020
#define ZBL_MEV                  0x0030

#define ZBL_V0                   0x0100
#define ZBL_BETA                 0x0200
#define ZBL_M_S                  0x0300
#define ZBL_CM_S                 0x0400

#define ZBL_XUNIT                0x0ff0

#define ZBL_ENERGY               0x00f0
#define ZBL_VELOCITY             0x0f00

#define ZBL_N_ONLY               0x1000
#define ZBL_N_BOTH               0x2000
#define ZBL_N_NO                 0x3000

#define ZBL_NUCLEAR              0xf000

#define ZBL_DSA                  0xf0000

#define ZBL_DEFAULT (ZBL_KEV_NM | ZBL_V0 | ZBL_N_NO)

double **zbl96(int,int,double,double,double,double,double,double,unsigned
               int,int *);

/* 
   parameters for zbl96
      z1
      z2
      m1
      m2
      density
      mine
      maxe
      estep
      flag     (eg. KEV_NM | V0 | N_NO )
      n        ( number of calculated stopping values )

   output
   
      sto = zbl96(...)
   
      sto[0][n]   energy or velocity values
      sto[1][n]   stopping values
*/
