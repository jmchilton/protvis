#include "../common/inc.h"
#include "../common/stdinc.h"
#include "../common/reference.h"
#include "handlers.h"
#include "msplot.h"

static PyObject *ToBinary(PyObject *self, PyObject *args) {
	const char *szSource, *szDest;
	if (!PyArg_ParseTuple(args, "ss", &szSource, &szDest)) {
		return NULL;
	}
	State state(szDest);
	Transcode(szSource, &state);
	/*DWORD nWidth = state.MS1.GetSpectrumCount();//(DWORD)(state.MS1.GetTimeRange() + 0.5f);
	while (nWidth > 2048) {
		nWidth >>= 1;
	}
	DWORD nHeight = (DWORD)(state.MS1.GetMzRange() + 0.5f);
	while (nHeight > 1024) {
		nHeight >>= 1;
	}
	char szLcFile[260]; //This only needs to hold "../ConvertedFiles/[unique]_[index]_lc"
	sprintf(szLcFile, "%s_lc", szDest);
	state.MS1.Render(szLcFile, nWidth, nHeight);*/
	return Py_BuildValue("i", FILETYPE_MZML);
}

static PyObject *GetSpectrum(PyObject *self, PyObject *args) {
	const char *szFileName, *szSpectrumName;
	if (!PyArg_ParseTuple(args, "ss", &szFileName, &szSpectrumName)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		PyObject *pRet = MzML::GetSpectrum(pFile, szSpectrumName);
		fclose(pFile);
		return pRet;
	}
	return Py_BuildValue("");
}

static PyObject *GetSpectrumFromOffset(PyObject *self, PyObject *args) {
	const char *szFileName;
	unsigned long nOffset;
	if (!PyArg_ParseTuple(args, "sk", &szFileName, &nOffset)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		fseek(pFile, nOffset, SEEK_SET);
		PyObject *pRet = (PyObject *)Spectrum::GetInfo(pFile);
		fclose(pFile);
		return pRet;
	}
	return Py_BuildValue("");
}

static PyObject *GetOffsetFromSpectrum(PyObject *self, PyObject *args) {
	const char *szFileName, *szSpectrumName;
	if (!PyArg_ParseTuple(args, "ss", &szFileName, &szSpectrumName)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		unsigned long nOffset = MzML::GetSpectrumOffset(pFile, szSpectrumName);
		fclose(pFile);
		return Py_BuildValue("k", nOffset);
	}
	return Py_BuildValue("k", 0);
}

static PyObject *Search(PyObject *self, PyObject *args) {
	const char *szFileName;
	PyObject *pSearchTerms;
	if (!PyArg_ParseTuple(args, "sO", &szFileName, &pSearchTerms)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		SearchStatus stat(pSearchTerms);
		MzML::SearchSpectrums(pFile, stat);
		fclose(pFile);
		return Py_BuildValue("[i,k,O]", 0, stat.GetTotal(), stat.GetResults());
	} 
	return Py_BuildValue("[i,k,[]]", 0, 0);
}

static PyObject *DefaultSortColumn(PyObject *self, PyObject *args) {
	return Py_BuildValue("[s,[]]", "spectrum");
}

static PyObject *SpectrumMS1(PyObject *self, PyObject *args) {
	const char *szFileName;
	float nContrast;
	float nMinTime = -1.0f, nMaxTime = -1.0f, nMinMz = -1.0f, nMaxMz = -1.0f;
	if (!PyArg_ParseTuple(args, "sf|ffff", &szFileName, &nContrast, &nMinTime, &nMaxTime, &nMinMz, &nMaxMz)) {
		return NULL;
	}
	MemoryStream *pStream = MS1Plot::RenderFromFile(szFileName, 1500, 1000, pow(nContrast, 1.2f), nMinTime, nMaxTime, nMinMz, nMaxMz);
	PyObject *pRet = Py_BuildValue("s#", pStream->GetBuffer(), pStream->GetLength());
	delete pStream;
	return pRet;
}

static PyObject *SpectrumMS2(PyObject *self, PyObject *args) {
	const char *szFileName;
	float nMinTime = -1.0f, nMaxTime = -1.0f, nMinMz = -1.0f, nMaxMz = -1.0f;
	if (!PyArg_ParseTuple(args, "sf|ffff", &szFileName, &nMinTime, &nMaxTime, &nMinMz, &nMaxMz)) {
		return NULL;
	}
	MemoryStream *pStream = MS2Plot::RenderFromFile(szFileName, 1500, 1000, nMinTime, nMaxTime, nMinMz, nMaxMz);
	PyObject *pRet = Py_BuildValue("s#", pStream->GetBuffer(), pStream->GetLength());
	delete pStream;
	return pRet;
}

static PyMethodDef Methods[] = {
    {"ToBinary", ToBinary, METH_VARARGS, ""},
    {"GetSpectrum", GetSpectrum, METH_VARARGS, ""},
    {"GetSpectrumFromOffset", GetSpectrumFromOffset, METH_VARARGS, ""},
    {"GetOffsetFromSpectrum", GetOffsetFromSpectrum, METH_VARARGS, ""},
    {"Search", Search, METH_VARARGS, ""},
    {"DefaultSortColumn", DefaultSortColumn, METH_VARARGS, ""},
    {"spectrum_ms1", SpectrumMS1, METH_VARARGS, ""},
    {"spectrum_ms2", SpectrumMS2, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initMzML() {
	PyObject *pModule = Py_InitModule("MzML", Methods);
	InitaliseMS1Cache();
	if (pModule == NULL) {
		return;
	}
}
