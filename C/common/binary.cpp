#include "binary.h"
#include "stdinc.h"

inline BYTE GetCharValue(char ch) {
	if (ch >= 'A' && ch <= 'Z') {
		return ch - 'A';
	} else if (ch >= 'a' && ch <= 'z') {
		return ch - 'a' + 26;
	} else if (ch >= '0' && ch <= '9') {
		return ch - '0' + 26 + 26;
	} else if (ch == '+') {
		return 62;
	} else if (ch == '/') {
		return 63;
	}
	return 0;
}

unsigned Base64Decode(const char *szSource, unsigned nSourceLen, BYTE *pDest) {
	if (nSourceLen & 0x3 || nSourceLen == 0) {
		return 0;
	}
	BYTE *pDst = pDest;
	nSourceLen = ((nSourceLen + 3) >> 2) - 1;
	DWORD nValue;
	for (unsigned i = 0; i < nSourceLen; ++i, szSource += 4, pDst += 3) {
		nValue = (GetCharValue(szSource[0]) << 18) | (GetCharValue(szSource[1]) << 12) | (GetCharValue(szSource[2]) << 6) | GetCharValue(szSource[3]);
		pDst[0] = (nValue >> 16) & 0xFF;
		pDst[1] = (nValue >> 8) & 0xFF;
		pDst[2] = nValue & 0xFF;
	}
	nValue = (GetCharValue(szSource[0]) << 6) | GetCharValue(szSource[1]);
	if (szSource[2] == '=') {
		nValue >>= 4;
		pDst[0] = nValue & 0xFF;
		++pDst;
	} else if (szSource[3] == '=') {
		nValue = (nValue << 4) | (GetCharValue(szSource[2]) >> 2);
		pDst[0] = (nValue >> 8) & 0xFF;
		pDst[1] = nValue & 0xFF;
		pDst += 2;
	} else {
		nValue = (nValue << 12) | (GetCharValue(szSource[2]) << 6) | GetCharValue(szSource[3]);
		pDst[0] = (nValue >> 16) & 0xFF;
		pDst[1] = (nValue >> 8) & 0xFF;
		pDst[2] = nValue & 0xFF;
		pDst += 3;
	}
	return pDst - pDest;
}

bool Base64DecodeToStream(const char *szSource, unsigned nSourceLen, OutputStream *pStream) {
	if (nSourceLen & 0x3 || nSourceLen == 0) {
		return false;
	}
	nSourceLen = ((nSourceLen + 3) >> 2) - 1;
	DWORD nValue;
	for (unsigned i = 0; i < nSourceLen; ++i, szSource += 4) {
		nValue = (GetCharValue(szSource[0]) << 18) | (GetCharValue(szSource[1]) << 12) | (GetCharValue(szSource[2]) << 6) | GetCharValue(szSource[3]);
		pStream->WriteByte((nValue >> 16) & 0xFF);
		pStream->WriteByte((nValue >> 8) & 0xFF);
		pStream->WriteByte(nValue & 0xFF);
	}
	nValue = (GetCharValue(szSource[0]) << 6) | GetCharValue(szSource[1]);
	if (szSource[2] == '=') {
		nValue >>= 4;
		pStream->WriteByte(nValue & 0xFF);
	} else if (szSource[3] == '=') {
		nValue = (nValue << 4) | (GetCharValue(szSource[2]) >> 2);
		pStream->WriteByte((nValue >> 8) & 0xFF);
		pStream->WriteByte(nValue & 0xFF);
	} else {
		nValue = (nValue << 12) | (GetCharValue(szSource[2]) << 6) | GetCharValue(szSource[3]);
		pStream->WriteByte((nValue >> 16) & 0xFF);
		pStream->WriteByte((nValue >> 8) & 0xFF);
		pStream->WriteByte(nValue & 0xFF);
	}
	return true;
}

bool InflateToStream(BYTE *pSource, unsigned nSourceLen, OutputStream *pStream) {
	z_stream strm;
	strm.zalloc = Z_NULL;
	strm.zfree = Z_NULL;
	strm.opaque = Z_NULL;
	strm.avail_in = 0;
	strm.next_in = Z_NULL;
	if (inflateInit(&strm) != Z_OK) {
		return false;
	}
	strm.avail_in = nSourceLen;
	strm.next_in = pSource;
	BYTE pOut[2048];
	int nRet = Z_STREAM_ERROR;
	do {
		strm.avail_out = sizeof(pOut);
		strm.next_out = pOut;
		nRet = inflate(&strm, Z_NO_FLUSH);
		if (nRet == Z_STREAM_ERROR || nRet == Z_NEED_DICT || nRet == Z_DATA_ERROR || nRet == Z_MEM_ERROR) {
			break;
		}
		pStream->Write(pOut, sizeof(pOut) - strm.avail_out);
	} while (strm.avail_out == 0);
	inflateEnd(&strm);
	return nRet == Z_STREAM_END;
}

bool Base64DecodeAndInflateToStream(const char *szSource, unsigned nLength, OutputStream *pStream) {
	BYTE *pZip = (BYTE *)malloc((nLength * 3) / 4);
	unsigned nZipLen = Base64Decode(szSource, nLength, pZip);
	if (nZipLen == 0) {
		free(pZip);
		return false;
	}
	bool bSuccess = InflateToStream(pZip, nZipLen, pStream);
	free(pZip);
	return bSuccess;
}
