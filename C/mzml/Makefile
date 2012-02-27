include ../compile.mk
include ../config.mk

SOURCES=handlers.cpp msplot.cpp main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
PYSOURCES=handlers.cpp msplot.cpp MzMlmodule.cpp
PYOBJECTS=$(PYSOURCES:.cpp=.o)
EXECUTABLE=mzml
LIBS=../$(BUILD_DIR)/common.a -lz -lexpat -lpng

all: $(SOURCES) $(EXECUTABLE)
	

$(EXECUTABLE): $(OBJECTS) $(PYOBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(LDFLAGS) $(OBJECTS) -o ../$(BUILD_DIR)/$@ $(LIBS)
	$(CC) $(LDFLAGS) $(PYOBJECTS) -o ../$(BUILD_DIR)/MzML.so -shared $(LIBS) $(PYTHON_LIB)
	cp ../$(BUILD_DIR)/MzML.so ../../MzML.so

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
