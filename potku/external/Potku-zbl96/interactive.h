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

static const char *err_strings[] = {
    "no error",
    "too few command line parameters",
    "maximum energy smaller than minimum energy",
    "negative energy or velocity",
    "no such ion",
    "no such target",
    "no such isotope",
    "negative or zero step",
    "ion velocity exceeds the velocity of light"
};

void readparms(int,char **,int *,int *,double *,double *,double *,double *,
               double *,double *,unsigned int *,double [][COLS]);
void get_element(char *,int,int *,double *,double [][COLS]);
void usage(void);
void fatal_error(int);
