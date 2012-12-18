inline bool DecodeSpectrum(const char *szName, DWORD &nStartScan, DWORD &nEndScan, DWORD &nCharge, const char *szValidateName = NULL) {
	const char *szStartPtr = NULL, *szEndPtr = NULL, *szChargePtr = NULL, *szPtr = szName;
	for (;;) {
		szPtr = strchr(szPtr, '.');
		if (szPtr == NULL) {
			if (szStartPtr != NULL) {
				char *szEnd;
				nStartScan = strtoul(szStartPtr + 1, &szEnd, 10);
				if (*szEnd == '.') {
					nEndScan = strtoul(szEndPtr + 1, &szEnd, 10);
					if (*szEnd == '.') {
						nCharge = strtoul(szChargePtr + 1, &szEnd, 10);
						if (*szEnd == 0) {
							if (szValidateName != NULL) {
								for (; szName < szStartPtr && *szValidateName != 0; ++szName, ++szValidateName) {
									if (*szName != *szValidateName) {
										if (szName != szStartPtr || stricmp(szValidateName, ".mzml") != 0) {
											return false;
										}
									}
								}
							}
							return true;
						}
					}
				}
			}
			return false;
		}
		szStartPtr = szEndPtr;
		szEndPtr = szChargePtr;
		szChargePtr = szPtr;
		++szPtr;
	}
}

inline void ParamGroup::EndChild() {
	if (m_pCvParam != NULL) {
		delete m_pCvParam;
	}
}

inline CVParamData *ParamGroup::GetParams() {
	return m_pCvParam == NULL ? NULL : (CVParamData *)m_pCvParam->GetBuffer();
}

inline DWORD ParamGroup::GetParamsCount() {
	return m_pCvParam == NULL ? 0 : m_pCvParam->GetLength() / sizeof(CVParamData);
}

inline void Spectrum::SetStartTime(float nTime) {
	if (m_nStartTime >= 0.0f) { //FIXME: Do we need this?
		printf("Scan start time already set to %f\n", m_nStartTime);
	}
	m_nStartTime = nTime;
}

inline void Spectrum::EatAll(FILE *pFile, DWORD nCount) {
	for (DWORD i = 0; i < nCount; ++i) {
		READ_STRUCTURE(pFile, header, 2, (DWORD, DWORD));
		fseek(pFile, sizeof(DWORD) + 2 * sizeof(float) + header._0 * (sizeof(float) * 2) + header._1 * sizeof(float), SEEK_CUR);
	}
}

inline void Spectrum::SearchAll(FILE *pFile, SearchStatus &stat, DWORD nCount) {
	for (DWORD i = 0; i < nCount; ++i) {
		READ_STRUCTURE(pFile, header, 5, (DWORD, DWORD, DWORD, float, float));
		stat.Match("time", header._3);
		stat.Match("pepmass", header._4);
		if (stat.IsMatched()) {
			fseek(pFile, -(long)(2 * sizeof(DWORD) + 2 * sizeof(float)), SEEK_CUR);
			stat.AddResult(GetInfo(pFile));
		} else {
			fseek(pFile, header._0 * (sizeof(float) * 2) + header._1 * sizeof(float), SEEK_CUR);
		}
	}
}

inline PyObject *Spectrum::GetInfo(FILE *pFile) {
	READ_STRUCTURE(pFile, header, 5, (DWORD, DWORD, DWORD, float, float));
	PyObject *pList = PyList_New(header._0);
	if (pList == NULL) {
		return NULL;
	}
	for (uint32_t i = 0; i < header._0; ++i) {
		READ_STRUCTURE(pFile, ion, 2, (float, float));
		PyObject *pValue = Py_BuildValue("[f,f]", ion._0, ion._1);
		if (!pValue) {
			Py_DECREF(pList);
			return NULL;
		}
		PyList_SET_ITEM(pList, i, pValue);
	}
	PyObject *pIntensity = Py_True;
	Py_INCREF(pIntensity);
	float nPepMass;
	fread(&nPepMass, 1, sizeof(float), pFile);
	return Py_BuildValue("{s:O,s:O,s:O}", "pepmass", nPepMass > 0 ? PyFloat_FromDouble(nPepMass) : Py_BuildValue(""), "intensity", pIntensity, "ions", pList);
}

