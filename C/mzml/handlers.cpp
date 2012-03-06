#include "../common/stdinc.h"
#include "../common/binary.h"
#include "handlers.h"

bool CVParam::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "CVParam::Begin(): ");
	const XML_Char *szCvRef = Attr(pszAttrs, "cvRef");
	const XML_Char *szAccession = Attr(pszAttrs, "accession");
	const XML_Char *szUnitCvRef = Attr(pszAttrs, "unitCvRef");
	const XML_Char *szUnitAccession = Attr(pszAttrs, "unitAccession");
	const XML_Char *szValue = Attr(pszAttrs, "value");
	if (szCvRef != NULL && szAccession != NULL) {
		size_t nRefLen = strlen(szCvRef);
		if (strncmp(szAccession, szCvRef, nRefLen) == 0 && szAccession[nRefLen] == ':') {
			CVParamData data = { 0 };
			strncpy((char *)&data.nCvRef, szCvRef, 4);
			data.nAccession = strtoul(szAccession + nRefLen + 1, NULL, 10);
			if (szUnitCvRef != NULL && szUnitAccession != NULL) {
				nRefLen = strlen(szUnitCvRef);
				if (strncmp(szUnitAccession, szUnitCvRef, nRefLen) == 0 && szUnitAccession[nRefLen] == ':') {
					strncpy((char *)&data.nUnitCvRef, szUnitCvRef, 4);
					data.nUnitAccession = strtoul(szUnitAccession + nRefLen + 1, NULL, 10);
				}
			}
			if (szValue != NULL) {
				strncpy(data.szValue, szValue, 23);
				data.szValue[23] = 0;
			}
			m_pStream->Write(&data, sizeof(CVParamData));
		}
	}
	return true;
}

bool ParamGroup::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ParamGroup::Begin(): ");
	return true;
}

OutputStream *ParamGroup::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //cvParam
		if (m_pCvParam == NULL) {
			m_pCvParam = new MemoryStream();
		}
		return m_pCvParam;
	}
	return NULL;
}

CVParamData *ParamGroup::GetParams() {
	return m_pCvParam == NULL ? NULL : (CVParamData *)m_pCvParam->GetBuffer();
}

DWORD ParamGroup::GetParamsCount() {
	return m_pCvParam == NULL ? 0 : m_pCvParam->GetLength() / sizeof(CVParamData);
}

bool SelectedIon::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SelectedIon::Begin(): ");
	return true;
}

void SelectedIon::End() {
	CVParamData *pParams = GetParams();
	for (DWORD i = GetParamsCount(); i > 0; --i, ++pParams) {
		if (pParams->nAccession == ACC_MS_PRECURSOR_MZ) {
			m_pStream->WriteFloat((float)strtod(pParams->szValue, NULL));
			break;
		}
	}
}

bool SelectedIonList::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SelectedIonList::Begin(): ");
	return true;
}

OutputStream *SelectedIonList::BeginChild(DWORD nIndex) {
	switch (nIndex) {
		case 0: //selectedIon
			return m_pStream;
	}
	return NULL;
}

bool Precursor::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Precursor::Begin(): ");
	return true;
}

OutputStream *Precursor::BeginChild(DWORD nIndex) {
	switch (nIndex) {
		/*case 0: //activation
			return NULL;
			
		case 1: //isolationWindow
			return NULL;*/
			
		case 2: //selectedIonList
			return m_pStream;
	}
	return NULL;
}

bool PrecursorList::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Precursor::Begin(): ");
	return true;
}

OutputStream *PrecursorList::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //precursor
		return m_pStream;
	}
	return NULL;
}

bool Binary::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Binary::Begin(): ");
	m_pDataArray = (BinaryDataArray *)pState->colPath.Peek();
	return true;
}

void Binary::End() {
	CVParamData *pParams = m_pDataArray->GetParams();
	for (DWORD i = m_pDataArray->GetParamsCount(); i > 0; --i, ++pParams) {
		if (pParams->nAccession == ACC_MS_COMPRESSED_ZLIB) {
			Base64DecodeAndInflateToStream(m_buffer.GetBuffer(), m_buffer.GetLength(), m_pStream);
			return;
		}
	}
	Base64DecodeToStream(m_buffer.GetBuffer(), m_buffer.GetLength(), m_pStream);
}

void Binary::RawData(const char *szData, int nLength) {
	m_buffer.Write(szData, nLength);
}

