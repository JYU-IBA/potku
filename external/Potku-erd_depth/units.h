
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

#define C_MEV_UM    1.0e-25

#define C_UG 	    1.0e-9

#define C_G	    1.0e-3
