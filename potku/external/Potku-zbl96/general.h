/*
        Zbl96 is a program for calculating electronic and nuclear
        stopping powers according to the semiempirical model of
        Ziegler, Biersack and Littmark.
        
        This program is based on the version 96 of Srim-code.
        
        Version 0.9 written by K. Arstila 16.10.1996
        Version 0.99 written by K. Arstila 10.11.1999
        Version 0.99a written by K. Arstila 3.2.2000
        
        DO NOT DISTRIBUTE OUTSIDE THE UNIVERSITY OF 
        JYVASKYLA WITHOUT PERMISSION OF THE AUTHOR

                        Kai.Arstila@Helsinki.FI

*/

#define COLS 54+1
#define ROWS 93+1
#define HEAD 2
#define ACOLS 16
#define BCOLS 38
#define LINE 250

#define NA 6.022e23

#define TRUE  1
#define FALSE 0 

#define MAI 0 
#define NATURAL -1

#define max(A,B)  ((A) > (B)) ? (A) : (B)
#define min(A,B)  ((A) < (B)) ? (A) : (B)

#define XSTR(x) STR(x)
#define STR(x) #x

void readscoef(double [][COLS]);
double pstop(int,double,double [][COLS]);
double hestop(int,double,double [][COLS]);
double heeff(int,double);
double histop(int,int,double,double [][COLS]);
double hieff(int,int,double,double [][COLS]);
double nuclear(int,int,double,double,double);
double intpow(double,int);

