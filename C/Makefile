include compile.mk
include config.mk

all: common mzml mgf pepxml protxml

exe: common mzml_exe mgf_exe pepxml_exe protxml_exe

.PHONY: common mzml pepxml protxml clean

common:
	$(MAKE) $(AM_MAKEFLAGS) -C $@ all
	
mzml:
	$(MAKE) $(AM_MAKEFLAGS) -C $@ all
	
mgf:
	#$(MAKE) $(AM_MAKEFLAGS) -C $@ all

pepxml:
	#$(MAKE) $(AM_MAKEFLAGS) -C $@ all

protxml:
	#$(MAKE) $(AM_MAKEFLAGS) -C $@ all
	
mzml_exe:
	$(MAKE) $(AM_MAKEFLAGS) -C mzml exe
	
mgf_exe:
	#$(MAKE) $(AM_MAKEFLAGS) -C mgf exe

pepxml_exe:
	#$(MAKE) $(AM_MAKEFLAGS) -C pepxml exe

protxml_exe:
	#$(MAKE) $(AM_MAKEFLAGS) -C protxml exe

clean:
	$(MAKE) $(AM_MAKEFLAGS) -C common clean
	$(MAKE) $(AM_MAKEFLAGS) -C mzml clean
	$(MAKE) $(AM_MAKEFLAGS) -C pepxml clean
	$(MAKE) $(AM_MAKEFLAGS) -C protxml clean
	$(RM) -rf $(BUILD_DIR) 
