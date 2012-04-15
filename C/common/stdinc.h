#ifndef __STDINC_H__
	#define __STDINC_H__
	
	#ifdef _MSC_VER
		#include <Windows.h>

		typedef unsigned long long QWORD;
		typedef int int32_t;
		typedef DWORD uint32_t;
		typedef QWORD uint64_t;
		//typedef unsigned int ssize_t; //defined in pyconfig.h
	#else
		#include <stdint.h>

		typedef uint8_t BYTE;
		typedef uint16_t WORD;
		typedef uint32_t DWORD;
		typedef uint64_t QWORD;

		#define stricmp strcasecmp
		#define O_SEQUENTIAL 0
		#define O_RANDOM 0
	#endif

	#include "debug.h"

#endif
