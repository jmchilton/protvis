#ifndef __SEARCH_H__
	#define __SEARCH_H__

	#include "array.h"
	#include "inc.h"

	class SearchStatus {
		public:
			SearchStatus(PyObject *pParams) {
			}
			
			DWORD GetTotal() {
				return 0; //FIXME: implement
			}
			PyObject *GetResults() {
				return Py_BuildValue(""); //FIXME: implement
			}
	};

#endif
