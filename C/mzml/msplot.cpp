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
	((MemoryStream *)png_get_io_ptr(png_ptr))->Write(data, length);
}

static void PngWriterFlush(png_structp png_ptr) {
}

inline float abs(float x) {
	return x >= 0 ? x : -x;
}

//MS1
//FIXME: Make caching threadsafe

#define CACHE_MAX 10
typedef struct {
	char ID[15];
	char Code;
	DWORD Width, Height;
	float MinTime, MaxTime, MinMz, MaxMz;
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

MemoryStream *BlankImage() {
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
			png_set_IHDR(png_ptr, info_ptr, 1, 1, 8, PNG_COLOR_TYPE_GRAY_ALPHA, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
			png_write_info(png_ptr, info_ptr);
			png_bytep pRows[1 + 1];
			*pRows = (png_bytep)pRows + 1; //Assign the row
			*((WORD *)(pRows + 1)) = 0; //Draw the pixel
			png_write_image(png_ptr, pRows);
			png_write_end(png_ptr, NULL);
		}
	}
	return pStream;
}

static MemoryStream *RenderFromCache(MS1Plot::Cache &cache, float nContrast) {
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
			png_set_IHDR(png_ptr, info_ptr, cache.nWidth, cache.nHeight, 8, PNG_COLOR_TYPE_GRAY_ALPHA, PNG_INTERLACE_NONE, PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
			png_write_info(png_ptr, info_ptr);
			unsigned nPixels = cache.nWidth * cache.nHeight;
			png_bytep *pRows = (png_bytep *)malloc(cache.nHeight * sizeof(png_bytep) + nPixels * 2);
			if (pRows == NULL) {
				longjmp(png_jmpbuf(png_ptr), 1);
			}
			png_bytep *pRow = pRows;
			png_byte *pData = (png_byte *)(pRows + cache.nHeight);
			for (unsigned i = 0; i < cache.nHeight; ++i) {
				*pRow++ = pData + cache.nWidth * i * 2;
			}
			//Generate bitmap
			float nIntensityScale = 1.0f / cache.nMaxIntensity;
			float *pImgPtr = cache.pImage;
			float nVal;
			for (unsigned i = 0; i < nPixels; ++i) {
				nVal = pow(*pImgPtr++ * nIntensityScale, nContrast);
				pData[0] = 0;
				pData[1] = nVal >= 1.0f ? 255 : (png_byte)(nVal * 255.0f + 0.5f);
				pData += 2;
			}
			png_write_image(png_ptr, pRows);
			png_write_end(png_ptr, NULL);
			free(pRows);
		}
	}
	return pStream;
}

inline void AddCache(const char *szId, DWORD nCode, DWORD nWidth, DWORD nHeight, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz, MS1Plot::Cache &cache) {
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
	strncpy(pCache->ID, szId, 14);
	pCache->ID[14] = 0;
	pCache->Code = nCode;
	pCache->Width = nWidth;
	pCache->Height = nHeight;
	pCache->MinTime = nMinTime;
	pCache->MaxTime = nMaxTime;
	pCache->MinMz = nMinMz;
	pCache->MaxMz = nMaxMz;
	if (pCache->Image.pImage != NULL) {
		free(pCache->Image.pImage);
	}
	memcpy(&pCache->Image, &cache, sizeof(MS1Plot::Cache));
}