inline PyObject *Spectrum::PointsMS2All(FILE *pFile, DWORD nCount) {
	PyObject *pList = PyList_New(nCount);
	if (pList == NULL) {
		return NULL;
	}
	for (DWORD i = 0; i < nCount; ++i) {
		off_t offPos = ftell(pFile);
		READ_STRUCTURE(pFile, spectrum, 5, (DWORD, DWORD, DWORD, float, float));
		PyObject *pValue = Py_BuildValue("[f,f,k,k]", spectrum._3, spectrum._4, spectrum._2, offPos);
		if (!pValue) {
			Py_DECREF(pList);
			return NULL;
		}
		fseek(pFile, spectrum._0 * (2 * sizeof(float)) + spectrum._1 * sizeof(float), SEEK_CUR);
		PyList_SET_ITEM(pList, i, pValue);
	}
	return pList;
}

inline PyObject *Spectrum::PointsMS2ChunksAll(FILE *pFile, DWORD nChunks, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz, DWORD nCount) {
	PyObject *pLstY, *pLstX, *pList = PyList_New(nChunks);
	if (pList == NULL) {
		return NULL;
	}
	for (DWORD i = 0; i < nChunks; ++i) {
		pLstY = PyList_New(nChunks);
		if (pLstY == NULL) {
			Py_DECREF(pList);
			return NULL;
		}
		for (DWORD j = 0; j < nChunks; ++j) {
			pLstX = PyList_New(0);
			if (pLstX == NULL) {
				Py_DECREF(pList);
				return NULL;
			}
			PyList_SET_ITEM(pLstY, j, pLstX);
		}
		PyList_SET_ITEM(pList, i, pLstY);
	}
	for (DWORD i = 0; i < nCount; ++i) {
		off_t offPos = ftell(pFile);
		READ_STRUCTURE(pFile, spectrum, 5, (DWORD, DWORD, DWORD, float, float));
		PyObject *pValue = Py_BuildValue("[f,f,k,k]", spectrum._3, spectrum._4, spectrum._2, offPos);
		if (!pValue) {
			Py_DECREF(pList);
			return NULL;
		}
		fseek(pFile, spectrum._0 * (2 * sizeof(float)) + spectrum._1 * sizeof(float), SEEK_CUR);
		if (spectrum._3 >= nMinTime && spectrum._3 <= nMaxTime && spectrum._4 >= nMinMz && spectrum._4 <= nMaxMz) {
			DWORD x = (DWORD)((spectrum._3 - nMinTime) / (nMaxTime - nMinTime) * nChunks);
			DWORD y = (DWORD)((spectrum._4 - nMinMz) / (nMaxMz - nMinMz) * nChunks);
			if (x >= nChunks) {
				x = nChunks - 1;
			}
			if (y >= nChunks) {
				y = nChunks - 1;
			}
			PyList_Append(PyList_GET_ITEM(PyList_GET_ITEM(pList, y), x), pValue);
		}
	}
	return pList;
}

inline void Run::AddSpectrumN(DWORD nIndex) {
	m_arrSpectrums.Push(Index(nIndex, m_pStream->Tell()));
}

inline void Run::Search(FILE *pFile, SearchStatus &stat) {
	READ_STRUCTURE(pFile, header, 2, (DWORD, DWORD));
	Spectrum::SearchAll(pFile, stat, header._0);
}

inline PyObject *Run::GetSpectrum(FILE *pFile, DWORD nScan) {
	DWORD nOffset = GetSpectrumOffset(pFile, nScan);
	fseek(pFile, nOffset, SEEK_SET);
	PyObject *pInfo = Spectrum::GetInfo(pFile);
	PyDict_SetItemString(pInfo, "charge", PyInt_FromLong(0));
	PyDict_SetItemString(pInfo, "offset", PyInt_FromLong(nOffset));
	return pInfo;
}

inline DWORD Run::GetSpectrumOffset(FILE *pFile, DWORD nScan) {
	READ_STRUCTURE(pFile, header, 2, (DWORD, DWORD));
	fseek(pFile, header._1, SEEK_CUR);
	DWORD nSize = (header._0 + 1) / 2;
	Index *pIndex = (Index *)malloc(nSize * sizeof(Index));
	fread(pIndex, 1, nSize * sizeof(Index), pFile);
	if (pIndex[(header._0 - 1) / 2].scanId < nScan) {
		if (header._0 & 0x01) {
			--nSize;
		}
		fread(pIndex, 1, nSize * sizeof(Index), pFile);
	}
	//FIXME: binary search for small performance gain
	for (DWORD i = 0; i < nSize; ++i) {
		if (pIndex[i].scanId == nScan) {
			free(pIndex);
			return pIndex[i].spectrum__offset;
		} else if (pIndex[i].scanId > nScan) {
			free(pIndex);
			return (DWORD)-1;
		}
	}
	return (DWORD)-1;
}

