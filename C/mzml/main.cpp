#include "../common/stdinc.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "handlers.h"

#define BUFFER_SIZE 16384 //16KB read buffer

int main(int argc, char *argv[]) {
	if (argc == 2) {
		InitaliseMS1Cache();
		/*DWORD nWidth = state.MS1.GetSpectrumCount();
		while (nWidth > 2048) {
			nWidth >>= 1;
		}
		DWORD nHeight = (DWORD)(state.MS1.GetMzRange() + 0.5f);
		while (nHeight > 1024) {
			nHeight >>= 1;
		}*/
		for (float n = 0.05f; n <= 1.0f; n += 0.05f) {
			MemoryStream *pStream = MS1Plot::RenderFromFileSmooth(argv[1], 1500, 1000, pow(n, 1.2f));
			char szLcFile[128];
			sprintf(szLcFile, "%s_ms1_%d", argv[1], (int)(n * 20.0f + 0.5f));
			FILE *pFile = fopen(szLcFile, "wb");
			if (pFile == NULL) {
				printf("Failed to open the file %s for writing\n", szLcFile);
				return -1;
			}
			fwrite(pStream->GetBuffer(), 1, pStream->GetLength(), pFile);
			fclose(pFile);
		}
		ClearMS1Cache();
	} else if (argc == 3) {
		State state(argv[2], argv[1]);
		Transcode(argv[1], &state);
	} else {
		printf("Usage: %s <xml file> <binary file>\n", argv[0]);
		printf("OR\n");
		printf("Usage: %s <binary file>\n", argv[0]);
		return 1;
	}
	return 0;
}
