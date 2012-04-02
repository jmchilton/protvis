#ifndef __HANDLERS_H__
	#define __HANDLERS_H__

	#include "../common/handlers.h"
	#include "../common/search.h"
	#include <string.h>
	#include "msplot.h"
	
	struct _State;
	
	#define LIST_TYPE(name, type, tag) \
		class name : public TagHandler { \
			TAG_HANDLER(name, m_nCount(0)) { \
				TRACEPOS(m_pStream, #type "List.__init__(): "); \
				m_offStartPos = m_pStream->Tell(); \
				WRITE_STRUCTURE(m_pStream, 1, (DWORD), (0)); \
				return true; \
			} \
			virtual void End() { \
				off_t offEndPos = m_pStream->Tell(); \
				m_pStream->Seek(m_offStartPos); \
				WRITE_STRUCTURE(m_pStream, 1, (DWORD), (m_nCount)); \
				m_pStream->Seek(offEndPos); \
			} \
			virtual OutputStream *BeginChild(DWORD nIndex) { \
				if (nIndex == 0) { /*tag*/ \
					++m_nCount; \
					return m_pStream; \
				} \
				return TagHandler::BeginChild(nIndex - 1); \
			} \
			static void Search(FILE *f, SearchStatus &stat) { \
				READ_STRUCTURE(f, Info, 1, (DWORD)); \
				type::SearchAll(f, stat, Info._0); \
			} \
			static void SearchAll(FILE *f, SearchStatus &stat, DWORD nCount) { \
				for (DWORD i = 0; i < nCount; ++i) { \
					READ_STRUCTURE(f, Info, 1, (DWORD)); \
					type::SearchAll(f, stat, Info._0); \
				} \
			} \
			/*static void Eat(FILE *f) { \
				READ_STRUCTURE(f, Info, 1, (DWORD)); \
				type::EatAll(f, Info._0); \
			}
			static void EatAll(FILE *f, DWORD nCount) { \
				for (DWORD i = 0; i < nCount; ++i) { \
					READ_STRUCTURE(f, Info, 1, (DWORD)); \
					type::EatAll(f, Info._0); \
				} \
			}*/ \
			private: \
				off_t m_offStartPos; \
				DWORD m_nCount; \
		};
	#define PARAM_GROUP_CHILDREN(cls, ...) TAG_HANDLER_CHILDREN(cls, __VA_ARGS__, { "cvParam", &CVParam::New })
	#define PARAM_EMPTY_CHILDREN(cls, ...) TAG_HANDLER_CHILDREN(cls, { "cvParam", &CVParam::New })

	#define ACC_MS_SCAN_START		1000016
	#define ACC_MS_SPECTRUM_LEVEL	1000511
	#define ACC_MS_DATA_MZ			1000514
	#define ACC_MS_DATA_INTENSITY	1000515
	#define ACC_MS_FLOAT_32			1000521
	#define ACC_MS_FLOAT_64			1000523
	#define ACC_MS_PRECURSOR_MZ		1000744
	#define ACC_MS_COMPRESSED_ZLIB	1000574
	#define ACC_MS_SPECTRUM_MS1		1000579
	#define ACC_MS_SPECTRUM_MSN		1000580
	#define ACC_UO_SECOND			0000010
	#define ACC_UO_MINUTE			0000031        
	#define ACC_UO_HOUR				0000032
	
	#define ACC_REF_NAME(a,b,c,d) ((a) | ((b) << 8) | ((c) << 16) | ((d) << 24))
	#define ACC_REF_MS	ACC_REF_NAME('M', 'S', 0, 0)
	#define ACC_REF_UO	ACC_REF_NAME('U', 'O', 0, 0)

	typedef struct {
		DWORD nAccession;
		DWORD nUnitAccession;
		DWORD nCvRef; //This is the numeric representation of the first 4 characters
		DWORD nUnitCvRef; //This is the numeric representation of the first 4 characters
		char szValue[24]; //If the value is larger than this buffer, we dont care about it, or its truncated characters
	} CVParamData;

	class CVParam : public TagHandler {
		//Takes MemoryStream as array of CVParamData's
		TAG_HANDLER(CVParam);
	};

	class ParamGroup : public TagHandler {
		TAG_HANDLER(ParamGroup, m_pCvParam(NULL));
		virtual OutputStream *BeginChild(DWORD nIndex);
		virtual void End();
		void EndChild();
		CVParamData *GetParams();
		DWORD GetParamsCount();
		static void Eat(FILE *f); //Not used, but needed for LIST_TYPE macro
		static void EatAll(FILE *f, DWORD nCount); //Not used, but needed for LIST_TYPE macro
		static void Search(FILE *f, SearchStatus &stat); //Not used, but needed for LIST_TYPE macro
		static void SearchAll(FILE *f, SearchStatus &stat, DWORD nCount); //Not used, but needed for LIST_TYPE macro
		
		private:
			MemoryStream *m_pCvParam;
	};
	
	class ScanWindowList : public TagHandler {
		TAG_HANDLER(ScanWindowList, m_nCount(0));
		virtual void End();
		virtual OutputStream *BeginChild(DWORD nIndex);

		private:
			off_t m_offStartPos;
			DWORD m_nCount;
	};
	
	class SelectedIon : public ParamGroup {
		//This element is not written to file directly
		X_HANDLER(SelectedIon, ParamGroup);
		virtual void End();
	};
	
	class SelectedIonList : public TagHandler {
		//This element is not written to file directly
		TAG_HANDLER(SelectedIonList);
		virtual OutputStream *BeginChild(DWORD nIndex);
	};

	class Precursor : public TagHandler {
		//This element is not written to file directly
		TAG_HANDLER(Precursor);
		virtual OutputStream *BeginChild(DWORD nIndex);
	};

	class PrecursorList : public TagHandler {
		//This element is not written to file directly
		TAG_HANDLER(PrecursorList);
		virtual OutputStream *BeginChild(DWORD nIndex);
	};
	
	class Spectrum;
	class BinaryDataArray;
	class Binary : public TagHandler {
		//This element is not written to file directly
		TAG_HANDLER(Binary);
		virtual void End();
		virtual void RawData(const char *szData, int nLength);
		
		private:
			BinaryDataArray *m_pDataArray;
			MemoryStream m_buffer;
	};

	class BinaryDataArrayList;
	class BinaryDataArray : public ParamGroup {
		//This element is not written to file directly
		X_HANDLER(BinaryDataArray, ParamGroup, m_pBinary(NULL));
		virtual void End();
		virtual OutputStream *BeginChild(DWORD nIndex);

		private:
			Spectrum *m_pSpectrum;
			MemoryStream *m_pBinary;
	};
	
	class BinaryDataArrayList : public TagHandler {
		//This element is not written to file directly
		TAG_HANDLER(BinaryDataArrayList);
		virtual OutputStream *BeginChild(DWORD nIndex);

		friend class BinaryDataArray;
	};

	class ScanList;
	class Scan : public ParamGroup {
		//This element is not written to file directly
		X_HANDLER(Scan, ParamGroup);
		virtual void End();
		virtual OutputStream *BeginChild(DWORD nIndex);
		
		private:
			Spectrum *m_pSpectrum;
	};

	class ScanList : public ParamGroup {
		//This element is not written to file directly
		X_HANDLER(ScanList, ParamGroup);
		virtual OutputStream *BeginChild(DWORD nIndex);
	};

	class Run;
	class MzML;
	class Spectrum : public ParamGroup {
		/*struct Ion {
			float mz;
			float intensity;
		}
		//ONLY IF (m_nMsLevel > 1)
		struct Spectrum {
			DWORD ion__count;
			DWORD precursor__count;
			DWORD scan;
			float scan_start_time; //negative number if not specified
			float precursor_mz; //negative number if not specified
			Ion ions[ion__count];
			float precursor_mz[precursor__count];
		}*/
		X_HANDLER(Spectrum, ParamGroup, m_nMsLevel(0), m_nIndex((DWORD)-1), m_nStartTime(-1.0f), m_pPrecursorList(NULL), m_pMz(NULL), m_pIntensity(NULL));
		virtual void End();
		virtual OutputStream *BeginChild(DWORD nIndex);
		void SetStartTime(float nTime);
		static void EatAll(FILE *pFile, DWORD nCount);
		static void SearchAll(FILE *f, SearchStatus &stat, DWORD nCount);
		static PyObject *GetInfo(FILE *pFile); //Assumes the file is pointing to the correct place
		static PyObject *PointsMS2All(FILE *pFile, DWORD nCount);
		static PyObject *PointsMS2ChunksAll(FILE *pFile, DWORD nChunks, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz, DWORD nCount);
		
		private:
			off_t m_offStartPos;
			DWORD m_nMsLevel;
			DWORD m_nIndex;
			float m_nStartTime;
			MemoryStream *m_pPrecursorList;
			MemoryStream *m_pMz;
			MemoryStream *m_pIntensity;
			MzML *m_pMzML;
			Run *m_pRun;

		friend class BinaryDataArray;
	};
	
	class SpectrumList : public TagHandler {
		/*struct SpectrumList {
			Spectrum spectrum;
		}*/
		TAG_HANDLER(SpectrumList);
		virtual OutputStream *BeginChild(DWORD nIndex);
	};

	class Run : public ParamGroup {
		/*struct Index {
			DWORD scanId;
			DWORD spectrum__offset;
		}
		struct Run {
			DWORD spectrumList__count;
			DWORD index__offset;
			//DWORD chromatogramList__count;
			SpectrumList spectrumList[spectrumList__count];
			//ChromatogramList chromatogramList[chromatogramList__count];
			Index index[spectrumList__count]; // <--index__offset
		}*/
		X_HANDLER(Run, ParamGroup, m_arrSpectrums(256));
		virtual void End();
		virtual OutputStream *BeginChild(DWORD nIndex);
		void AddSpectrumN(DWORD nIndex);
		static void Search(FILE *pFile, SearchStatus &stat);
		static PyObject *GetSpectrum(FILE *pFile, DWORD nScan);
		static DWORD GetSpectrumOffset(FILE *pFile, DWORD nScan);
		static PyObject *PointsMS2(FILE *pFile);
		static PyObject *PointsMS2Chunks(FILE *pFile, DWORD nChunks, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz);

		private:
			typedef struct _Index {
				DWORD scanId;
				DWORD spectrum__offset;
				
				_Index(DWORD scan, DWORD offset) : scanId(scan), spectrum__offset(offset) { }
			} Index;
			
			LiteralArray<Index> m_arrSpectrums;
			off_t m_offStartPos;
			//DWORD m_nChromatogramLists;
			//MemoryStream *m_pChromatogramLists;
			friend class Spectrum; //FIXME: Debug
	};

	class MzML : public TagHandler {
		/*struct MS1Spectrum {
			DWORD ion__count;
			float startTime;
			Spectrum::Ion ions[ion__count];
		}
		struct MzML {
			//CVList cvList;
			//FileDescription fileDescription;
			//ReferenceableParamGroupList referenceableParamGroupList; //ONLY IF (OptionalFlags & 0x01)
			//SampleList sampleList; //ONLY IF (OptionalFlags & 0x02)
			//SoftwareList softwareList;
			//ScanSettingsList scanSettingsList; //ONLY IF (OptionalFlags & 0x04)
			//InstrumentConfigurationList instrumentConfigurationList;
			//DataProcessingList dataProcessingList;
			DWORD run__offset;
			DWORD ms1__offset;
			DWORD ms1__size;
			DWORD ms1__count;
			float ms1_maxIntensity;
			float ms1_minTime;
			float ms1_maxTime;
			float ms1_minMz;
			float ms1_maxMz;
			String spectrum_name;
			Run run;
			MS1Spectrum ms1spectrum[ms1spectrum__count]; // <--ms1__offset, sorted lowest to highest retention time
		}*/
		TAG_HANDLER(MzML, m_arrMS1Data(512));
		virtual void End();
		virtual OutputStream *BeginChild(DWORD nIndex);
		void AddSpectrum1(float nStartTime, DWORD nCount, float *pMz, float *pIntensity);
		static PyObject *GetSpectrum(FILE *pFile, const char *szSpectrumName);
		static DWORD GetSpectrumOffset(FILE *pFile, const char *szSpectrumName);
		static void SearchSpectrums(FILE *pFile, SearchStatus &stat);
		static void Info(FILE *pFile, float &nMinTime, float &nMaxTime, float &nMinMz, float &nMaxMz, float &nMaxIntensity, char *&szName); //MUST call free() on szName
		static PyObject *PointsMS2(FILE *pFile);
		static PyObject *PointsMS2Chunks(FILE *pFile, DWORD nChunks);
		static void SkipHeaders(FILE *pFile);

		private:
			typedef struct _MS1Data {
				float nScanTime;
				DWORD nCount;
				float *pMz;
				float *pIntensity;
				
				_MS1Data(float time, DWORD count, float *mz, float *intensity) : nScanTime(time), nCount(count), pMz(mz), pIntensity(intensity) { }
			} MS1Data;
			
			LiteralArray<MS1Data> m_arrMS1Data;
			off_t m_offRun;
	};
	
	class IndexedMzML : public TagHandler {
		/*struct IndexedMzML {
			MzML mzml;
		}*/
		TAG_HANDLER(IndexedMzML);
		virtual OutputStream *BeginChild(DWORD nIndex);
	};
	
	UNUSED_HANDLERS(PrecursorIonList);
	
	typedef struct _State : public BaseState {
		_State(const char *szFilePath, const char *szOriginalFile);
		MzML *pMzML;
		Run *pRun;
		Spectrum *pSpectrum;
		const char *szFileName;
	} State;
	
	#include "handlers.inl"

#endif
