INSTALLDIR = ../Potku-bin
DATADIR    = ../Potku-data
LIBDIR     = ../Potku-lib
INCDIR     = ../Potku-include

CC = gcc
CFLAGS = -g -Wall
# CFLAGS += -I${PWD}/$(INCDIR) -DDATAPATH=$(DATADIR)
CFLAGS += -I${PWD}/$(INCDIR) -DDATAPATH=$(DATADIR)

LIB= -lm 

LDFLAGS = -g -L${PWD}/$(LIBDIR)

ALL = genstop extract_stopping libsrim.a

all: $(ALL)

lib: libsrim.a

libsrim.a: libsrim.o


libsrim.a: libsrim.o 
	ar r libsrim.a libsrim.o
	ranlib libsrim.a

genstop: libsrim.o genstop.o
	$(CC) $(LDFLAGS) $^ $(LIB) -o $@

extract_stopping: libsrim.o extract_stopping.o
	$(CC) $(LDFLAGS) $^ $(LIB) -o $@

carbon_stopping.o: carbon_stopping.c
	$(CC) $(CFLAGS) -DZBL96 -c $^ -o $@

carbon_stopping: carbon_stopping.o
    # $(CC) $(LDFLAGS) $^ -lsrim -lzbl96 -o $@
	$(CC) $(LDFLAGS) $^ -lsrim -lzbl96 $(LIB) -o $@

clean:
	rm -f *.o $(ALL)

install:
	install -d $(INSTALLDIR) 
	install genstop extract_stopping $(INSTALLDIR)
	install -d $(LIBDIR) 
	install libsrim.a $(LIBDIR)
	install -d $(INCDIR)
	install libsrim.h $(INCDIR)