inline PyObject *Run::PointsMS2(FILE *pFile) {
	READ_STRUCTURE(pFile, header, 2, (DWORD, DWORD));
	return Spectrum::PointsMS2All(pFile, header._0);
}

inline PyObject *Run::PointsMS2Chunks(FILE *pFile, DWORD nChunks, float nMinTime, float nMaxTime, float nMinMz, float nMaxMz) {
	READ_STRUCTURE(pFile, header, 2, (DWORD, DWORD));
	return Spectrum::PointsMS2ChunksAll(pFile, nChunks, nMinTime, nMaxTime, nMinMz, nMaxMz, header._0);
}

inline PyObject *MzML::GetSpectrum(FILE *pFile, const char *szSpectrumName) {
	fseek(pFile, 4 * sizeof(DWORD) + 5 * sizeof(float), SEEK_SET);
	DWORD nScan, nEndScan, nCharge;
	WORD nLength;
	char *szName = DecodeStringFromFileBuffer(pFile, 21, nLength);
	if (!DecodeSpectrum(szSpectrumName, nScan, nEndScan, nCharge, szName)) {
		return Py_BuildValue("");
	}
	PyObject *pInfo = Run::GetSpectrum(pFile, nScan);
	sprintf(szName + nLength, "%u.%u", nScan, nScan);
	PyDict_SetItemString(pInfo, "title", PyString_FromString(szName));
	if (szName != NULL) {
		free(szName);
	}
	return pInfo;
}

inline DWORD MzML::GetSpectrumOffset(FILE *pFile, const char *szSpectrumName, bool bForce) {
	fseek(pFile, 4 * sizeof(DWORD) + 5 * sizeof(float), SEEK_SET);
	DWORD nScan, nEndScan, nCharge;
	char *szName = DecodeStringFromFile(pFile);
	if (!DecodeSpectrum(szSpectrumName, nScan, nEndScan, nCharge, bForce ? NULL : szName)) {  // Force => Not validating name? Seems variable name is wrong. -John
		return (DWORD)-1;
	}
	if (szName != NULL) {
		free(szName);
	}
	return Run::GetSpectrumOffset(pFile, nScan);
}

inline void MzML::SearchSpectrums(FILE *pFile, SearchStatus &stat) {
	fseek(pFile, 4 * sizeof(DWORD) + 5 * sizeof(float), SEEK_SET);
	char *szName = DecodeStringFromFile(pFile);
	if (szName == NULL) {
		stat.pData = (void *)"";
	} else {
		stat.pData = szName;
	}
	Run::Search(pFile, stat);
	if (szName == NULL) {
		free(szName);
	}
}

inline void MzML::AddSpectrum1(float nStartTime, DWORD nCount, float *pMz, float *pIntensity) {
	m_arrMS1Data.Push(MS1Data(nStartTime, nCount, pMz, pIntensity));
}

inline void MzML::Info(FILE *pFile, float &nMinTime, float &nMaxTime, float &nMinMz, float &nMaxMz, float &nMaxIntensity, char *&szName) {
	fseek(pFile, 4 * sizeof(DWORD), SEEK_SET);
	READ_STRUCTURE(pFile, info, 5, (float, float, float, float, float));
	nMinTime = info._1;
	nMaxTime = info._2;
	nMinMz = info._3;
	nMaxMz = info._4;
	nMaxIntensity = info._0;
	szName = DecodeStringFromFile(pFile);
}

inline PyObject *MzML::PointsMS2(FILE *pFile) {
	SkipHeaders(pFile);
	return Run::PointsMS2(pFile);
}

inline PyObject *MzML::PointsMS2Chunks(FILE *pFile, DWORD nChunks) {
	fseek(pFile, 4 * sizeof(DWORD) + sizeof(float), SEEK_SET);
	READ_STRUCTURE(pFile, info, 4, (float, float, float, float));
	EatStringFromFile(pFile);
	return Run::PointsMS2Chunks(pFile, nChunks, info._0, info._1, info._2, info._3);
}

inline void MzML::SkipHeaders(FILE *pFile) {
	DWORD nRunOffset;
	fread(&nRunOffset, 1, sizeof(DWORD), pFile);
	fseek(pFile, nRunOffset, SEEK_SET);
}
