include compile.mk
include config.mk

all: common mzml pepxml protxml

.PHONY: common mzml pepxml protxml clean

common:
	$(MAKE) $(AM_MAKEFLAGS) -C $@ all
	
mzml:
	$(MAKE) $(AM_MAKEFLAGS) -C $@ all

pepxml:
	#$(MAKE) $(AM_MAKEFLAGS) -C $@ all

protxml:
	#$(MAKE) $(AM_MAKEFLAGS) -C $@ all

clean:
	$(MAKE) $(AM_MAKEFLAGS) -C common clean
	$(MAKE) $(AM_MAKEFLAGS) -C mzml clean
	$(MAKE) $(AM_MAKEFLAGS) -C pepxml clean
	$(MAKE) $(AM_MAKEFLAGS) -C protxml clean
	$(RM) -rf $(BUILD_DIR) 
