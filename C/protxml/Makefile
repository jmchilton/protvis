include ../config.mk
SOURCES=main.cpp handlers.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=protxml
LIBS=../$(BUILD_DIR)/common.a

all: $(SOURCES) $(EXECUTABLE)
	
$(EXECUTABLE): $(OBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(OBJECTS) $(LDFLAGS) -o ../$(BUILD_DIR)/$@ $(LIBS)

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
