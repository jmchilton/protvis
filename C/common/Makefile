include ../compile.mk
include ../config.mk

SOURCES=handlers.cpp binary.cpp
OBJECTS=$(SOURCES:.cpp=.o)
LIBRARY=../$(BUILD_DIR)/common.a

all: $(SOURCES) $(LIBRARY)
	
$(LIBRARY): $(OBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(AR) $@ $(OBJECTS)

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
