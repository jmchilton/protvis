inline void Spectrum::SetStartTime(float nTime) {
	if (m_nStartTime >= 0.0f) { //FIXME: Do we need this?
		printf("Scan start time already set to %f\n", m_nStartTime);
	}
	m_nStartTime = nTime;
}

inline void Spectrum::SearchAll(FILE *pFile, SearchStatus &stat, DWORD nCount) {
	for (DWORD i = 0; i < nCount; ++i) {
		READ_STRUCTURE(pFile, header, 4, (DWORD, DWORD, float, float));
		stat.Match("time", header._2);
		stat.Match("pepmass", header._3);
		if (stat.IsMatched()) {
			fseek(pFile, -(2 * sizeof(DWORD) + 2 * sizeof(float)), SEEK_CUR);
			stat.AddResult(GetInfo(pFile));
		} else {
			fseek(pFile, header._0 * (sizeof(float) * 2) + header._1 * sizeof(float), SEEK_CUR);
		}
	}
}

inline PyObject *Spectrum::GetInfo(FILE *pFile) {
	READ_STRUCTURE(pFile, header, 4, (DWORD, DWORD, float, float));
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
	float nPepMass = 0; //FIXME: implement
	return Py_BuildValue("{s:O,s:O,s:O}", "pepmass", nPepMass > 0 ? PyFloat_FromDouble(nPepMass) : Py_BuildValue(""), "intensity", pIntensity, "ions", pList);
}

inline void Run::AddSpectrumN(DWORD nIndex) {
	m_arrSpectrums.Push(Index(nIndex, m_pStream->Tell()));
}

inline void Run::Search(FILE *pFile, SearchStatus &stat) {
	READ_STRUCTURE(pFile, header, 2, (DWORD, DWORD));
	SpectrumList::SearchAll(pFile, stat, header._0);
}

inline PyObject *MzML::GetSpectrum(FILE *pFile, const char *szSpectrumName) {
	return NULL; //FIXME: implement
}

inline unsigned long MzML::GetSpectrumOffset(FILE *pFile, const char *szSpectrumName) {
	return 0; //FIXME: implement
}

inline void MzML::SearchSpectrums(FILE *pFile, SearchStatus &stat) {
	fseek(pFile, 3 * sizeof(DWORD) + 5 * sizeof(float), SEEK_SET);
	Run::Search(pFile, stat);
}

inline void MzML::AddSpectrum1(float nStartTime, DWORD nCount, float *pMz, float *pIntensity) {
	m_arrMS1Data.Push(MS1Data(nStartTime, nCount, pMz, pIntensity));
}

inline void MzML::Info(FILE *pFile, float &nMinTime, float &nMaxTime, float &nMinMz, float &nMaxMz, float &nMaxIntensity) {
	fseek(pFile, 3 * sizeof(DWORD), SEEK_SET);
	READ_STRUCTURE(pFile, info, 5, (float, float, float, float, float));
	nMinTime = info._1;
	nMaxTime = info._2;
	nMinMz = info._3;
	nMaxMz = info._4;
	nMaxIntensity = info._0;
}
