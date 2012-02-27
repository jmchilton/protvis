include ../config.mk
SOURCES=main.cpp handlers.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=pepxml
LIBS=../$(BUILD_DIR)/common.a -lexpat

all: $(SOURCES) $(EXECUTABLE)
	
$(EXECUTABLE): $(OBJECTS)
	$(MKDIR) ../$(BUILD_DIR)
	$(CC) $(LDFLAGS) $(OBJECTS) -o ../$(BUILD_DIR)/$@ $(LIBS)

.cpp.o:
	$(CC) $(CFLAGS) $< -c -o $@

clean:
	$(RM) -f *.o
