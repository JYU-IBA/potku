BIN_DIR := Potku-bin/
LIB_DIR := Potku-lib/
INC_DIR := Potku-include/

BINS := $(addprefix $(BIN_DIR), gsto* coinc* erd_depth* tof_list* \
          srim_gen_stop*)
LIBS := $(addprefix $(LIB_DIR), libgsto.a)
INCS := $(addprefix $(INC_DIR), gsto_masses.h libgsto.h)

all:
	+$(MAKE) -C Potku-gsto
	+$(MAKE) clean -C Potku-tof_list
	+$(MAKE) -C Potku-tof_list
	+$(MAKE) install -C Potku-tof_list
	+$(MAKE) clean -C Potku-erd_depth
	+$(MAKE) -C Potku-erd_depth
	+$(MAKE) install -C Potku-erd_depth
	+$(MAKE) clean -C Potku-coinc
	+$(MAKE) -C Potku-coinc
	+$(MAKE) install -C Potku-coinc

clean:
	+$(MAKE) clean -C Potku-gsto
	+$(MAKE) clean -C Potku-coinc
	+$(MAKE) clean -C Potku-erd_depth
	+$(MAKE) clean -C Potku-tof_list

	rm -f $(BINS) $(LIBS) $(INCS)