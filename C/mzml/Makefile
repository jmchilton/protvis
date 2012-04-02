include ../compile.mk
include ../config.mk

SOURCES=handlers.cpp msplot.cpp main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
PYSOURCES=handlers.cpp msplot.cpp MzMlmodule.cpp
PYOBJECTS=$(PYSOURCES:.cpp=.o)
EXECUTABLE=../$(BUILD_DIR)/mzml
PYMODULE=../$(BUILD_DIR)/MzML.so
LIBS=../$(BUILD_DIR)/common.a

all: $(SOURCES) $(PYMODULE)

exe: $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(OBJECTS) $(LIBS) $(LDFLAGS) -o $@
	
$(PYMODULE): $(PYOBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(PYOBJECTS) -shared $(LIBS) $(PYTHON_LIB) $(LDFLAGS) -o $@
	cp $@ ../../MzML.so

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
