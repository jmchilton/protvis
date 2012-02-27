include ../compile.mk
include ../config.mk

SOURCES=handlers.cpp binary.cpp
OBJECTS=$(SOURCES:.cpp=.o)
LIBRARY=common.a

all: $(SOURCES) $(LIBRARY)
	
$(LIBRARY): $(OBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(AR) ../$(BUILD_DIR)/$@ $(OBJECTS)

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
