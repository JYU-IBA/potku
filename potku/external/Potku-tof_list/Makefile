
INSTALLDIR = ../Potku-bin
DATAINSTALLDIR = ../Potku-data
LIBINSTALLDIR = ../Potku-lib

CC=gcc
CFLAGS= -g -Wall -Wmissing-prototypes # -DDEBUG

CFLAGS += -DDATAPATH=$(DATAINSTALLDIR)

# CFLAGS= -Wall -O2 -fomit-frame-pointer
# CFLAGS= -O6 -mcpu=pentiumpro -funroll-loops -ffast-math -malign-double -fomit-frame-pointer
LIB= -lzbl96 -lm

LDFLAGS=-g -L${PWD}/$(LIBINSTALLDIR)

# LDFLAGS=
OBJS=tof_list.o
PROG=tof_list

$(PROG): $(OBJS)
	$(CC) $(LDFLAGS) -o $(PROG) $(OBJS) $(LIB)

clean:
	rm -f $(OBJS) $(PROG) .depend

depend .depend:
	$(CC) -MM *.c > .depend
include .depend

install:
	install -d $(INSTALLDIR) 
	install $(PROG) $(INSTALLDIR)
