#ifndef __STREAMS_H__
	#define __STREAMS_H__

	#include <sys/types.h>
	#include <stdio.h>
	#include <sys/stat.h>
	#include <fcntl.h>
	#ifdef _MSC_VER
		#include <io.h>
		
		//Use ISO C++ conformant functions on the Visual compiler
		#define open _open
		#define close _close
		#define lseek _lseek
		#define read _read
		#define write _write

		#define BIN_FILE_PERMISSIONS _S_IREAD | _S_IWRITE
	#else
		#include <unistd.h>

		#define BIN_FILE_PERMISSIONS S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH
	#endif
	#include <malloc.h>
	#include <string.h>
	#include <expat.h>
	#include "array.h"

	class OutputStream {
		public:
			virtual ~OutputStream() { }
			virtual off_t Tell() = 0;
			virtual off_t Seek(off_t nOffset, int nStart = SEEK_SET) = 0;
			virtual ssize_t Write(const void *pBuffer, size_t nBytes) = 0;
			virtual ssize_t WriteBuffered(const void *pBuffer, size_t nBytes) { return Write(pBuffer, nBytes); }
			ssize_t WriteChar(char n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteByte(BYTE n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteWord(WORD n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteInt(int n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteDWord(DWORD n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteQWord(QWORD n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteFloat(float n) { return WriteBuffered(&n, sizeof(n)); }
			ssize_t WriteDouble(double n) { return WriteBuffered(&n, sizeof(n)); }
	};

	class FileStream : public OutputStream {
		#define FILESTREAM_BUFFER_SIZE (512 * 1024)
		public:
			FileStream(const char *szFileName) : m_nDesc(open(szFileName, O_WRONLY | O_CREAT | O_TRUNC | O_SEQUENTIAL, BIN_FILE_PERMISSIONS)), m_nBuffered(0), m_bOpened(true) {
				ASSERT_ALWAYS(m_nDesc >= 0, "Failed to open the file \'%s\' for writing\n", szFileName);
			}

			FileStream(int fd) : m_nDesc(fd), m_nBuffered(0), m_bOpened(false) {
			}

			virtual ~FileStream() {
				if (m_nBuffered > 0) {
					write(m_nDesc, m_pBuffer, m_nBuffered);
				}
				if (m_bOpened) {
					close(m_nDesc);
				}
			}

			virtual off_t Tell() {
				return lseek(m_nDesc, 0, SEEK_CUR) + m_nBuffered;
			}

			virtual off_t Seek(off_t nOffset, int nStart = SEEK_SET) {
				if (m_nBuffered > 0) {
					write(m_nDesc, m_pBuffer, m_nBuffered);
					m_nBuffered = 0;
				}
				return lseek(m_nDesc, nOffset, nStart);
			}

			virtual ssize_t Write(const void *pBuffer, size_t nBytes) {
				if (m_nBuffered > 0) {
					write(m_nDesc, m_pBuffer, m_nBuffered);
					m_nBuffered = 0;
				}
				return write(m_nDesc, pBuffer, nBytes);
			}
			
			virtual ssize_t WriteBuffered(const void *pBuffer, size_t nBytes) {
				size_t n = nBytes;
				if (m_nBuffered + nBytes >= FILESTREAM_BUFFER_SIZE) {
					int nLeft = FILESTREAM_BUFFER_SIZE - m_nBuffered;
					nBytes -= nLeft;
					const char *ptr = (const char *)pBuffer + nLeft;
					memcpy(m_pBuffer + m_nBuffered, pBuffer, nLeft);
					write(m_nDesc, m_pBuffer, FILESTREAM_BUFFER_SIZE);
					if (nBytes > FILESTREAM_BUFFER_SIZE) {
						write(m_nDesc, ptr, m_nBuffered);
						m_nBuffered = 0;
					} else if (nBytes > 0) {
						memcpy(m_pBuffer, ptr, nBytes);
						m_nBuffered = nBytes;
					}
				} else {
					char *ptr = m_pBuffer + m_nBuffered;
					m_nBuffered += nBytes;
					memcpy(ptr, pBuffer, nBytes);
				}
				return n;
			}

		private:
			int m_nDesc;
			DWORD m_nBuffered;
			bool m_bOpened;
			char m_pBuffer[FILESTREAM_BUFFER_SIZE];
	};

	class MemoryStream : public OutputStream {
		public:
			MemoryStream(unsigned nInitSize = 32) : m_szString((char *)malloc(nInitSize)), m_nSeek(0), m_nCapacity(nInitSize), m_nLength(0) {
				ASSERT_MEMORY(m_szString, nInitSize);
			}
			
			virtual ~MemoryStream() {
				if (m_szString != NULL) {
					free(m_szString);
				}
			}
			
			char *StealBuffer() { //Warning: this invalidates the object but it must still be deleted
				char *pData = m_szString;
				m_szString = NULL;
				return pData;
			}

			virtual off_t Tell() {
				return m_nSeek;
			}

			virtual off_t Seek(off_t nOffset, int nStart = SEEK_SET) {
				switch (nStart) {
					case SEEK_SET:
						m_nSeek = nOffset;
						break;

					case SEEK_CUR:
						m_nSeek += nOffset;
						break;

					case SEEK_END:
						m_nSeek = m_nLength - nOffset;
						break;
				}
				return m_nSeek;
			}

			virtual ssize_t Write(const void *pBuffer, size_t nBytes) {
				if (m_nSeek + nBytes > m_nCapacity) {
					m_nCapacity = m_nCapacity * 2 + nBytes;
					m_szString = (char *)realloc(m_szString, m_nCapacity);
					ASSERT_MEMORY(m_szString, m_nCapacity);
				}
				memcpy(m_szString + m_nSeek, pBuffer, nBytes);
				m_nSeek += nBytes;
				if (m_nSeek > m_nLength) {
					m_nLength = m_nSeek;
				}
				return nBytes;
			}

			unsigned GetLength() const {
				return m_nLength;
			}

			void SetLength(unsigned nLength) { //Shorten only
				ASSERT(nLength <= m_nLength);
				m_nLength = nLength;
			}

			char *GetBuffer() { //Modify with care
				return m_szString;
			}

		private:
			char *m_szString;
			unsigned m_nSeek;
			unsigned m_nCapacity;
			unsigned m_nLength;
	};

	#define WriteStream(s) WriteBuffered(s->GetBuffer(), s->GetLength())
	#define WriteStreamBig(s) Write(s->GetBuffer(), s->GetLength())

#endif
