#ifdef _MSC_VER
	#include "../common/inc.h"
#else
	#include "../common/inc.h"
#endif
#include "../common/stdinc.h"
#include "../common/reference.h"
#include "handlers.h"
#include "msplot.h"

static PyObject *ToBinary(PyObject *self, PyObject *args) {
	const char *szDest;
	const char *szOriginalName;
	PyObject *pFile;
	if (!PyArg_ParseTuple(args, "Oss", &pFile, &szDest, &szOriginalName)) {
		return NULL;
	}
	State state(szDest, szOriginalName);
	int fd = fileno(PyFile_AsFile(pFile));
	lseek(fd, 0, SEEK_SET);
	Transcode(fd, &state);
	return Py_BuildValue("i", FILETYPE_MZML);
}

static PyObject *GetSpectrumFromScan(PyObject *self, PyObject *args) {
	const char *szFileName;
	DWORD nScan;
	if (!PyArg_ParseTuple(args, "si", &szFileName, &nScan)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		PyObject *pRet = MzML::GetSpectrumFromScan(pFile, nScan);
		fclose(pFile);
		return pRet;
	}
	return Py_BuildValue("");
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
	char bForce = 0;
	if (!PyArg_ParseTuple(args, "ss|b", &szFileName, &szSpectrumName, &bForce)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		long nOffset = MzML::GetSpectrumOffset(pFile, szSpectrumName, bForce);
		fclose(pFile);
		return Py_BuildValue("i", nOffset);
	}
	return Py_BuildValue("i", -1);
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

static PyObject *Display(PyObject *self, PyObject *args) {
	const char *szFileName;
	PyObject *pQuery;
	if (!PyArg_ParseTuple(args, "sO", &szFileName, &pQuery)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile != NULL) {
		float nMinTime, nMaxTime, nMinMz, nMaxMz, nMaxIntensity;
		char *szName;
		MzML::Info(pFile, nMinTime, nMaxTime, nMinMz, nMaxMz, nMaxIntensity, szName);
		fclose(pFile);
		PyObject *ret = Py_BuildValue("[f,f,f,f,f,s]", nMinTime, nMaxTime, nMinMz, nMaxMz, nMaxIntensity, szName);
		free(szName);
		return ret;
	}
	return Py_BuildValue("");
}

static PyObject *SpectrumMS1Smooth(PyObject *self, PyObject *args) {
	const char *szFileName;
	float nContrast;
	long nWidth, nHeight;
	float nMinTime = -1.0f, nMaxTime = -1.0f, nMinMz = -1.0f, nMaxMz = -1.0f;
	if (!PyArg_ParseTuple(args, "sfll|ffff", &szFileName, &nContrast, &nWidth, &nHeight, &nMinTime, &nMaxTime, &nMinMz, &nMaxMz)) {
		return NULL;
	}
	if (nWidth <= 0 || nHeight <= 0) {
		return Py_BuildValue("");
	}
	MemoryStream *pStream = MS1Plot::RenderFromFileSmooth(szFileName, nWidth, nHeight, pow(nContrast, 1.2f), nMinTime, nMaxTime, nMinMz, nMaxMz);
	PyObject *pRet = pStream == NULL ? Py_BuildValue("") : Py_BuildValue("s#", pStream->GetBuffer(), pStream->GetLength());
	delete pStream;
	return pRet;
}

static PyObject *SpectrumMS1Points(PyObject *self, PyObject *args) {
	const char *szFileName;
	float nContrast;
	long nWidth, nHeight;
	float nMinTime = -1.0f, nMaxTime = -1.0f, nMinMz = -1.0f, nMaxMz = -1.0f;
	if (!PyArg_ParseTuple(args, "sfll|ffff", &szFileName, &nContrast, &nWidth, &nHeight, &nMinTime, &nMaxTime, &nMinMz, &nMaxMz)) {
		return NULL;
	}
	if (nWidth <= 0 || nHeight <= 0) {
		return Py_BuildValue("");
	}
	MemoryStream *pStream = MS1Plot::RenderFromFilePoints(szFileName, nWidth, nHeight, pow(nContrast, 1.2f), nMinTime, nMaxTime, nMinMz, nMaxMz);
	PyObject *pRet = pStream == NULL ? Py_BuildValue("") : Py_BuildValue("s#", pStream->GetBuffer(), pStream->GetLength());
	delete pStream;
	return pRet;
}

static PyObject *SpectrumMS2(PyObject *self, PyObject *args) {
	const char *szFileName;
	long nWidth, nHeight;
	float nMinTime = -1.0f, nMaxTime = -1.0f, nMinMz = -1.0f, nMaxMz = -1.0f;
	if (!PyArg_ParseTuple(args, "sll|ffff", &szFileName, &nWidth, &nHeight, &nMinTime, &nMaxTime, &nMinMz, &nMaxMz)) {
		return NULL;
	}
	if (nWidth <= 0 || nHeight <= 0) {
		return Py_BuildValue("");
	}
	MemoryStream *pStream = MS2Plot::RenderFromFile(szFileName, nWidth, nHeight, nMinTime, nMaxTime, nMinMz, nMaxMz);
	PyObject *pRet = pStream == NULL ? Py_BuildValue("") : Py_BuildValue("s#", pStream->GetBuffer(), pStream->GetLength());
	delete pStream;
	return pRet;
}

static PyObject *PointsMS2Chunks(PyObject *self, PyObject *args) {
	const char *szFileName;
	DWORD nChunks;
	if (!PyArg_ParseTuple(args, "sI", &szFileName, &nChunks)) {
		return NULL;
	}
	FILE *pFile = fopen(szFileName, "r");
	if (pFile == NULL) {
		return Py_BuildValue("");
	}
	PyObject *pList = MzML::PointsMS2Chunks(pFile, nChunks);
	fclose(pFile);
	return pList;
}

static PyObject *Version(PyObject *self, PyObject *args) {
	return Py_BuildValue("f", 0.8);
}

static PyMethodDef Methods[] = {
    {"ToBinary", ToBinary, METH_VARARGS, ""},
    {"GetSpectrum", GetSpectrum, METH_VARARGS, ""},
    {"GetSpectrumFromScan", GetSpectrumFromScan, METH_VARARGS, ""},
    {"GetSpectrumFromOffset", GetSpectrumFromOffset, METH_VARARGS, ""},
    {"GetOffsetFromSpectrum", GetOffsetFromSpectrum, METH_VARARGS, ""},
    {"Search", Search, METH_VARARGS, ""},
    {"DefaultSortColumn", DefaultSortColumn, METH_VARARGS, ""},
    {"Display", Display, METH_VARARGS, ""},
    {"spectrum_ms1_smooth", SpectrumMS1Smooth, METH_VARARGS, ""},
    {"spectrum_ms1_points", SpectrumMS1Points, METH_VARARGS, ""},
    {"spectrum_ms2", SpectrumMS2, METH_VARARGS, ""},
    {"points_ms2_chunks", PointsMS2Chunks, METH_VARARGS, ""},
    {"version", Version, METH_VARARGS, ""},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initMzML() {
	PyObject *pModule = Py_InitModule("MzML", Methods);
	if (pModule == NULL) {
		return;
	}
}
