#ifndef __BINARY_H__
	#define __BINARY_H__

	#include "../common/streams.h"
	
	unsigned Base64Decode(const char *szSource, unsigned nSourceLen, BYTE *pDest); //pDest must have at least ((nSourceLen * 3) / 4) bytes of space
	bool Base64DecodeToStream(const char *szSource, unsigned nSourceLen, OutputStream *pStream);
	bool InflateToStream(BYTE *pSource, unsigned nSourceLen, OutputStream *pStream);
	bool Base64DecodeAndInflateToStream(const char *szSource, unsigned nLength, OutputStream *pStream);

#endif
