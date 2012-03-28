#include "handlers.h"
#include "stdinc.h"

#define BUFFER_SIZE 16384 //16KB read buffer

const XML_Char *Attr(const XML_Char **pszAttrs, const XML_Char *szAttr) {
	for (unsigned i = 0; pszAttrs[i] != NULL; i += 2) {
		if (strcmp(pszAttrs[i], szAttr) == 0) {
			return pszAttrs[i + 1];
		}
	}
	return NULL;
}

void StartElementHandler(BaseState *pState, const XML_Char *szName, const XML_Char **pszAttrs) {
	if (!pState->colPath.Empty()) {
		TagHandler *pParent = pState->colPath.Peek();
		if (pParent != NULL) {
			const TagHandlerEntry *pHandlers = pParent->GetHandlers();
			DWORD nIndex = 0;
			while (pHandlers->szTagName != NULL) {
				if (strcmp(pHandlers->szTagName, szName) == 0) {
					OutputStream *pStream = pParent->BeginChild(nIndex);
					if (pStream != NULL) {
						pState->colPath.Push(pHandlers->pNew(pState, pStream, pszAttrs));
						return;
					} else {
						//printf("U: %s\n", szName);
					}
					break;
				}
				++pHandlers;
				++nIndex;
			}
		} else {
			//printf("I: %s\n", szName);
		}
		pState->colPath.Push(NULL);
	} else {
		const TagHandlerEntry *pHandlers = pState->pHandlers;
		while (pHandlers->szTagName != NULL) {
			if (strcmp(pHandlers->szTagName, szName) == 0) {
				pState->colPath.Push(pHandlers->pNew(pState, &pState->osFile, pszAttrs));
				return;
			}
			++pHandlers;
		}
		pState->colPath.Push(NULL);
	}
}

void EndElementHandler(BaseState *pState, const XML_Char *szName) {
	TagHandler *pHandler = pState->colPath.Pop();
	if (pHandler != NULL) {
		pHandler->End();
		delete pHandler;
	}
}

void DataHandler(BaseState *pState, const XML_Char *szData, int nLen) {
	if (!pState->colPath.Empty()) {
		TagHandler *pHandler = pState->colPath.Peek();
		if (pHandler != NULL) {
			pHandler->RawData(szData, nLen);
		}
	}
}

bool Transcode(const char *szXmlFile, BaseState *pState) {
	int fd = open(szXmlFile, O_RDONLY | O_SEQUENTIAL);
	ASSERT_ALWAYS(fd >= 0, "Failed to open the file \'%s\' for reading\n", szXmlFile);
	bool bSuccess = Transcode(fd, pState);
	close(fd);
	return bSuccess;
}

bool Transcode(int fd, BaseState *pState) {
	int nLength;
	int bDone = 0;
	char pBuffer[BUFFER_SIZE];
	XML_Parser pParser = XML_ParserCreate(NULL);
	XML_SetUserData(pParser, pState);
	XML_SetElementHandler(pParser, (XML_StartElementHandler)&StartElementHandler, (XML_EndElementHandler)&EndElementHandler);
	XML_SetCharacterDataHandler(pParser, (XML_CharacterDataHandler)&DataHandler);
	do {
		nLength = read(fd, pBuffer, BUFFER_SIZE);
		bDone = nLength < BUFFER_SIZE;
		if (!XML_Parse(pParser, pBuffer, nLength, bDone)) {
			fprintf(stderr, "A parser error occured\n");
			return false;
		}
	} while (!bDone);
	XML_ParserFree(pParser);
	return true;
}

class EatStream : public OutputStream {
	public:
		virtual ~EatStream() { }
		virtual off_t Tell() { return 0; }
		virtual off_t Seek(off_t nOffset, int nStart = SEEK_SET) { return 0; }
		virtual ssize_t Write(const void *pBuffer, size_t nBytes) { return 0; }
};

EatStream g_EatStream;
OutputStream *g_pNullStream = &g_EatStream;
