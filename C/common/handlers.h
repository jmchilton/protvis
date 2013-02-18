#ifndef __TAGHANDLERS_H__
	#define __TAGHANDLERS_H__

	#include "streams.h"
	#include <boost/preprocessor/punctuation/comma_if.hpp>
	#include <boost/preprocessor/list/for_each.hpp>
	#include <boost/preprocessor/tuple/to_list.hpp>
	#include <boost/preprocessor/arithmetic/sub.hpp>
	#include <boost/preprocessor/cat.hpp>

	class TagHandler;
	struct _BaseState;
	typedef TagHandler* (*TagHandlerCreator)(struct _BaseState *pUserData, OutputStream *pStream, const XML_Char **pszAttrs);
	
	typedef struct _TagHandlerEntry {
		const XML_Char *szTagName;
		TagHandlerCreator pNew;
	} TagHandlerEntry;
	
	typedef struct _BaseState {
		FileStream osFile;
		PointerArray<TagHandler*> colPath;
		TagHandlerEntry *pHandlers;

		_BaseState(const char *szFilePath, TagHandlerEntry *handlers) : osFile(szFilePath), pHandlers(handlers) { }
	} BaseState;

	class TagHandler {
		public:
			TagHandler(OutputStream *pStream, TagHandlerEntry *pHandlers) : m_pStream(pStream), m_pHandlers(pHandlers) { }
			virtual ~TagHandler() { }
			virtual void End() { }
			virtual OutputStream *BeginChild(DWORD nIndex) { return NULL; }
			//virtual void EndChild(OutputStream *pStream); //Not used
			virtual void RawData(const char *szData, int nLength) { }
			const TagHandlerEntry *GetHandlers() const { return m_pHandlers; }

		protected:
			OutputStream *m_pStream;
			TagHandlerEntry *m_pHandlers;
	};
	
	#define EXPAND(x) x
	#define NARGS(...)  _NARG(__VA_ARGS__, _RSEQ_N)
	#define _NARG(...) EXPAND(_ARG_N(__VA_ARGS__))
	#define _ARG_N(_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17, _18, _19, _20, _21, _22, _23, _24, _25, _26, _27, _28, _29, _30, _31, _32, _33, _34, _35, _36, _37, _38, _39, _40, _41, _42, _43, _44, _45, _46, _47, _48, _49, _50, _51, _52, _53, _54, _55, _56, _57, _58, _59, _60, _61, _62, _63, N, ...) N
	#define _RSEQ_N 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0
	#define HAS_COMMA(...) _ARG_N(__VA_ARGS__, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
	#define _TRIGGER_PARENTHESIS_(...) ,
	#define ISEMPTY(...) _ISEMPTY(HAS_COMMA(__VA_ARGS__), HAS_COMMA(_TRIGGER_PARENTHESIS_ __VA_ARGS__), HAS_COMMA(__VA_ARGS__ (/*empty*/)), HAS_COMMA(_TRIGGER_PARENTHESIS_ __VA_ARGS__ (/*empty*/)) )
	#define PASTE5(_0, _1, _2, _3, _4) _0 ## _1 ## _2 ## _3 ## _4
	#define _ISEMPTY(_0, _1, _2, _3) HAS_COMMA(PASTE5(_IS_EMPTY_CASE_, _0, _1, _2, _3))
	#define _IS_EMPTY_CASE_1110 ,

	#define X_HANDLER(cls, base, ...) \
		protected: \
			cls(OutputStream *pStream, TagHandlerEntry *pHandlers = ms_pHandlers##cls) : base(pStream, pHandlers) BOOST_PP_COMMA_IF(ISEMPTY(__VA_ARGS__)) __VA_ARGS__ { } \
		public: \
			static TagHandlerEntry ms_pHandlers##cls[]; \
			virtual ~cls() { /*destruction is done in cls::End()*/ } \
			static TagHandler *New(BaseState *pState, OutputStream *pStream, const XML_Char **pszAttrs) { \
				cls *obj = new cls(pStream); \
				if (!obj->Begin((struct _State *)pState, pszAttrs)) { \
					delete obj; \
					return NULL; \
				} \
				return obj; \
			} \
			bool Begin(struct _State *pState, const XML_Char **pszAttrs)
	#define TAG_HANDLER(cls, ...) X_HANDLER(cls, TagHandler, __VA_ARGS__)

	#define TAG_HANDLER_CHILDREN(cls, ...) TagHandlerEntry cls::ms_pHandlers##cls[] = { __VA_ARGS__, { NULL, NULL } };
	
	#define _UNUSED_HANDLER(n, data, elem) \
		class elem : public TagHandler { \
			TAG_HANDLER(elem) { return true; } \
		};
	#define UNUSED_HANDLERS(...) BOOST_PP_LIST_FOR_EACH(_UNUSED_HANDLER, NULL, BOOST_PP_TUPLE_TO_LIST(NARGS(__VA_ARGS__), (__VA_ARGS__)))

	//A hack up to easily read/write data structures in a single chunk
	#ifdef _MSC_VER
		#define _PACKED(struc) __pragma(pack(push, 1)) struc __pragma(pack(pop))
	#else
		#define _PACKED(struc) struc __attribute__((packed))
	#endif
	#define _VARIABLE(n, data, elem) elem BOOST_PP_CAT(data, BOOST_PP_SUB(n, 2));
	#define _VALUE(n, data, elem) elem,
	#define ___NAME(prefix, line) __##prefix##_##line
	#define __NAME(prefix, line) ___NAME(prefix, line)
	#define _NAME(prefix) __NAME(prefix, __LINE__)
	#define WRITE_STRUCTURE(stream, count, types, data) \
		_PACKED(struct _NAME(type) { \
			BOOST_PP_LIST_FOR_EACH(_VARIABLE, _, BOOST_PP_TUPLE_TO_LIST(count, types)) \
		}); \
		struct _NAME(type) _NAME(value) = { \
			BOOST_PP_LIST_FOR_EACH(_VALUE, _, BOOST_PP_TUPLE_TO_LIST(count, data)) \
		}; \
		stream->WriteBuffered(&_NAME(value), sizeof(_NAME(type)))
	#define READ_STRUCTURE(stream, name, count, types) \
		_PACKED(struct name##_Type__ { \
			BOOST_PP_LIST_FOR_EACH(_VARIABLE, _, BOOST_PP_TUPLE_TO_LIST(count, types)) \
		}); \
		struct name##_Type__ name; \
		fread(&name, 1, sizeof(name##_Type__), stream)
	#define ALLOC_STRUCTURE(stream, count, types) \
		_PACKED(struct _NAME(type) { \
			BOOST_PP_LIST_FOR_EACH(_VARIABLE, _, BOOST_PP_TUPLE_TO_LIST(count, types)) \
		}); \
		stream->Seek(sizeof(_NAME(type)), SEEK_CUR)
	
	#define ENCODE_OPTIONAL_SINGLE(n, data, elem) (elem == data ? 0 : (1 << (n - 2))) | 
	#define ENCODE_OPTIONAL(...) BOOST_PP_LIST_FOR_EACH(ENCODE_OPTIONAL_SINGLE, NULL, BOOST_PP_TUPLE_TO_LIST(NARGS(__VA_ARGS__), (__VA_ARGS__))) 0

	#define TRACEPOS(stream, msg)

	#define AS_INT(str) strtol(str, NULL, 10)
	#define AS_DWORD(str) strtoul(str, NULL, 10)
	#define AS_FLOAT(str) (float)strtod(str, NULL)
	#define AS_DOUBLE(str) strtod(str, NULL)

	inline OutputStream *NullStream() {
		extern OutputStream *g_pNullStream;
		return g_pNullStream;
	}

	inline void EncodeStringToFile(OutputStream *pStream, const char *szString) {
		WORD nLen = strlen(szString);
		pStream->Write(&nLen, sizeof(WORD));
		pStream->Write(szString, nLen);
	}

	inline void EncodeStringToFile(OutputStream *pStream, const char *szString, WORD nLen) {
		pStream->Write(&nLen, sizeof(WORD));
		pStream->Write(szString, nLen);
	}

	template<typename T>
	inline T YNBit(const XML_Char *szValue, T tMask) {
		return (szValue[0] & 0xDF) == 'Y' && szValue[1] == 0 ? tMask : 0;
	}

	const XML_Char *Attr(const XML_Char **pszAttrs, const XML_Char *szAttr);
	bool Transcode(const char *szXmlFile, BaseState *pState);
	bool Transcode(int fd, BaseState *pState);

	// Byte to verify at beginning of spectrum
	#define MS2_SPECTRUM_MARKER 0xFF00FF00;

	#define WRITE_MS2_MARKER(pStream) \
		DWORD markerVariable = MS2_SPECTRUM_MARKER; \
		pStream->WriteBuffered(&markerVariable, sizeof(DWORD));

	#define CHECK_MS2_MARKER(pStream) \
		DWORD markerRead; \
		fread(&markerRead, 1, sizeof(DWORD), pStream); \
		DWORD equal = markerRead & MS2_SPECTRUM_MARKER;\
		if(!equal) { \ 
			return; \ 
		}

	#define CHECK_MS2_MARKER_RET_NULL(pStream) \
		DWORD markerRead; \
		fread(&markerRead, 1, sizeof(DWORD), pStream); \
		DWORD equal = markerRead & MS2_SPECTRUM_MARKER;\
		if(!equal) { \ 
			return NULL; \ 
		}


#endif
