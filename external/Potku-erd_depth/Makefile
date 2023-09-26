INSTALLDIR = ../bin
DATADIR    = ../share
LIBDIR     = ../lib
INCDIR     = ../include

CC = gcc
CFLAGS = -g -Wall -Wmissing-prototypes # -DDEBUG
#CFLAGS += -I${PWD}/$(INCDIR) -DDATAPATH=${PWD}/$(DATADIR)
CFLAGS += -I$(INCDIR) -DDATAPATH=$(DATADIR)

# CFLAGS= -Wall -O2 -fomit-frame-pointer
# CFLAGS= -O6 -mcpu=pentiumpro -funroll-loops -ffast-math -malign-double -fomit-frame-pointer

LIB= -lgsto
LIB+= -lm

LDFLAGS = -g -L$(LIBDIR)

OBJS = erd_depth.o

PROG = erd_depth

$(PROG): $(OBJS)
	$(CC) $(LDFLAGS) -o $(PROG) $(OBJS) $(LIB)

clean:
	rm -f $(OBJS) $(PROG) .depend

depend .depend:
	$(CC) -I$(INCDIR) -MM *.c > .depend
include .depend

install:
	install -d $(INSTALLDIR) 
	install $(PROG) $(INSTALLDIR)
