#ifdef WIN32
#include <windows.h>
#define sleep(x) = Sleep(1000*x)
#include <string.h>
char *strsep(char **stringp, const char *delim) {
	char *start= *stringp;
	char *p;

	p = (start != NULL) ? strpbrk(start, delim) : NULL;

	if(p==NULL) {
		*stringp=NULL;
	} else {
		*p = '\0';
		*stringp=p+1;
	}
	return start;
}
#endif
