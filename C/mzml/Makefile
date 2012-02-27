include ../compile.mk
include ../config.mk

SOURCES=handlers.cpp msplot.cpp main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
PYSOURCES=handlers.cpp msplot.cpp MzMlmodule.cpp
PYOBJECTS=$(PYSOURCES:.cpp=.o)
EXECUTABLE=../$(BUILD_DIR)/mzml
PYMODULE=../$(BUILD_DIR)/MzML.so
LIBS=../$(BUILD_DIR)/common.a -lz -lexpat -lpng

all: $(SOURCES) $(EXECUTABLE) $(PYMODULE)
	

$(EXECUTABLE): $(OBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(LDFLAGS) $(OBJECTS) -o $@ $(LIBS)
	
$(PYMODULE): $(PYOBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(LDFLAGS) $(PYOBJECTS) -o $@ -shared $(LIBS) $(PYTHON_LIB)
	cp $@ ../../MzML.so

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
