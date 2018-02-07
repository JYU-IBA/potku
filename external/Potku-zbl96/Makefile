
BININSTALLDIR  = ../Potku-bin
LIBINSTALLDIR  = ../Potku-lib
INCINSTALLDIR  = ../Potku-include
DATAINSTALLDIR = ../Potku-data


CC = gcc
# CFLAGS = -O2 -Wall -Wmissing-prototypes
CFLAGS = -g -Wall -Wmissing-prototypes 
CFLAGS += -DDATAPATH=$(DATAINSTALLDIR)
LIB = -lm
LDFLAGS = # -g
PROG = zbl96


OBJS = zbl96stop.o zbl96main.o 
LIBOBJS = zbl96stop.o zbl96lib.o

$(PROG): $(OBJS)
	$(CC) $(LFLAGS) -o $(PROG) $(OBJS) $(LIB)

lib: libzbl96.a $(LIBOBJS)

clean:
	rm  -f $(OBJS) $(LIBOBJS) $(PROG) libzbl96.a test_libzbl96 testlib.o 

testlib: testlib.o $(LIBOBJS) libzbl96.a
	$(CC) $(LDFLAGS) -o test_libzbl96 testlib.o -L. -lzbl96 $(LIB)

libzbl96.a: $(LIBOBJS)
	ar r libzbl96.a $(LIBOBJS)
	ranlib libzbl96.a

install:
	install -d $(BININSTALLDIR) 
	install $(PROG) $(BININSTALLDIR) 
	install -d $(DATAINSTALLDIR)
	install -m 644 scoef.95a scoef.95b masses.dat $(DATAINSTALLDIR)  

inst-lib: lib testlib
	install -d $(BININSTALLDIR) 
	install test_libzbl96 $(BININSTALLDIR)  
	install -d $(LIBINSTALLDIR)
	install -m 644 libzbl96.a $(LIBINSTALLDIR)  
	install -d $(INCINSTALLDIR)
	install -m 644 zbl96.h $(INCINSTALLDIR) 

depend .depend:
	$(CC) -MM *.c > .depend

include .depend
