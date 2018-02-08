#ifdef WIN32
#include <windows.h>
#define sleep(x) Sleep(1000*x)
char *strsep(char **, const char *);
#endif
