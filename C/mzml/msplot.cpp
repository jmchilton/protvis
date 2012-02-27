#include <png.h>
#include "msplot.h"
#include <math.h>
#include "../common/handlers.h"

#define UPDATE_VAL(n) \
	nVal = pImg[nIdx]; \
	nVal += n; \
	/*nVal = 1.0f;*/ \
	pImg[nIdx] = nVal; \
	if (nVal > nMax) { \
		nMax = nVal; \
	}

static void PngWriterWrite(png_structp png_ptr, png_bytep data, png_size_t length) {
	((MemoryStream *)png_ptr->io_ptr)->Write(data, length);
}

static void PngWriterFlush(png_structp png_ptr) {
}

//MS1
//FIXME: Make caching threadsafe

#define CACHE_MAX 10
typedef struct {
	char ID[16];
	DWORD TimeStamp;
	MS1Plot::Cache Image;
} ImageCache;

static DWORD gs_nTimeStamp = 0;
ImageCache gs_cache[CACHE_MAX];

void InitaliseMS1Cache() {
	memset(gs_cache, 0, sizeof(gs_cache));
}

void ClearMS1Cache() {
	ImageCache *pCache = gs_cache;
	for (DWORD i = 0; i < CACHE_MAX; ++i, ++pCache) {
		if (pCache->ID == NULL) {
			break;
		} else if (pCache->Image.pImage != NULL) {
			free(pCache->Image.pImage);
		}
	}
}