MemoryStream *MS1Plot::RenderFromFileSmooth(const char *szFileName, DWORD nWidth, DWORD nHeight, float nContrast, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	//Try the cache first
	for (DWORD i = 0; i < CACHE_MAX; ++i) {
		ImageCache &c = gs_cache[i];
		if (c.ID == NULL) {
			break;
		} else if (strncmp(szFileName, c.ID, 14) == 0 && c.Code == 0 && c.Width == nWidth && c.Height == nHeight && c.MinTime == nMinTime && c.MaxTime == nMaxTime && c.MinMz == nMinMz && c.MaxMz == nMaxMz) {
			c.TimeStamp = gs_nTimeStamp++;
			return RenderFromCache(c.Image, nContrast);
		}
	}
	//Not in cache, load it up
	FILE *pFile = fopen(szFileName, "rb");
	if (pFile != NULL) {
		struct Info {
			DWORD run__offset;
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
		if ((nMinTime < 0 || abs(nMinTime - info.minTime) < 0.001) && (nMaxTime < 0 || abs(nMaxTime - info.maxTime) < 0.001)) {
			if (nWidth > info.count) {
				nWidth = info.count;
			}
		} else {
			char *pSrcDataPtr = pSrcData;
			unsigned nScans = 0;
			for (uint32_t i = 0; i < info.count; ++i) {
				Scan *pScan = (Scan *)pSrcDataPtr;
				if (pScan->nStartTime >= nMinTime && pScan->nStartTime <= nMaxTime) {
					++nScans;
				}
				pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
			}
			if (nWidth > nScans) {
				nWidth = nScans;
			}
		}
		if (nHeight == (DWORD)-1) {
			nHeight = (DWORD)(info.maxMz - info.minMz + 0.5f);
			while (nHeight > 512) {
				nHeight >>= 1;
			}
		}
		if (nMinTime < 0) {
			nMinTime = info.minTime;
		}
		if (nMaxTime < 0) {
			nMaxTime = info.maxTime;
		}
		if (nMinMz < 0) {
			nMinMz = info.minMz;
		}
		if (nMaxMz < 0) {
			nMaxMz = info.maxMz;
		}
		if (nMinTime > nMaxTime || nMinMz > nMaxMz || nContrast <= 0.0f || nWidth == 0) {
			return BlankImage();
		}
		if (nContrast <= 0.0f) {
			nContrast = 0.001f;
		} else if (nContrast > 1.0f) {
			nContrast = 1.0f;
		}
		return RenderFromFileInternalPixels(szFileName, pSrcData, 0, info.count, nWidth, nHeight, nContrast, info.maxInt, nMinTime, nMaxTime, nMinMz, nMaxMz);
	}
	return NULL;
}

MemoryStream *MS1Plot::RenderFromFilePoints(const char *szFileName, DWORD nWidth, DWORD nHeight, float nContrast, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	//Try the cache first
	for (DWORD i = 0; i < CACHE_MAX; ++i) {
		ImageCache &c = gs_cache[i];
		if (c.ID == NULL) {
			break;
		} else if (strncmp(szFileName, c.ID, 14) == 0 && c.Code == 1 && c.Width == nWidth && c.Height == nHeight && c.MinTime == nMinTime && c.MaxTime == nMaxTime && c.MinMz == nMinMz && c.MaxMz == nMaxMz) {
			c.TimeStamp = gs_nTimeStamp++;
			return RenderFromCache(c.Image, nContrast);
		}
	}
	//Not in cache, load it up
	FILE *pFile = fopen(szFileName, "rb");
	if (pFile != NULL) {
		struct Info {
			DWORD run__offset;
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
		DWORD nScans = 0, nMaxPeaks = 0, nPoints;
		if ((nMinTime < 0 || abs(nMinTime - info.minTime) < 0.001) && (nMaxTime < 0 || abs(nMaxTime - info.maxTime) < 0.001)) {
			nScans = info.count;
			char *pSrcDataPtr = pSrcData;
			if ((nMinMz < 0 || abs(nMinMz - info.minMz) < 0.001) && (nMaxMz < 0 || abs(nMaxMz - info.maxMz) < 0.001)) {
				for (uint32_t i = 0; i < info.count; ++i) {
					Scan *pScan = (Scan *)pSrcDataPtr;
					++nScans;
					if (pScan->nPoints > nMaxPeaks) {
						nMaxPeaks = pScan->nPoints;
					}
					pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
				}
			} else {
				nPoints = 0;
				for (uint32_t i = 0; i < info.count; ++i) {
					Scan *pScan = (Scan *)pSrcDataPtr;
					++nScans;
					nPoints = 0;
					
					for (uint32_t j = 0; j < pScan->nPoints; ++j) {
						if (pScan->pPoints[j].mz >= nMinMz && pScan->pPoints[j].mz <= nMaxMz) {
							++nPoints;
						}
					}
					if (nPoints > nMaxPeaks) {
						nMaxPeaks = nPoints;
					}
					pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
				}
			}
		} else {
			char *pSrcDataPtr = pSrcData;
			if ((nMinMz < 0 || abs(nMinMz - info.minMz) < 0.001) && (nMaxMz < 0 || abs(nMaxMz - info.maxMz) < 0.001)) {
				for (uint32_t i = 0; i < info.count; ++i) {
					Scan *pScan = (Scan *)pSrcDataPtr;
					if (pScan->nStartTime >= nMinTime && pScan->nStartTime <= nMaxTime) {
						++nScans;
						if (pScan->nPoints > nMaxPeaks) {
							nMaxPeaks = pScan->nPoints;
						}
					}
					pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
				}
			} else {
				for (uint32_t i = 0; i < info.count; ++i) {
					Scan *pScan = (Scan *)pSrcDataPtr;
					if (pScan->nStartTime >= nMinTime && pScan->nStartTime <= nMaxTime) {
						++nScans;
						nPoints = 0;
						for (uint32_t j = 0; j < pScan->nPoints; ++j) {
							if (pScan->pPoints[j].mz >= nMinMz && pScan->pPoints[j].mz <= nMaxMz) {
								++nPoints;
							}
						}
						if (nPoints > nMaxPeaks) {
							nMaxPeaks = nPoints;
						}
					}
					pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
				}
			}
		}
		if (nMinTime < 0) {
			nMinTime = info.minTime;
		}
		if (nMaxTime < 0) {
			nMaxTime = info.maxTime;
		}
		if (nMinMz < 0) {
			nMinMz = info.minMz;
		}
		if (nMaxMz < 0) {
			nMaxMz = info.maxMz;
		}
		if (nScans == 0 || nMaxPeaks == 0 || nMinTime > nMaxTime || nMinMz > nMaxMz || nContrast <= 0.0f) {
			return BlankImage();
		} else {
			if (nContrast <= 0.0f) {
				nContrast = 0.001f;
			} else if (nContrast > 1.0f) {
				nContrast = 1.0f;
			}
			unsigned nRadiusX = nWidth / (nScans * 2);
			unsigned nRadiusY = nHeight / (nMaxPeaks * 2);
			if (nRadiusX > 1 && nRadiusY > 1) {
				return RenderFromFileInternalPoints(szFileName, pSrcData, info.count, nWidth, nHeight, nContrast, info.maxInt, nMinTime, nMaxTime, nMinMz, nMaxMz, nRadiusX < nRadiusY ? nRadiusX : nRadiusY);
			} else {
				return RenderFromFileInternalPixels(szFileName, pSrcData, 1, info.count, nWidth, nHeight, nContrast, info.maxInt, nMinTime, nMaxTime, nMinMz, nMaxMz);
			}
		}
	}
	return NULL;
}

inline MemoryStream *MS1Plot::RenderFromFileInternalPixels(const char *szFileName, char *pSrcData, char nCacheCode, uint32_t nScans, DWORD nWidth, DWORD nHeight, float nContrast, float nMaxIntensity, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	unsigned nPixels = nWidth * nHeight;
	float *pImg = (float *)malloc(nPixels * sizeof(float));
	if (pImg == NULL) {
		return NULL;
	}
	memset(pImg, 0, nPixels * sizeof(float));
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
				if (point.mz >= nMinMz && point.mz <= nMaxMz) {
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
		}
		pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
	}
	free(pSrcData);
	MS1Plot::Cache cache = { nWidth, nHeight, nMax, pImg };
	AddCache(szFileName, nCacheCode, nWidth, nHeight, nMinTime, nMaxTime, nMinMz, nMaxMz, cache);
	return RenderFromCache(cache, nContrast);
}

inline MemoryStream *MS1Plot::RenderFromFileInternalPoints(const char *szFileName, char *pSrcData, int32_t nScans, int32_t nWidth, int32_t nHeight, float nContrast, float nMaxIntensity, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz, int nRadius) {
	unsigned nPixels = nWidth * nHeight;
	float *pImg = (float *)malloc(nPixels * sizeof(float));
	if (pImg == NULL) {
		return NULL;
	}
	memset(pImg, 0, nPixels * sizeof(float));
	float nScaleX = (nWidth - 1) / (nMaxTime - nMinTime);
	float nScaleY = (nHeight - 1) / (nMaxMz - nMinMz);
	int32_t nPosX, nPosY;
	float nVal, nIntensity;
	float nMax = nMaxIntensity;
	unsigned nIdx;
	char *pSrcDataPtr = pSrcData;
	DWORD r2 = nRadius * nRadius;
	DWORD y2;
	for (int32_t i = 0; i < nScans; ++i) {
		Scan *pScan = (Scan *)pSrcDataPtr;
		if (pScan->nStartTime >= nMinTime && pScan->nStartTime <= nMaxTime) {
			nVal = (pScan->nStartTime - nMinTime) * nScaleX;
			nPosX = (int32_t)nVal - nRadius;
			for (unsigned j = 0; j < pScan->nPoints; ++j) {
				const ScanPoint<float> &point = pScan->pPoints[j];
				if (point.mz >= nMinMz && point.mz <= nMaxMz) {
					nVal = (nMaxMz - point.mz) * nScaleY;
					nIntensity = point.intensity;
					nPosY = ((int32_t)nVal - nRadius) * nWidth;
					int x, y;
					for (y = -nRadius; y <= nRadius; ++y) {
						if (nPosY >= 0 && (unsigned)nPosY < nPixels) {
							y2 = y * y;
							nIdx = nPosY + nPosX;
							for (x = -nRadius; x <= nRadius; ++x) {
								if (nPosX + x + nRadius >= 0 && nPosX + x + nRadius < nWidth) {
									if ((x * x) + y2 <= r2) {
										UPDATE_VAL(nIntensity);
									} else if (x > 0) {
										break;
									}
								}
								++nIdx;
							}
						}
						nPosY += nWidth;
					}
				}
			}
		}
		pSrcDataPtr += sizeof(Scan) + pScan->nPoints * sizeof(ScanPoint<float>);
	}
	free(pSrcData);
	MS1Plot::Cache cache = { nWidth, nHeight, nMax, pImg };
	AddCache(szFileName, 1, nWidth, nHeight, nMinTime, nMaxTime, nMinMz, nMaxMz, cache);
	return RenderFromCache(cache, nContrast);
}

//MS2

template <typename T>
inline T min(T x, T y) {
	return x < y ? x : y;
}

template <typename T>
inline T max(T x, T y) {
	return x > y ? x : y;
}

MemoryStream *MS2Plot::RenderFromFile(const char *szFileName, DWORD nWidth, DWORD nHeight, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	FILE *pFile = fopen(szFileName, "rb");
	if (pFile != NULL) {
		struct MzMLInfo {
			DWORD run__offset;
			DWORD _1, _2, _3;
			float maxIntensity;
			float minTime, maxTime;
			float minMz, maxMz;
		};
		struct RunInfo {
			DWORD scans, indexOffset;
		};
		MzMLInfo mzml;
		RunInfo run;
		if (fread(&mzml, 1, sizeof(MzMLInfo), pFile) != sizeof(MzMLInfo)) {
			fclose(pFile);
			return NULL;
		}
		fseek(pFile, mzml.run__offset, SEEK_SET);
		if (fread(&run, 1, sizeof(RunInfo), pFile) != sizeof(RunInfo)) {
			fclose(pFile);
			return NULL;
		}
		if (run.scans == 0) {
			return BlankImage();
		}
		DWORD nDataSize = run.indexOffset - (mzml.run__offset + 2 * sizeof(DWORD));
		char *pSrcData = (char *)malloc(nDataSize);
		if (fread(pSrcData, 1, nDataSize, pFile) != nDataSize) {
			fclose(pFile);
			return NULL;
		}
		fclose(pFile);
		if (nMinTime < 0) {
			nMinTime = mzml.minTime;
		}
		if (nMaxTime < 0) {
			nMaxTime = mzml.maxTime;
		}
		if (nMinMz < 0) {
			nMinMz = mzml.minMz;
		}
		if (nMaxMz < 0) {
			nMaxMz = mzml.maxMz;
		}
		float nScaleX = (mzml.maxTime - mzml.minTime) / (nMaxTime - nMinTime);
		float nScaleY = (mzml.maxMz - mzml.minMz) / (nMaxMz - nMinMz);
		int nScale = (DWORD)min(max(1, (int)(min(nScaleX, nScaleY) / 3.0f)), 5);
		return RenderFromFileInternal(pSrcData, run.scans, nWidth, nHeight, nScale, nMinTime, nMaxTime, nMinMz, nMaxMz);
	}
	return NULL;
}

inline MemoryStream *MS2Plot::RenderFromFileInternal(char *pSrcData, uint32_t nSpectrums, DWORD nWidth, DWORD nHeight, int nScale, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	unsigned nPixels = nWidth * nHeight;
	BYTE *pImg = (BYTE *)malloc(nPixels * sizeof(BYTE));
	if (pImg == NULL) {
		return NULL;
	}
	memset(pImg, 0, nPixels * sizeof(BYTE));
	float nScaleX = (nWidth - 1) / (nMaxTime - nMinTime);
	float nScaleY = (nHeight - 1) / (nMaxMz - nMinMz);
	unsigned nPosX, nPosY;
	unsigned nIdx;
	char *pSrcDataPtr = pSrcData;
	for (uint32_t i = 0; i < nSpectrums; ++i) {
		Spectrum *pSpectrum = (Spectrum *)pSrcDataPtr;
		if (pSpectrum->precursor_mz >= 0 && pSpectrum->scan_start_time >= nMinTime && pSpectrum->scan_start_time <= nMaxTime) {
			nPosX = (unsigned)((pSpectrum->scan_start_time - nMinTime) * nScaleX) - nScale;
			nPosY = ((unsigned)((nMaxMz - pSpectrum->precursor_mz) * nScaleY) - nScale) * nWidth;
			//pImg[nPosY * nWidth + nPosX] = 0xFF;
			int x, y;
			for (y = -nScale; y <= nScale; ++y) {
				if (nPosY >= 0 && (unsigned)nPosY < nPixels) {
					nIdx = nPosY + nPosX;
					for (x = -nScale; x <= nScale; ++x) {
						if (nPosX + x + nScale >= 0 && nPosX + x + nScale < nWidth) {
							pImg[nIdx] = 0xFF;
						}
						++nIdx;
					}
				}
				nPosY += nWidth;
			}
		}
		pSrcDataPtr += sizeof(Spectrum) + pSpectrum->ion__count * (2 * sizeof(float)) + pSpectrum->precursor__count * sizeof(float);
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
				*pRow++ = (png_bytep)(pData + nWidth * i);
			}
			//Generate bitmap
			BYTE *pImgPtr = pImg;
			for (unsigned i = 0; i < nPixels; ++i) {
				*pData++ = (*pImgPtr++ << 24) | 0x0000FF;
			}
			png_write_image(png_ptr, pRows);
			png_write_end(png_ptr, NULL);
			free(pRows);
		}
	}
	free(pImg);
	return pStream;
}
