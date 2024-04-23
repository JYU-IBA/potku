CC=gcc
CFLAGS=-Wall -g
LDFLAGS=
BINDIR=../bin/

OBJS=coinc.o
PROG=coinc

$(PROG): $(OBJS)
	$(CC) $(LDFLAGS) -o $(PROG) $(OBJS)
	
all: coinc

clean:
	rm -f $(OBJS) $(PROG)

coinc: coinc.o

install:
	install $(PROG) $(BINDIR)
