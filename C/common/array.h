#ifndef __ARRAY_H__
	#define __ARRAY_H__
	
	#include <malloc.h>
	#include "stdinc.h"
	#include "inc.h"

	//A very crude but fast vector
	//This doesn't use constants, so the state or elements can be changed quickly
	//There is also no error checking, it is assumed that it will not be used with invalid indices
	//Any objects passed into Push() must be created on the HEAP, not the stack.
	//Indices are always stored in unsigned 32 bit integers. It is assumed that there will be less than 4.3 billion elements
	
	#define CONV_CAST(x) ((PyObject *)(x))
	#define ARRAY_TO_LIST(conv) \
		PyObject *pList = PyList_New(m_nItems); \
		if (pList == NULL) { \
			return NULL; \
		} \
		for (uint32_t i = 0; i < m_nItems; ++i) { \
			PyObject *pValue = conv(m_pItems[i]); \
			if (!pValue) { \
				Py_DECREF(pList); \
				return NULL; \
			} \
			PyList_SET_ITEM(pList, i, pValue); \
		} \
		return pList;

	template<typename T>
	class PointerArray {
		public:
			PointerArray(uint32_t nInitSize = 8) : m_pItems((T *)malloc(nInitSize * sizeof(T))), m_nItems(0), m_nCapacity(nInitSize) {
				ASSERT_MEMORY(m_pItems, nInitSize * sizeof(T));
			}

			~PointerArray() {
				free(m_pItems);
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

			bool Empty() const {
				return m_nItems == 0;
			}
			
			operator PyObject *() {
				ARRAY_TO_LIST(CONV_CAST)
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
			
			operator PyObject *();

		private:
			T *m_pItems;
			uint32_t m_nItems;
			uint32_t m_nCapacity;
	};
	
	#define LITERAL_ARRAY_TO_LIST(T, conv) template<> inline LiteralArray<T>::operator PyObject *() { ARRAY_TO_LIST(conv) }
	LITERAL_ARRAY_TO_LIST(float, PyFloat_FromDouble)
	LITERAL_ARRAY_TO_LIST(double, PyFloat_FromDouble)
	LITERAL_ARRAY_TO_LIST(char, PyInt_FromLong)
	LITERAL_ARRAY_TO_LIST(short, PyInt_FromLong)
	LITERAL_ARRAY_TO_LIST(int, PyInt_FromLong)
	LITERAL_ARRAY_TO_LIST(long, PyInt_FromLong)
	LITERAL_ARRAY_TO_LIST(size_t, PyInt_FromLong)
	template<typename T> inline LiteralArray<T>::operator PyObject *() { ARRAY_TO_LIST(CONV_CAST) }

#endif
