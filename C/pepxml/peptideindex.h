#ifndef __PEPTIDEINDEX_H__
	#define __PEPTIDEINDEX_H__

	#include "../common/array.h"

	template<typename T>
	class PeptideInstances {
		public:
			typedef struct _IndexData {
				T QueryOffset;
				T HitOffset;
			} IndexData;

			void Add(T nQueryOffset, T nHitOffset) {
				if (m_nItems == m_nCapacity) {
					m_nCapacity *= 2;
					m_pItems = (IndexData *)realloc(m_pItems, m_nCapacity * sizeof(IndexData));
					ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(IndexData));
				}
				IndexData id = { nQueryOffset, nHitOffset };
				memcpy(&m_pItems[m_nItems++], &id, sizeof(IndexData));
			}

			const char *GetPeptide() const {
				return Peptide;
			}

			uint32_t GetCount() const {
				return m_nItems;
			}

			IndexData *GetBuffer() {
				return m_pItems;
			}

			IndexData &Get(uint32_t nIndex) {
				ASSERT(m_nItems > nIndex);
				return m_pItems[nIndex];
			}

		private:
			void Create(const char *szPeptide, size_t nPeptideLen, T nQueryOffset, T nHitOffset) {
				Peptide = (char *)malloc(nPeptideLen * sizeof(char));
				ASSERT_MEMORY(Peptide, nPeptideLen * sizeof(char));
				memcpy(Peptide, szPeptide, nPeptideLen * sizeof(char));
				m_nCapacity = 4;
				m_pItems = (IndexData *)malloc(m_nCapacity * sizeof(IndexData));
				ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(IndexData));
				m_nItems = 1;
			}

			void Deconstruct() {
				free(m_pItems);
				free(Peptide);
			}

		private:
			char *Peptide;
			IndexData *m_pItems;
			uint32_t m_nItems;
			uint32_t m_nCapacity;

		template<typename X> friend class PeptideArray;
	};
	
	template<typename T>
	class PeptideArray {
		public:
			PeptideArray(uint32_t nInitSize = 8) : m_pItems((PeptideInstances<T> *)malloc(nInitSize * sizeof(PeptideInstances<T>))), m_nItems(0), m_nCapacity(nInitSize) {
				ASSERT_MEMORY(m_pItems, nInitSize * sizeof(PeptideInstances<T>));
			}

			~PeptideArray() {
				for (uint32_t i = 0; i < m_nItems; ++i) {
					m_pItems[i].Deconstruct();
				}
				free(m_pItems);
			}

			bool Add(const char *szPeptide, size_t nPeptideLen, T nQueryOffset, T nHitOffset) {
				for (uint32_t i = 0; i < m_nItems; ++i) {
					PeptideInstances<T> &piPeptide = m_pItems[i];
					if (strcmp(piPeptide.GetPeptide(), szPeptide) == 0) {
						piPeptide.Add(nQueryOffset, nHitOffset);
						return false;
					}
				}
				if (m_nItems == m_nCapacity) {
					m_nCapacity *= 2;
					m_pItems = (PeptideInstances<T> *)realloc(m_pItems, m_nCapacity * sizeof(PeptideInstances<T>));
					ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(PeptideInstances<T>));
				}
				m_pItems[m_nItems++].Create(szPeptide, nPeptideLen, nQueryOffset, nHitOffset);
				return true;
			}

			uint32_t GetLength() const {
				return m_nItems;
			}

			PeptideInstances<T> &Get(uint32_t nIndex) {
				ASSERT(m_nItems > nIndex);
				return m_pItems[nIndex];
			}

			uint32_t GetInstances(PeptideInstances<T> **pBuffer) const {
				for (uint32_t i = 0; i < m_nItems; ++i) {
					*pBuffer++ = &m_pItems[i];
				}
				return m_nItems;
			}

		private:
			PeptideInstances<T> *m_pItems;
			uint32_t m_nItems;
			uint32_t m_nCapacity;
	};

	template<typename T>
	class PeptideIndex {
		public:
			PeptideIndex() : m_nPeptides(0) {
			}

			~PeptideIndex() {
			}

			void Add(const char *szPeptide, T nQueryOffset, T nHitOffset) {
				WORD nHash = 0;
				const char *szPtr = szPeptide;
				for (; *szPtr != 0; ++szPtr) {
					nHash ^= (*szPtr & 0xDF) - 'A';
					if (*++szPtr == 0) {
						break;
					}
					nHash ^= ((*szPtr & 0xDF) - 'A') << 5;
				}
				if (m_colBins[nHash].Add(szPeptide, szPtr - szPeptide + 1, nQueryOffset, nHitOffset)) {
					++m_nPeptides;
				}
			}

			DWORD ConsolidateAndGet(PeptideInstances<T> ***pBuffer) const {
				PeptideInstances<T> **pBuf = (PeptideInstances<T> **)malloc(m_nPeptides * sizeof(PeptideInstances<T> *));
				*pBuffer = pBuf;
				for (int i = 0; i < 32 * 32; ++i) {
					pBuf += m_colBins[i].GetInstances(pBuf);
				}
				qsort(*pBuffer, m_nPeptides, sizeof(PeptideInstances<T> *), CmpPeptideInstance);
				return m_nPeptides;
			}

			static int CmpPeptideInstance(const void *e1, const void *e2) {
				return (*(PeptideInstances<T> **)e2)->GetCount() - (*(PeptideInstances<T> **)e1)->GetCount();
			}

		private:
			PeptideArray<T> m_colBins[32 * 32]; //2 chars of A-Y: 25 chars = 6 bits
			DWORD m_nPeptides;
	};

#endif
