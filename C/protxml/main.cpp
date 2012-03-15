#include "../common/stdinc.h"
#include <stdio.h>
#include <string.h>
#include "handlers.h"

int main(int argc, char *argv[]) {
	if (argc != 3) {
		printf("Usage: %s <xml file> <binary file>\n", argv[0]);
	}
	State state(argv[2]);
	Transcode(argv[1], &state);
	return 0;
}