bool BinaryDataArray::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "BinaryDataArray::Begin(): ");
	m_pSpectrum = (Spectrum *)pState->pSpectrum;
	return true;
}

void BinaryDataArray::End() {
	CVParamData *pParams = GetParams();
	for (DWORD i = GetParamsCount(); i > 0; --i, ++pParams) {
		if (pParams->nCvRef == ACC_REF_MS) {
			switch (pParams->nAccession) {
				case ACC_MS_FLOAT_64: {
					float *pFloats = (float *)m_pBinary->GetBuffer();
					double *pDoubles = (double *)m_pBinary->GetBuffer();
					double *pEnd = (double *)((BYTE *)pDoubles + m_pBinary->GetLength());
					while (pDoubles < pEnd) {
						*pFloats++ = *pDoubles++;
					}
					m_pBinary->SetLength(m_pBinary->GetLength() / (sizeof(double) / sizeof(float)));
					break;
				}
				case ACC_MS_DATA_MZ:
					m_pSpectrum->m_pMz = m_pBinary;
					m_pBinary = NULL;
					break;
			
				case ACC_MS_DATA_INTENSITY:
					m_pSpectrum->m_pIntensity = m_pBinary;
					m_pBinary = NULL;
					break;
			}
		}
	}
	if (m_pBinary != NULL) {
		delete m_pBinary;
	}
}

OutputStream *BinaryDataArray::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //binary
		if (m_pBinary != NULL) {
			return NULL;
		}
		m_pBinary = new MemoryStream();
		return m_pBinary;
	}
	return ParamGroup::BeginChild(nIndex - 1);
}

bool BinaryDataArrayList::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "BinaryDataArrayListList::Begin(): ");
	return true;
}

OutputStream *BinaryDataArrayList::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //binaryDataArray
		return m_pStream; //This is not used, but we can't return NULL
	}
	return NULL;
}

bool Scan::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Scan::Begin(): ");
	m_pSpectrum = pState->pSpectrum;
	return true;
}

void Scan::End() {
	CVParamData *pParams = GetParams();
	for (DWORD i = GetParamsCount(); i > 0; --i, ++pParams) {
		if (pParams->nAccession == ACC_MS_SCAN_START) {
			m_pSpectrum->SetStartTime((float)strtod(pParams->szValue, NULL));
			return;
		}
	}
}

OutputStream *Scan::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //scanWindowList
		return NULL;
	}
	return ParamGroup::BeginChild(nIndex - 1);
}

bool ScanList::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ScanList::Begin(): ");
	return true;
}

OutputStream *ScanList::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //scan
		return m_pStream; //This is not used, but we can't return NULL
	}
	return NULL;
}

bool Spectrum::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Spectrum::Begin(): ");
	pState->pSpectrum = this;
	m_pMzML = pState->pMzML;
	m_pRun = pState->pRun;
	const XML_Char *pIndex = Attr(pszAttrs, "index");
	if (pIndex != NULL) {
		m_nIndex = strtoul(pIndex, NULL, 10);
	}
	return true;
}

