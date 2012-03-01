#ifndef __MS1_H__
	#define __MS1_H__
	
	#include "../common/array.h"
	#include "../common/streams.h"
	#include <float.h>

	class MS1Plot {
		public:
			template<typename T>
			struct ScanPoint {
				T mz;
				T intensity;
			};
			typedef struct {
				unsigned nWidth, nHeight;
				float nMaxIntensity;
				float *pImage;
			} Cache;

			MS1Plot() : m_nMinTime(FLT_MAX), m_nMaxTime(0.0f), m_nMinMz(FLT_MAX), m_nMaxMz(0.0f) {
			}
			
			~MS1Plot() {
				m_pScans.FreeAll();
			}
			
			DWORD GetSpectrumCount() {
				return m_pScans.GetLength();
			}
			
			float GetMzRange() {
				return m_nMaxMz - m_nMinMz;
			}
			
			float GetTimeRange() {
				return m_nMaxTime - m_nMinTime;
			}
			
			template<typename T>
			void AddScan(float nStartTime, const ScanPoint<T> *pPoints, unsigned nPoints) {
				if (nStartTime < m_nMinTime) {
					m_nMinTime = nStartTime;
				} else if (nStartTime > m_nMaxTime) {
					m_nMaxTime = nStartTime;
				}
				Scan *pScan = (Scan *)malloc(sizeof(Scan) + nPoints * sizeof(ScanPoint<float>));
				pScan->nStartTime = nStartTime;
				pScan->nPoints = nPoints;
				ScanPoint<float> *pDest = pScan->pPoints;
				const ScanPoint<T> *pSrc = pPoints;
				float n;
				while (nPoints--) {
					n = (float)pSrc->mz;
					if (n < m_nMinMz) {
						m_nMinMz = n;
					}
					if (n > m_nMaxMz) {
						m_nMaxMz = n;
					}
					pDest->mz = n;
					pDest->intensity = (float)pSrc->intensity;
					++pDest;
					++pSrc;
				}
				m_pScans.Push(pScan);
			}
			
			template<typename T>
			void AddScan(float nStartTime, const T *pMzPoints, const T *pIntensityPoints, unsigned nPoints) {
				if (nStartTime < m_nMinTime) {
					m_nMinTime = nStartTime;
				} else if (nStartTime > m_nMaxTime) {
					m_nMaxTime = nStartTime;
				}
				Scan *pScan = (Scan *)malloc(sizeof(Scan) + nPoints * sizeof(ScanPoint<float>));
				pScan->nStartTime = nStartTime;
				pScan->nPoints = nPoints;
				ScanPoint<float> *pDest = pScan->pPoints;
				const T *pSrcMz = pMzPoints;
				const T *pSrcIntensity = pIntensityPoints;
				float n;
				while (nPoints--) {
					n = (float)*pSrcMz;
					if (n < m_nMinMz) {
						m_nMinMz = n;
					}
					if (n > m_nMaxMz) {
						m_nMaxMz = n;
					}
					pDest->mz = n;
					pDest->intensity = (float)*pSrcIntensity;
					++pDest;
					++pSrcMz;
					++pSrcIntensity;
				}
				m_pScans.Push(pScan);
			}
			//These read the format as written by the XML parser
			static MemoryStream *RenderFromFileSmooth(const char *szFileName, DWORD nWidth, DWORD nHeight, float nContrast = 0.5f, float nMinTime = -1.0f, float nMaxTime = -1.0f, float nMinMz = -1.0f, float nMaxMz = -1.0f);
			static MemoryStream *RenderFromFilePoints(const char *szFileName, DWORD nWidth, DWORD nHeight, float nContrast = 0.5f, float nMinTime = -1.0f, float nMaxTime = -1.0f, float nMinMz = -1.0f, float nMaxMz = -1.0f);
			
		private:
			static MemoryStream *RenderFromFileInternalPixels(const char *szFileName, char *pSrcData, char nCacheCode, uint32_t nScans, DWORD nWidth, DWORD nHeight, float nContrast, float nMaxIntensity, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz);
			static MemoryStream *RenderFromFileInternalPoints(const char *szFileName, char *pSrcData, int32_t nScans, int32_t nWidth, int32_t nHeight, float nContrast, float nMaxIntensity, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz, int nRadius);

		private:
			typedef struct {
				DWORD nPoints;
				float nStartTime;
				ScanPoint<float> pPoints[0]; //[nPoints]
			} Scan;
			PointerArray<Scan*> m_pScans;
			float m_nMinTime;
			float m_nMaxTime;
			float m_nMinMz;
			float m_nMaxMz;
	};

	class MS2Plot {
		public:
			//These read the format as written by the XML parser
			static MemoryStream *RenderFromFile(const char *szFileName, DWORD nWidth, DWORD nHeight, float nMinTime = -1.0f, float nMaxTime = -1.0f, float nMinMz = -1.0f, float nMaxMz = -1.0f);
			
		private:
			static MemoryStream *RenderFromFileInternal(char *pSrcData, uint32_t nScans, DWORD nWidth, DWORD nHeight, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz);
	};
	
	void InitaliseMS1Cache(); //Must be called before doing any rendering
	void ClearMS1Cache();

#endif
