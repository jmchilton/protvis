#ifndef __ARRAY_H__
	#define __ARRAY_H__
	
	#include "stdinc.h"
	#include "inc.h"

	//A very crude but fast vector
	//This doesn't use constants, so the state or elements can be changed quickly
	//There is also no error checking, it is assumed that it will not be used with invalid indices
	//Any objects passed into Push() must be created on the HEAP, not the stack.
	//Indices are always stored in unsigned 32 bit integers. It is assumed that there will be less than 4.3 billion elements
	
	template<typename T>
	class PointerArray {
		public:
			PointerArray(uint32_t nInitSize = 8) : m_pItems((T *)malloc(nInitSize * sizeof(T))), m_nItems(0), m_nCapacity(nInitSize) {
				ASSERT_MEMORY(m_pItems, nInitSize * sizeof(T));
			}
			
			PointerArray(const PointerArray &other) : m_pItems(other.m_pItems), m_nItems(other.m_nItems), m_nCapacity(other.m_nCapacity) { //Warning: This invalidates the old object
				((PointerArray *)&other)->m_pItems = NULL;
			}

			~PointerArray() {
				if (m_pItems != NULL) {
					free(m_pItems);
				}
			}
			
			void FreeAll() {
				T *pItem = m_pItems;
				for (uint32_t i = m_nItems; i > 0; --i) {
					free(*pItem++);
				}
			}

			void Push(T pItem) {
				if (m_nItems == m_nCapacity) {
					m_nCapacity *= 2;
					m_pItems = (T *)realloc(m_pItems, m_nCapacity * sizeof(T));
					ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(T));
				}
				m_pItems[m_nItems++] = pItem;
			}

			T Peek() {
				ASSERT(m_nItems > 0);
				return m_pItems[m_nItems - 1];
			}

			T Pop() {
				ASSERT(m_nItems > 0);
				return m_pItems[--m_nItems];
			}

			uint32_t GetLength() const {
				return m_nItems;
			}
			
			T *GetBuffer() {
				return m_pItems;
			}

			T Get(uint32_t nIndex) {
				ASSERT(m_nItems > nIndex);
				return m_pItems[nIndex];
			}

			void Set(uint32_t nIndex, T t) {
				ASSERT(m_nItems > nIndex);
				m_pItems[nIndex] = t;
			}
			
			void RemoveAt(uint32_t nIndex) {
				ASSERT(m_nItems > nIndex);
				if (--m_nItems > nIndex) {
					memmove(m_pItems + nIndex, m_pItems + nIndex + 1, (m_nItems - nIndex) * sizeof(T));
				}
			}

			bool Empty() const {
				return m_nItems == 0;
			}
			
			PointerArray &operator=(const PointerArray &other) { //Warning: This invalidates the old object
				m_pItems = other.m_pItems;
				m_nItems = other.m_nItems;
				m_nCapacity = other.m_nCapacity;
				((PointerArray *)&other)->m_pItems = NULL;
				return *this;
			}

		private:
			T *m_pItems;
			uint32_t m_nItems;
			uint32_t m_nCapacity;
	};

	template<typename T>
	class LiteralArray {
		public:
			LiteralArray(uint32_t nInitSize = 8) : m_pItems((T *)malloc(nInitSize * sizeof(T))), m_nItems(0), m_nCapacity(nInitSize) {
				ASSERT_MEMORY(m_pItems, nInitSize * sizeof(T));
			}

			~LiteralArray() {
				free(m_pItems);
			}

			void Push(const T &pItem) {
				if (m_nItems == m_nCapacity) {
					m_nCapacity *= 2;
					m_pItems = (T *)realloc(m_pItems, m_nCapacity * sizeof(T));
					ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(T));
				}
				m_pItems[m_nItems++] = pItem;
			}

			T &Peek() {
				ASSERT(m_nItems > 0);
				return m_pItems[m_nItems - 1];
			}

			T &Pop() {
				ASSERT(m_nItems > 0);
				return m_pItems[--m_nItems];
			}

			uint32_t GetLength() const {
				return m_nItems;
			}
			
			T *GetBuffer() {
				return m_pItems;
			}

			T &Get(uint32_t nIndex) {
				ASSERT(m_nItems > nIndex);
				return m_pItems[nIndex];
			}

			bool Empty() const {
				return m_nItems == 0;
			}

		private:
			T *m_pItems;
			uint32_t m_nItems;
			uint32_t m_nCapacity;
	};
	
	template<typename T>
	class Dictionary {
		public:
			Dictionary(uint32_t nInitSize = 8) : m_pItems((Pair *)malloc(nInitSize * sizeof(Pair))), m_nItems(0), m_nCapacity(nInitSize) {
				ASSERT_MEMORY(m_pItems, nInitSize * sizeof(Pair));
			}
			
			~Dictionary() {
				free(m_pItems);
			}

			uint32_t GetLength() const {
				return m_nItems;
			}

			void Remove(const char *szKey) {
				DWORD nHash = Hash(szKey);
				for (uint32_t i = 0; i < m_nItems; ++i) {
					if (m_pItems[i].nKey == nHash) {
						if (--m_nItems > i) {
							memmove(m_pItems + i, m_pItems + i + 1, (m_nItems - i) * sizeof(Pair));
						}
						break;
					}
				}
			}
			
			T *Get(const char *szKey) {
				DWORD nHash = Hash(szKey);
				for (uint32_t i = 0; i < m_nItems; ++i) {
					if (m_pItems[i].nKey == nHash) {
						return &m_pItems[i].tValue;
					}
				}
				return NULL;
			}
			
			void Set(const char *szKey, T &tValue) {
				DWORD nHash = Hash(szKey);
				for (uint32_t i = 0; i < m_nItems; ++i) {
					if (m_pItems[i].nKey == nHash) {
						m_pItems[i].tValue = tValue;
						return;
					}
				}
				if (m_nItems == m_nCapacity) {
					m_nCapacity *= 2;
					m_pItems = (Pair *)realloc(m_pItems, m_nCapacity * sizeof(Pair));
					ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(Pair));
				}
				m_pItems[m_nItems++].nKey = nHash;
				m_pItems[m_nItems++].tValue = tValue;
			}
			
			void ForceSet(const char *szKey, T &tValue) { //Warning: this function can invalidate the object if it adds an existing key
				DWORD nHash = Hash(szKey);
				if (m_nItems == m_nCapacity) {
					m_nCapacity *= 2;
					m_pItems = (Pair *)realloc(m_pItems, m_nCapacity * sizeof(Pair));
					ASSERT_MEMORY(m_pItems, m_nCapacity * sizeof(Pair));
				}
				m_pItems[m_nItems++].nKey = nHash;
				m_pItems[m_nItems++].tValue = tValue;
			}
			
		private:
			static DWORD Hash(const char *szKey) {
				if (szKey == NULL || *szKey == 0) {
					return 0;
				}
				const char *szPtr = szKey;
				DWORD nHash = *szPtr << 7;
				while (*szPtr != 0) {
					nHash = (nHash * 1000003) ^ *szPtr++;
				}
				return nHash ^ (szPtr - szKey);
			}

		private:
			typedef struct {
				DWORD nKey;
				T tValue;
			} Pair;
			Pair *m_pItems;
			uint32_t m_nItems;
			uint32_t m_nCapacity;
	};

#endif
