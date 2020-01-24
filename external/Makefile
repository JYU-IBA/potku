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