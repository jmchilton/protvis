inline void Spectrum::SetStartTime(float nTime) {
	if (m_nStartTime >= 0.0f) { //FIXME: Do we need this?
		printf("Scan start time already set to %f\n", m_nStartTime);
	}
	m_nStartTime = nTime;
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

inline PyObject *MzML::GetSpectrum(FILE *pFile, const char *szSpectrumName) {
	return NULL; //FIXME: implement
}

inline unsigned long MzML::GetSpectrumOffset(FILE *pFile, const char *szSpectrumName) {
	return 0; //FIXME: implement
}

inline void MzML::SearchSpectrums(FILE *pFile, SearchStatus &stat) {
	//FIXME: implement
}

inline void MzML::AddSpectrum1(float nStartTime, DWORD nCount, float *pMz, float *pIntensity) {
	m_arrMS1Data.Push(MS1Data(nStartTime, nCount, pMz, pIntensity));
}
