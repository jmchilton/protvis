#ifndef __SEARCH_H__
	#define __SEARCH_H__

	#include "array.h"
	#include "inc.h"

	class SearchStatus {
		public:
			typedef PointerArray<const char *> PhraseList;
			
			SearchStatus(PyObject *pParams) : m_nTotal(0), m_pResults(PyList_New(0)) {
				PyObject *pKey, *pValue;
				Py_ssize_t nPos = 0;
				while (PyDict_Next(pParams, &nPos, &pKey, &pValue)) {
					size_t nLen = PyList_GET_SIZE(pValue);
					PhraseList phrases(nLen);
					for (size_t i = 0; i < nLen; ++i) {
						phrases.Set(i, PyString_AS_STRING(PyList_GET_ITEM(pValue, i)));
					}
					m_terms.ForceSet(PyString_AS_STRING(pKey), phrases);
				}
			}
			
			template<typename T>
			int Match(const char *szField, T x) {
				PhraseList *pPhrases = m_terms.Get(szField);
				if (pPhrases == NULL) {
					pPhrases = m_terms.Get(NULL);
					if (pPhrases == NULL) {
						return -1;
					} else {
						szField = NULL;
					}
				}
				const char **pPhrase = pPhrases->GetBuffer();
				DWORD nPhrases = pPhrases->GetLength();
				for (DWORD i = 0; i < nPhrases; ++pPhrases) {
					if (Compare(x, *pPhrase)) {
						pPhrases->RemoveAt(i);
						--nPhrases;
					} else {
						++i;
					}
				}
				if (nPhrases == 0) {
					m_terms.Remove(szField);
					return 1;
				}
				return 0;
			}
			
			int MatchWildcard(const char *szField, const char *szValue) {
				PhraseList *pPhrases = m_terms.Get(szField);
				if (pPhrases == NULL) {
					pPhrases = m_terms.Get(NULL);
					if (pPhrases == NULL) {
						return -1;
					} else {
						szField = NULL;
					}
				}
				const char **pPhrase = pPhrases->GetBuffer();
				DWORD nPhrases = pPhrases->GetLength();
				for (DWORD i = 0; i < nPhrases; ++pPhrases) {
					if (Compare(szValue, *pPhrase)) {
						pPhrases->RemoveAt(i);
						--nPhrases;
					} else {
						++i;
					}
				}
				if (nPhrases == 0) {
					m_terms.Remove(szField);
					return 1;
				}
				return 0;
			}
			
			void AddResult(PyObject *pResult) {
				PyList_Append(m_pResults, pResult);
			}
			
			bool IsMatched() {
				return m_terms.GetLength() == 0;
			}
			
			DWORD GetTotal() {
				return m_nTotal;
			}
			
			PyObject *GetResults() {
				return m_pResults;
			}
		
		private:
			bool Compare(double nValue, const char *szPhrase) {
				char *szEnd;
				double nPhrase = strtod(szPhrase, &szEnd);
				if (*szEnd != 0) {
					return false;
				}
				const char *szToken = strchr(szPhrase, '.');
				int nPrecision;
				if (szToken == NULL) {
					szToken = strchr(szPhrase, 'e');
					nPrecision = szToken == NULL ? 0 : -atoi(szToken + 1);
				} else {
					++szToken;
					const char *szToken2 = strchr(szToken, 'e');
					nPrecision = szToken == NULL ? strlen(szToken) : (szToken2 - szToken) - strlen(szToken2 + 1);
				}
				nValue -= nPhrase;
				return (nValue >= 0 ? nValue : -nValue) < pow(10, -nPrecision);
			}
			
			bool Compare(int nValue, const char *szPhrase) {
				char *szEnd;
				long nPhrase = strtol(szPhrase, &szEnd, 10);
				return *szEnd == 0 && nValue == nPhrase;
			}
			
			bool Compare(unsigned nValue, const char *szPhrase) {
				char *szEnd;
				unsigned long nPhrase = strtoul(szPhrase, &szEnd, 10);
				return *szEnd == 0 && nValue == nPhrase;
			}
			
			bool Compare(const char *szValue, const char *szPhrase) {
				const char *szPtr1, *szPtr2;
				while (*szValue != 0) {
					szPtr1 = szValue;
					szPtr2 = szPhrase;
					while (*szPtr1 != 0 && *szPtr2 != 0) {
						char c = *szPtr1;
						if (c != *szPtr2 && (c < 'a' || c > 'z' || (c & 0xDF) != (*szPtr2 & 0xDF))) {
							break;
						}
						++szPtr1;
						++szPtr2;
					}
					if (*szPtr2 == 0) {
						return true;
					} else if (*szPtr1 == 0) {
						break;
					}
					++szValue;
				}
				return false;
			}

		private:
			DWORD m_nTotal;
			Dictionary<PhraseList> m_terms;
			PyObject *m_pResults;
	};

#endif