void Spectrum::End() {
	DWORD nMsLevel = 0;
	CVParamData *pParams = GetParams();
	for (DWORD i = GetParamsCount(); i > 0; --i, ++pParams) {
		if (pParams->nCvRef == ACC_REF_MS) {
			switch (pParams->nAccession) {
				case ACC_MS_SPECTRUM_MS1:
					if (nMsLevel == 0) {
						nMsLevel = 1;
					}
					break;

				case ACC_MS_SPECTRUM_MSN:
					if (nMsLevel == 0) {
						nMsLevel = 2;
					}
					break;

				case ACC_MS_SPECTRUM_LEVEL:
					nMsLevel = strtoul(pParams->szValue, NULL, 10);
					break;
			}
		}
	}
	if (nMsLevel == 1) {
		if (m_pMz != NULL && m_pIntensity != NULL) {
			if (m_pMz->GetLength() == m_pIntensity->GetLength()) {
				if (m_nStartTime >= 0.0f) {
					m_pMzML->AddSpectrum1(m_nStartTime, m_pIntensity->GetLength() / sizeof(float), (float *)m_pMz->StealBuffer(), (float *)m_pIntensity->StealBuffer());
				}
			}
		}
	} else if (nMsLevel == 2 && m_nIndex != (DWORD)-1) {
		m_pRun->AddSpectrumN(m_nIndex);
		DWORD nIonCount = m_pMz == NULL || m_pIntensity == NULL || m_pMz->GetLength() != m_pIntensity->GetLength() ? 0 : m_pMz->GetLength() / sizeof(float);
		DWORD nPrecursorCount = m_pPrecursorList == NULL ? 0 : m_pPrecursorList->GetLength() / sizeof(float);
		if (nIonCount > 0) {
			WRITE_STRUCTURE(m_pStream, 4, (DWORD, DWORD, float, float), (nIonCount, nPrecursorCount, m_nStartTime, m_pPrecursorList == NULL ? -1.0f : *(float *)m_pPrecursorList->GetBuffer()));
			const float *pMz = (const float *)m_pMz->GetBuffer();
			const float *pInt = (const float *)m_pIntensity->GetBuffer();
			for (DWORD i = 0; i < nIonCount; ++i) {
				WRITE_STRUCTURE(m_pStream, 2, (float, float), (pMz[i], pInt[i]));
			}
			if (m_pPrecursorList != NULL) {
				m_pStream->WriteStream(m_pPrecursorList);
			}
		} else {
			WRITE_STRUCTURE(m_pStream, 4, (DWORD, DWORD, float, float), (0, 0, 0.0f, 0.0f));
		}
	}
	if (m_pMz != NULL) {
		delete m_pMz;
	}
	if (m_pIntensity != NULL) {
		delete m_pIntensity;
	}
	if (m_pPrecursorList != NULL) {
		delete m_pPrecursorList;
	}
}

OutputStream *Spectrum::BeginChild(DWORD nIndex) {
	switch (nIndex) {
		case 0: //scanList
			return NullStream();

		case 1: //precursorList
			if (m_pPrecursorList != NULL) {
				return NULL;
			}
			m_pPrecursorList = new MemoryStream();
			return m_pPrecursorList;

		case 2: //binaryDataArrayList
			return NullStream();
	}
	return ParamGroup::BeginChild(nIndex - 3);
}

bool SpectrumList::Begin(State *pState, const XML_Char **pszAttrs)  {
	TRACEPOS(m_pStream, "SpectrumList::Begin(): ");
	return true;
}

OutputStream *SpectrumList::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { /*spectrum*/
		return m_pStream;
	}
	return TagHandler::BeginChild(nIndex - 1);
}

bool Run::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Run::Begin(): ");
	pState->pRun = this;
	m_offStartPos = m_pStream->Tell();
	ALLOC_STRUCTURE(m_pStream, 2, (DWORD, DWORD));
	return true;
}

void Run::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 2, (DWORD, DWORD), (m_arrSpectrums.GetLength(), offEndPos - m_offStartPos));
	m_pStream->Seek(offEndPos);
	m_pStream->WriteBuffered(m_arrSpectrums.GetBuffer(), m_arrSpectrums.GetLength() * sizeof(Index));
}

OutputStream *Run::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //spectrumList
		return m_pStream;
	}
	return ParamGroup::BeginChild(nIndex - 1);
}

bool MzML::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "MzML::Begin(): ");
	pState->pMzML = this;
	ALLOC_STRUCTURE(m_pStream, 8, (DWORD, DWORD, DWORD, float, float, float, float, float));
	return true;
}

