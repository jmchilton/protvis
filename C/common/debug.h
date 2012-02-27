#ifndef __DEBUG_H__
	#define __DEBUG_H__

	#include <stdlib.h>

	#define ASSERT_MEMORY(p, sz) if (!(p)) { fprintf(stderr, "Out of memory error allocating %u bytes of data for variable \'%s\'\n", (unsigned)(sz), #p); DIE(-2); }
	#define ASSERT_ALWAYS(b, ...) if (!(b)) { fprintf(stderr, __VA_ARGS__); DIE(-1); }

	#ifdef _DEBUG
		#define DIE(n) system("PAUSE"); exit(n);
		#define ASSERT(x) if (!(x)) { fprintf(stderr, "%s(%d): Assertion failed\n", __FILE__, __LINE__); DIE(-101); }
		#define ASSERT_MSG(msg, ...) fprintf(stderr, msg, __VA_ARGS__); DIE(-3);
	#else
		#define DIE(n) exit(n);
		#define ASSERT(x)
		#define ASSERT_MSG(msg, ...)
	#endif

#endif
