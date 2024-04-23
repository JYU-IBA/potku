BINDIR = ../bin/
LIBDIR     = ../lib/
INCDIR     = ../include/
DATADIR = ../share/

CC = gcc
CFLAGS = -g -Wall
CFLAGS += -DDATAPATH=$(DATADIR)
CFLAGS += -I$(INCDIR)
#CFLAGS += -DDEBUG

LIB= -lm 

LDFLAGS = -g -lm -L$(LIBDIR)

AUX = srim_gen_stop gsto_stop

all: clean lib lib_install aux aux_install

aux: $(AUX)

lib: libgsto.a

libgsto.a: libgsto.o gsto_masses.o win_compat.o
	ar -vr libgsto.a win_compat.o libgsto.o gsto_masses.o
	ranlib libgsto.a

srim_gen_stop: srim_gen_stop.o
	$(CC) $(LDFLAGS) $^ -lgsto -o $@ $(LIB)

gsto_stop: gsto_stop.o
	$(CC) $(LDFLAGS) $^ -lgsto -o $@ $(LIB)

clean:
	rm -f *.a *.o $(AUX)

lib_install:
	install -d $(LIBDIR) 
	install libgsto.a $(LIBDIR)
	install -d $(INCDIR)
	install libgsto.h gsto_masses.h $(INCDIR)

aux_install:
	install -d $(BINDIR) 
	install gsto_stop srim_gen_stop $(BINDIR)