void MzML::End() {
	#define BUFFER_SIZE (256 * 1024)
	off_t offMidPos = m_pStream->Tell();
	const uint32_t nSpecs = m_arrMS1Data.GetLength();
	const MS1Data *pData = m_arrMS1Data.GetBuffer();
	uint32_t j, nPoints, nLoop;
	float *pMz, *pInt;
	float nMinTime = pData->nScanTime, nMaxTime = pData->nScanTime;
	float nMinMz = pData->pMz == NULL ? FLT_MAX : pData->pMz[0], nMaxMz = pData->pMz == NULL ? FLT_MIN : pData->pMz[0];
	float nMaxIntensity = FLT_MIN;
	float nVal;
	float pBuffer[(BUFFER_SIZE + 1) * 2];
	DWORD nBufElems = 0;
	for (uint32_t i = 0; i < nSpecs; ++i) {
		nVal = pData->nScanTime;
		//WRITE_STRUCTURE(m_pStream, 2, (DWORD, float), (pData->nCount, nVal));
		pBuffer[nBufElems << 1] = *(float *)&pData->nCount;
		pBuffer[(nBufElems << 1) + 1] = nVal;
		++nBufElems;
		if (nVal < nMinTime) {
			nMinTime = nVal;
		} else if (nVal > nMaxTime) {
			nMaxTime = nVal;
		}
		nPoints = pData->nCount;
		pMz = pData->pMz;
		pInt = pData->pIntensity;
		while (nPoints > 0) {
			if (nBufElems >= BUFFER_SIZE) {
				m_pStream->Write(pBuffer, (nBufElems << 1) * sizeof(float));
				nBufElems = 0;
			}
			nLoop = nPoints < BUFFER_SIZE - nBufElems ? nPoints : BUFFER_SIZE - nBufElems;
			for (j = 0; j < nLoop; ++j) {
				nVal = pMz[j];
				if (nVal < nMinMz) {
					nMinMz = nVal;
				} else if (nVal > nMaxMz) {
					nMaxMz = nVal;
				}
				nVal = pInt[j];
				if (nVal > nMaxIntensity) {
					nMaxIntensity = nVal;
				}
				pBuffer[(nBufElems + j) << 1] = pMz[j];
				pBuffer[((nBufElems + j) << 1) + 1] = nVal;
			}
			nPoints -= nLoop;
			nBufElems += nLoop;
		}
		++pData;
	}
	if (nBufElems != 0) {
		m_pStream->Write(pBuffer, (nBufElems << 1) * sizeof(float));
	}
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(0);
	WRITE_STRUCTURE(m_pStream, 8, (DWORD, DWORD, DWORD, float, float, float, float, float), (offMidPos, offEndPos - offMidPos, m_arrMS1Data.GetLength(), nMaxIntensity, nMinTime, nMaxTime, nMinMz, nMaxMz));
}

OutputStream *MzML::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //run
		return m_pStream;
	}
	return NULL;
}

bool IndexedMzML::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "IndexedMzML::Begin(): ");
	return true;
}

OutputStream *IndexedMzML::BeginChild(DWORD nIndex) {
	if (nIndex == 0) { //mzML
		return m_pStream;
	}
	return NULL;
}

static TagHandlerEntry gs_pHandlers[] = {
	{ "indexedmzML", &IndexedMzML::New },
	{ "mzML", &MzML::New },
	{ NULL, NULL }
};

_State::_State(const char *szFilePath) : BaseState(szFilePath, gs_pHandlers) {
}

TAG_HANDLER_CHILDREN(IndexedMzML,								{ "mzML", &MzML::New }); //Unhandled: indexList, indexListOffset, fileChecksum
TAG_HANDLER_CHILDREN(MzML,										{ "run", &Run::New }); //Unhandled: cvList, fileDescription, referenceableParamGroupList, sampleList, softwareList, scanSettingsList, instrumentConfigurationList, dataProcessingList
PARAM_GROUP_CHILDREN(	Run,									{ "spectrumList", &SpectrumList::New });
TAG_HANDLER_CHILDREN(		SpectrumList,						{ "spectrum", &Spectrum::New });
PARAM_GROUP_CHILDREN(			Spectrum,						{ "scanList", &ScanList::New }, { "precursorList", &PrecursorList::New }, { "binaryDataArrayList", &BinaryDataArrayList::New }); //Unhandled: productList
TAG_HANDLER_CHILDREN(				ScanList,					{ "scan", &Scan::New });
PARAM_GROUP_CHILDREN(					Scan,					{ "scanWindowList", &ScanWindowList::New });
PARAM_GROUP_CHILDREN(						ScanWindowList,		{ "scanWindow", &ParamGroup::New });
TAG_HANDLER_CHILDREN(				PrecursorList,				{ "precursor", &Precursor::New });
TAG_HANDLER_CHILDREN(					Precursor,				{ "activation", &ParamGroup::New }, { "isolationWindow", &ParamGroup::New }, { "selectedIonList", &SelectedIonList::New });
TAG_HANDLER_CHILDREN(						SelectedIonList,	{ "selectedIon", &SelectedIon::New });
PARAM_EMPTY_CHILDREN(							SelectedIon);
TAG_HANDLER_CHILDREN(				BinaryDataArrayList,		{ "binaryDataArray", &BinaryDataArray::New });
PARAM_GROUP_CHILDREN(					BinaryDataArray,		{ "binary", &Binary::New });
TAG_HANDLER_CHILDREN(						Binary,				{ NULL, NULL });
TAG_HANDLER_CHILDREN(CVParam,									{ NULL, NULL });
TAG_HANDLER_CHILDREN(ParamGroup,								{ NULL, NULL });
