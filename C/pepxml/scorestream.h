#ifndef __SCORESTREAM_H__
	#define __SCORESTREAM_H__

	#include "../common/streams.h"

	class ScoreStream : public OutputStream {
		public:
			typedef enum _ScoreType { //Must be in alphabetical order for BST search below to work correctly
				SS_A_RATIO,
				SS_BVALUE,
				SS_EXPECT,
				SS_HOMOLOGYSCORE,
				SS_HYPERSCORE,
				SS_IDENTITYSCORE,
				SS_IONSCORE,
				SS_IP_PROB,
				SS_NEXTSCORE,
				SS_PP_PROB,
				SS_PVALUE,
				SS_STAR,
				SS_X_RATIO,
				SS_YSCORE,
				SS_COUNT
			} ScoreType;

			ScoreStream() {
				memset(m_colScores, 0xFF, sizeof(m_colScores)); //NaN hack
			}

			virtual off_t Tell() {
				ASSERT_MSG("Function ScoreStream::Tell() was called. This function should not be used\n");
				return 0;
			}

			virtual off_t Seek(off_t nOffset, int nStart = SEEK_SET) {
				ASSERT_MSG("Function ScoreStream::Seek() was called. This function should not be used\n");
				return 0;
			}

			virtual ssize_t Write(const void *pBuffer, size_t nBytes) {
				ASSERT_MSG("Function ScoreStream::Write() was called. This function should not be used\n");
				return 0;
			}

			void SetScore(const XML_Char *szType, double nScore) {
				const XML_Char *szTypes[] = { "bscore", "expect", "homologyscore", "hyperscore", "identityscore", "ionscore", "nextscore", "pvalue", "star", "yscore" };
				unsigned i;
				for (unsigned nStart = 0, nEnd = sizeof(szTypes) / sizeof(szTypes[0]);;) {
					i = (nEnd + nStart) / 2;
					int nCmp = strcmp(szType, szTypes[i]);
					if (nCmp == 0) {
						m_colScores[i] = nScore;
						return;
					} else {
						if (nStart == nEnd) {
							break;
						}
						if (nCmp > 0) {
							nStart = i + 1;
						} else {
							nEnd = i - 1;
						}
					}
				}
				printf("Unknown score \'%s\'\n", szType);
			}

			void SetScore(ScoreType eType, double nScore) {
				m_colScores[eType] = nScore;
			}

			bool GetScore(ScoreType eType, double *pScore) {
				*pScore = m_colScores[eType];
				return *(uint64_t *)pScore == 0xFFFFFFFFFFFFFFFFULL; //Another NaN hack
			}

			double *GetScorePtr(ScoreType eType) {
				double *pScore = &m_colScores[eType];
				return *(uint64_t *)pScore == 0xFFFFFFFFFFFFFFFFULL ? NULL : pScore; //Another NaN hack
			}

		private:
			double m_colScores[SS_COUNT];
	};

#endif
