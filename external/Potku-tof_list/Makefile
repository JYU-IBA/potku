
INSTALLDIR = ../bin
DATADIR    = ../share
LIBDIR     = ../lib
INCDIR     = ../include

CC=gcc
CFLAGS  = -g -Wall -Wmissing-prototypes # -DDEBUG
#CFLAGS += -I${PWD}/$(INCDIR) -DDATAPATH=${PWD}/$(DATADIR)
#CFLAGS += -I$(INCDIR) -DDATAPATH=$(DATADIR) -DDEBUG
CFLAGS += -I$(INCDIR) -DDATAPATH=$(DATADIR) -DDEBUG

LIB= -lgsto
LIB+= -lm

#LDFLAGS=-g -L${PWD}/$(LIBDIR)
LDFLAGS=-g -L$(LIBDIR)

# LDFLAGS=
OBJS=tof_list.o
PROG=tof_list

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