static MemoryStream *RenderFromCache(MS1Plot::Cache &cache, float nDistortion) {
	MemoryStream *pStream = new MemoryStream();
	png_structp png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
	if (png_ptr != NULL) {
		png_infop info_ptr = NULL;
		png_bytep *pRows = NULL;
		if (setjmp(png_jmpbuf(png_ptr))) {
			puts("ERROR");
			if (pRows != NULL) {
				free(pRows);
			}
			png_destroy_write_struct(&png_ptr, &info_ptr);
			delete pStream;
			return NULL;
		}
		info_ptr = png_create_info_struct(png_ptr);
		if (info_ptr != NULL) {
			png_set_write_fn(png_ptr, pStream, &PngWriterWrite, &PngWriterFlush);
			png_set_IHDR(png_ptr, info_ptr, cache.nWidth, cache.nHeight, 8, PNG_COLOR_TYPE_GRAY, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
			png_write_info(png_ptr, info_ptr);
			unsigned nPixels = cache.nWidth * cache.nHeight;
			png_bytep *pRows = (png_bytep *)malloc(cache.nHeight * sizeof(png_bytep) + nPixels);
			if (pRows == NULL) {
				longjmp(png_jmpbuf(png_ptr), 1);
			}
			png_bytep *pRow = pRows;
			png_byte *pData = (png_byte *)(pRows + cache.nHeight);
			for (unsigned i = 0; i < cache.nHeight; ++i) {
				*pRow++ = pData + cache.nWidth * i;
			}
			//Generate bitmap
			//float nIntensityScale = 255.0f / (cache.nMaxIntensity / 5.0f);
			float nIntensityScale = 1.0f / cache.nMaxIntensity;
			float *pImgPtr = cache.pImage;
			float nVal;
			for (unsigned i = 0; i < nPixels; ++i) {
				//nPosX = (unsigned)(*pImgPtr++ * nIntensityScale + 0.5f);
				//*pData++ = nPosX > 255 ? 0 : 255 - (png_byte)nPosX;
				nVal = pow(*pImgPtr++ * nIntensityScale, nDistortion);
				*pData++ = nVal >= 1.0f ? 0 : (png_byte)((1.0f - nVal) * 255.0f + 0.5f);
			}
			png_write_image(png_ptr, pRows);
			png_write_end(png_ptr, NULL);
			free(pRows);
		}
	}
	return pStream;
}

inline void AddCache(const char *szId, MS1Plot::Cache &cache) {
	DWORD nMin = (DWORD)-1;
	DWORD nMinIdx = 0;
	for (DWORD i = 0; i < CACHE_MAX; ++i) {
		if (gs_cache[i].ID == NULL) {
			nMinIdx = 0;
			break;
		} else if (gs_cache[i].TimeStamp < nMin) {
			nMin = gs_cache[i].TimeStamp;
			nMinIdx = i;
		}
	}
	ImageCache *pCache = &gs_cache[nMinIdx];
	pCache->TimeStamp = gs_nTimeStamp++;
	strncpy(pCache->ID, szId, 15);
	pCache->ID[15] = 0;
	if (pCache->Image.pImage != NULL) {
		free(pCache->Image.pImage);
	}
	memcpy(&pCache->Image, &cache, sizeof(MS1Plot::Cache));
}

inline MemoryStream *RenderCachedImage(const char *szId, float nDistortion) {
	for (DWORD i = 0; i < CACHE_MAX; ++i) {
		if (gs_cache[i].ID == NULL) {
			break;
		} else if (strcmp(szId, gs_cache[i].ID) == 0) {
			gs_cache[i].TimeStamp = gs_nTimeStamp++;
			return RenderFromCache(gs_cache[i].Image, nDistortion);
		}
	}
	return NULL;
}

MemoryStream *MS1Plot::RenderFromFile(const char *szFileName, unsigned nWidth, unsigned nHeight, float nDistortion, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	MemoryStream *pCache = RenderCachedImage(szFileName, nDistortion);
	if (pCache != NULL) {
		return pCache;
	}
	FILE *pFile = fopen(szFileName, "rb");
	if (pFile != NULL) {
		struct Info {
			DWORD offset;
			DWORD size;
			DWORD count;
			float maxInt;
			float minTime, maxTime;
			float minMz, maxMz;
		};
		Info info;
		if (fread(&info, 1, sizeof(Info), pFile) != sizeof(Info)) {
			fclose(pFile);
			return NULL;
		}
		fseek(pFile, info.offset, SEEK_SET);
		char *pSrcData = (char *)malloc(info.size);
		if (fread(pSrcData, 1, info.size, pFile) != info.size) {
			fclose(pFile);
			return NULL;
		}
		fclose(pFile);
		return RenderFromFileInternal(szFileName, pSrcData, info.count, nWidth, nHeight, nDistortion, info.maxInt, nMinTime >= 0 ? nMinTime : info.minTime, nMaxTime >= 0 ? nMaxTime : info.maxTime, nMinMz >= 0 ? nMinMz : info.minMz, nMaxMz >= 0 ? nMaxMz : info.maxMz);
	}
	return NULL;
}

inline MemoryStream *MS1Plot::RenderFromFileInternal(const char *szFileName, char *pSrcData, uint32_t nScans, unsigned nWidth, unsigned nHeight, float nDistortion, float nMaxIntensity, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	unsigned nPixels = nWidth * nHeight;
	float *pImg = (float *)malloc(nPixels * sizeof(float));
	if (pImg == NULL) {
		return NULL;
	}
	float nScaleX = (nWidth - 1) / (nMaxTime - nMinTime);
	float nScaleY = (nHeight - 1) / (nMaxMz - nMinMz);
	unsigned nPosX, nPosY;
	float nVal, nIntensity, nFactorX, nFactorY;
	float nMax = nMaxIntensity;
	unsigned nIdx;
	char *pSrcDataPtr = pSrcData;
	for (uint32_t i = 0; i < nScans; ++i) {
		Scan *pScan = (Scan *)pSrcDataPtr;
		if (pScan->nStartTime >= nMinTime && pScan->nStartTime <= nMaxTime) {
			nVal = (pScan->nStartTime - nMinTime) * nScaleX;
			nFactorX = nVal - floor(nVal);
			nPosX = (unsigned)nVal;
			for (unsigned j = 0; j < pScan->nPoints; ++j) {
				const ScanPoint<float> &point = pScan->pPoints[j];
				nVal = (nMaxMz - point.mz) * nScaleY;
				nIntensity = point.intensity;
				nFactorY = nVal - floor(nVal);
				nPosY = (unsigned)nVal;
				nIdx = nPosY * nWidth + nPosX;
				UPDATE_VAL(nIntensity * (1.0f - nFactorX) * (1.0f - nFactorY));
				if (nPosX + 1 < nWidth) {
					++nIdx;
					UPDATE_VAL(nIntensity * nFactorX * (1.0f - nFactorY));
					if (nPosY + 1 < nHeight) {
						nIdx += nWidth;
						UPDATE_VAL(nIntensity * nFactorX * nFactorY);
						--nIdx;
						goto MS1DoX1Y2;
					}
				} else if (nPosY + 1 < nHeight) {
					nIdx += nWidth;
MS1DoX1Y2:
					UPDATE_VAL(nIntensity * (1.0f - nFactorX) * nFactorY);
				}
			}
		}
		pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
	}
	free(pSrcData);
	MS1Plot::Cache cache = { nWidth, nHeight, nMax, pImg };
	AddCache(szFileName, cache);
	return RenderFromCache(cache, nDistortion);
}

//MS2
MemoryStream *MS2Plot::RenderFromFile(const char *szFileName, unsigned nWidth, unsigned nHeight, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	FILE *pFile = fopen(szFileName, "rb");
	if (pFile != NULL) {
		fseek(pFile, 3 * sizeof(DWORD) + sizeof(float), SEEK_SET);
		struct Info {
			float minTime, maxTime;
			float minMz, maxMz;
		};
		Info info;
		if (fread(&info, 1, sizeof(Info), pFile) != sizeof(Info)) {
			fclose(pFile);
			return NULL;
		}
		//fseek(pFile, 3 * sizeof(DWORD) + 5 * sizeof(float));
		/*char *pSrcData = (char *)malloc(info.size);
		if (fread(pSrcData, 1, info.size, pFile) != info.size) {
			fclose(pFile);
			return NULL;
		}
		fclose(pFile);
		return RenderFromFileInternal(pSrcData, info.count, nWidth, nHeight, nDistortion, nMinTime >= 0 ? nMinTime : info.minTime, nMaxTime >= 0 ? nMaxTime : info.maxTime, nMinMz >= 0 ? nMinMz : info.minMz, nMaxMz >= 0 ? nMaxMz : info.maxMz);*/
	}
	return NULL;
}

inline MemoryStream *MS2Plot::RenderFromFileInternal(char *pSrcData, uint32_t nScans, unsigned nWidth, unsigned nHeight, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	return NULL;
	/*unsigned nPixels = nWidth * nHeight;
	float *pImg = (float *)malloc(nPixels * sizeof(float));
	if (pImg == NULL) {
		return NULL;
	}
	float nScaleX = (nWidth - 1) / (nMaxTime - nMinTime);
	float nScaleY = (nHeight - 1) / (nMaxMz - nMinMz);
	unsigned nPosX, nPosY;
	float nVal, nFactorX, nFactorY;
	unsigned nIdx;
	char *pSrcDataPtr = pSrcData;
	for (uint32_t i = 0; i < nScans; ++i) {
		Scan *pScan = (Scan *)pSrcDataPtr;
		if (pScan->nStartTime >= nMinTime && pScan->nStartTime <= nMaxTime) {
			nVal = (pScan->nStartTime - nMinTime) * nScaleX;
			nFactorX = nVal - floor(nVal);
			nPosX = (unsigned)nVal;
			for (unsigned j = 0; j < pScan->nPoints; ++j) {
				const ScanPoint<float> &point = pScan->pPoints[j];
				nVal = (nMaxMz - point.mz) * nScaleY;
				nFactorY = nVal - floor(nVal);
				nPosY = (unsigned)nVal;
				nIdx = nPosY * nWidth + nPosX;
				pImg[nIdx] = (1.0f - nFactorX) * (1.0f - nFactorY);
				if (nPosX + 1 < nWidth) {
					++nIdx;
					pImg[nIdx] =  nFactorX * (1.0f - nFactorY);
					if (nPosY + 1 < nHeight) {
						nIdx += nWidth;
						pImg[nIdx] = nFactorX * nFactorY;
						--nIdx;
						goto MS2DoX1Y2;
					}
				} else if (nPosY + 1 < nHeight) {
					nIdx += nWidth;
MS2DoX1Y2:
					pImg[nIdx] = (1.0f - nFactorX) * nFactorY;
				}
			}
		}
		pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
	}
	free(pSrcData);
	MemoryStream *pStream = new MemoryStream();
	png_structp png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
	if (png_ptr != NULL) {
		png_infop info_ptr = NULL;
		png_bytep *pRows = NULL;
		if (setjmp(png_jmpbuf(png_ptr))) {
			puts("ERROR");
			if (pRows != NULL) {
				free(pRows);
			}
			png_destroy_write_struct(&png_ptr, &info_ptr);
			delete pStream;
			free(pImg);
			return NULL;
		}
		info_ptr = png_create_info_struct(png_ptr);
		if (info_ptr != NULL) {
			png_set_write_fn(png_ptr, pStream, &PngWriterWrite, &PngWriterFlush);
			png_set_IHDR(png_ptr, info_ptr, nWidth, nHeight, 8, PNG_COLOR_TYPE_RGB_ALPHA, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
			png_write_info(png_ptr, info_ptr);
			unsigned nPixels = nWidth * nHeight;
			png_bytep *pRows = (png_bytep *)malloc(nHeight * sizeof(png_bytep) + nPixels * sizeof(float));
			if (pRows == NULL) {
				longjmp(png_jmpbuf(png_ptr), 1);
			}
			png_bytep *pRow = pRows;
			DWORD *pData = (DWORD *)(pRows + nHeight);
			for (unsigned i = 0; i < nHeight; ++i) {
				*pRow++ = pData + nWidth * i * 4;
			}
			//Generate bitmap
			BYTE *pImgPtr = pImg;
			for (unsigned i = 0; i < nPixels; ++i) {
				*pData++ = *pImgPtr++ ? 0x00FF00FF : 0xFF00FF00;
			}
			png_write_image(png_ptr, pRows);
			png_write_end(png_ptr, NULL);
			free(pRows);
		}
	}
	free(pImg);
	return pStream;*/
}
