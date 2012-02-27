#include "../common/stdinc.h"
#include "handlers.h"

//Helpers

BYTE GetEngineCode(const XML_Char *szName) {
	if (strcmp(szName, "interprophet") == 0) {
		return 1;
	}
	return 0;
}

//Handlers

bool Specificity::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Specificity.__init__(): ");
	const XML_Char *min_spacing = Attr(pszAttrs, "min_spacing");
	const XML_Char *no_cut = Attr(pszAttrs, "no_cut");
	WRITE_STRUCTURE(m_pStream, 2, (char, BYTE), (Attr(pszAttrs, "sense")[0], ENCODE_OPTIONAL(min_spacing, no_cut)));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "cut"));
	if (min_spacing != NULL) {
		EncodeStringToFile(m_pStream, min_spacing);
	}
	if (no_cut != NULL) {
		EncodeStringToFile(m_pStream, no_cut);
	}
	return true;
}

bool SampleEnzyme::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SampleEnzyme.__init__(): ");
	BYTE nFlags = 0x00;
	const XML_Char *fidelity = Attr(pszAttrs, "fidelity");
	if (fidelity != NULL) {
		if (strcmp(fidelity, "semispecific") == 0) {
			nFlags = 0x01;
		} else if (strcmp(fidelity, "nonspecific") == 0) {
			nFlags = 0x02;
		}
	}
	const XML_Char *independent = Attr(pszAttrs, "independent");
	if (independent == NULL) {
		nFlags |= 0x08;
	} else {
		if (strcmp(independent, "true") == 0) {
			nFlags |= 0x04;
		}
	}
	const XML_Char *description = Attr(pszAttrs, "description");
	if (description != NULL) {
		nFlags |= 0x10;
	}
	m_pStream->WriteByte(nFlags);
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "name"));
	if (description != NULL) {
		EncodeStringToFile(m_pStream, description);
	}
	m_offCountPos = m_pStream->Tell();
	m_pStream->WriteWord(0);
	m_nSpecificities = 0;
	return true;
}

void SampleEnzyme::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offCountPos);
	m_pStream->WriteWord(m_nSpecificities);
	m_pStream->Seek(offEndPos);
}

OutputStream *SampleEnzyme::BeginChild(const char *szName) {
	if (strcmp(szName, "specificity") == 0) {
		++m_nSpecificities;
		return m_pStream;
	}
	return NULL;
}

bool ModAminoacidMass::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ModAminoAcidMass.__init__(): ");
	WRITE_STRUCTURE(m_pStream, 2, (DWORD, double), (AS_DWORD(Attr(pszAttrs, "position")), AS_DOUBLE(Attr(pszAttrs, "mass"))));
	return true;
}

bool ModificationInfo::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ModificationInfo.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	const XML_Char *mod_nterm_mass = Attr(pszAttrs, "mod_nterm_mass");
	const XML_Char *mod_cterm_mass = Attr(pszAttrs, "mod_cterm_mass");
	WRITE_STRUCTURE(m_pStream, 2, (WORD, BYTE), (0, ENCODE_OPTIONAL(mod_nterm_mass, mod_cterm_mass)));
	if (mod_nterm_mass != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(mod_nterm_mass));
	}
	if (mod_cterm_mass != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(mod_cterm_mass));
	}
	m_nMassCount = 0;
	return true;
}

void ModificationInfo::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nMassCount);
	m_pStream->Seek(offEndPos);
}

OutputStream *ModificationInfo::BeginChild(const char *szName) {
	if (strcmp(szName, "mod_aminoacid_mass") == 0) {
		++m_nMassCount;
		return m_pStream;
	}
	return NULL;
}

bool AlternativeProtein::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "AlternativeProtein.__init__(): ");
	const XML_Char *protein_descr = Attr(pszAttrs, "protein_descr");
	const XML_Char *num_tol_term = Attr(pszAttrs, "num_tol_term");
	const XML_Char *protein_mw = Attr(pszAttrs, "protein_mw");
	m_pStream->WriteByte(ENCODE_OPTIONAL(protein_descr, num_tol_term, protein_mw));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "protein"));
	if (protein_descr != NULL) {
		EncodeStringToFile(m_pStream, protein_descr);
	}
	if (num_tol_term != NULL) {
		m_pStream->WriteInt(AS_INT(num_tol_term));
	}
	if (protein_mw != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(protein_mw));
	}
	return true;
}

bool SearchScoreSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SearchScoreSummary.__init__(): ");
	/*m_nParamCount = 0;
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteWord(0);*/
	return true;
}

void SearchScoreSummary::End() {
	/*off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nParamCount);
	m_pStream->Seek(offEndPos);*/
}

OutputStream *SearchScoreSummary::BeginChild(const char *szName) {
	/*if (strcmp(szName, "parameter") == 0) {
		++m_nParamCount;
		return m_pStream;
	}
	return NULL;*/
	return m_pStream;
}

bool PeptideprophetResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "PeptideprophetResult.__init__(): ");
	((ScoreStream *)m_pStream)->SetScore(ScoreStream::SS_PP_PROB, AS_DOUBLE(Attr(pszAttrs, "probability")));
	return true;
}

OutputStream *PeptideprophetResult::BeginChild(const char *szName) {
	if (strcmp(szName, "search_score_summary") == 0) {
		return NullStream();
	}
	return NULL;
}
	
bool InterprophetResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "InterprophetResult.__init__(): ");
	((ScoreStream *)m_pStream)->SetScore(ScoreStream::SS_IP_PROB, AS_DOUBLE(Attr(pszAttrs, "probability")));
	return true;
}

OutputStream *InterprophetResult::BeginChild(const char *szName) {
	if (strcmp(szName, "search_score_summary") == 0) {
		return NullStream();
	}
	return NULL;
}
	
bool AsapratioResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "AsapratioResult.__init__(): ");
	ASSERT_MSG("AsapratioResult not yet implemented\n");
	return false;
}
	
bool XpressratioResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "XpressratioResult.__init__(): ");
	ASSERT_MSG("XpressratioResult not yet implemented\n");
	return false;
}

bool AnalysisResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "AnalysisResult.__init__(): ");
	//m_nHad = 0;
	return true;
}

OutputStream *AnalysisResult::BeginChild(const char *szName) {
	/*if (strcmp(szName, "peptideprophet_result") == 0) {
		m_nHad |= 0x01;
		return m_pStream;
	} else if (strcmp(szName, "interprophet_result") == 0) {
		m_nHad |= 0x02;
		return m_pStream;
	} else if (strcmp(szName, "asapratio_result") == 0) {
		m_nHad |= 0x04;
		return m_pStream;
	} else if (strcmp(szName, "xpressratio_result") == 0) {
		m_nHad |= 0x08;
		return m_pStream;
	}
	return NULL;*/
	return m_pStream;
}

bool SearchScore::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SearchScore.__init__(): ");
	((ScoreStream *)m_pStream)->SetScore(Attr(pszAttrs, "name"), AS_DOUBLE(Attr(pszAttrs, "value")));
	return true;
}

bool SearchHit::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SearchHit.__init__(): ");
	m_pState = pState;
	const XML_Char *is_rejected = Attr(pszAttrs, "is_rejected");
	WORD nFlags = 0;
	if (is_rejected != NULL && is_rejected[0] == '1' && is_rejected[1] == 0) {
		nFlags = 0x8000;
	}
	const XML_Char *protein_descr = Attr(pszAttrs, "protein_descr");
	const XML_Char *peptide_prev_aa = Attr(pszAttrs, "peptide_prev_aa");
	const XML_Char *peptide_next_aa = Attr(pszAttrs, "peptide_next_aa");
	const XML_Char *num_matched_ions = Attr(pszAttrs, "num_matched_ions");
	const XML_Char *tot_num_ions = Attr(pszAttrs, "tot_num_ions");
	const XML_Char *num_tol_term = Attr(pszAttrs, "num_tol_term");
	const XML_Char *num_missed_cleavages = Attr(pszAttrs, "num_missed_cleavages");
	const XML_Char *calc_pI = Attr(pszAttrs, "calc_pI");
	const XML_Char *protein_mw = Attr(pszAttrs, "protein_mw");
	nFlags |= ENCODE_OPTIONAL(protein_descr, peptide_prev_aa, peptide_next_aa, num_matched_ions, tot_num_ions, num_tol_term, num_missed_cleavages, calc_pI, protein_mw);
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 8, (DWORD, WORD, WORD, DWORD, double, double, WORD, BYTE), (0, 0, 0, 0, AS_FLOAT(Attr(pszAttrs, "calc_neutral_pep_mass")), AS_FLOAT(Attr(pszAttrs, "massdiff")), nFlags, (BYTE)AS_DWORD(Attr(pszAttrs, "num_tot_proteins"))));
	TRACEPOS(m_pStream, "SearchHit.__init__(peptide): ");
	const XML_Char *peptide = Attr(pszAttrs, "peptide");
	pState->Peptides.Add(peptide, pState->QueryOffset, m_offStartPos);
	EncodeStringToFile(m_pStream, peptide);
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "protein"));
	if (protein_descr != NULL) {
		EncodeStringToFile(m_pStream, protein_descr);
	}
	if (peptide_prev_aa != NULL) {
		if (*peptide_prev_aa == 0) {
			m_pStream->WriteByte(0);
		} else {
			m_pStream->WriteByte(*peptide_prev_aa);
		}
	}
	if (peptide_next_aa != NULL) {
		if (*peptide_next_aa == 0) {
			m_pStream->WriteByte(0);
		} else {
			m_pStream->WriteByte(*peptide_next_aa);
		}
	}
	if (num_matched_ions != NULL) {
		m_pStream->WriteByte((BYTE)AS_INT(num_matched_ions));
	}
	if (tot_num_ions != NULL) {
		m_pStream->WriteDword(AS_INT(tot_num_ions));
	}
	if (num_tol_term != NULL) {
		m_pStream->WriteInt(AS_INT(num_tol_term));
	}
	if (num_missed_cleavages != NULL) {
		m_pStream->WriteInt(AS_INT(num_missed_cleavages));
	}
	if (calc_pI != NULL) {
		EncodeStringToFile(m_pStream, calc_pI);
	}
	if (protein_mw != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(protein_mw));
	}
	off_t DataOffset = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos + 4 + 2 + 2);
	m_pStream->WriteDWord(DataOffset - m_offStartPos);
	m_pStream->Seek(DataOffset);
	m_nModCount = 0;
	m_nAltCount = 0;
	m_pModInfos = NULL;
	m_pAltProts = NULL;
	return true;
}

void SearchHit::End() {
	double *bvalue = m_colScores.GetScorePtr(ScoreStream::SS_BVALUE);
	double *expect = m_colScores.GetScorePtr(ScoreStream::SS_EXPECT);
	double *homologyscore = m_colScores.GetScorePtr(ScoreStream::SS_HOMOLOGYSCORE);
	double *hyperscore = m_colScores.GetScorePtr(ScoreStream::SS_HYPERSCORE);
	double *identityscore = m_colScores.GetScorePtr(ScoreStream::SS_IDENTITYSCORE);
	double *ionscore = m_colScores.GetScorePtr(ScoreStream::SS_IONSCORE);
	double *nextscore = m_colScores.GetScorePtr(ScoreStream::SS_NEXTSCORE);
	double *pvalue = m_colScores.GetScorePtr(ScoreStream::SS_PVALUE);
	double *star = m_colScores.GetScorePtr(ScoreStream::SS_STAR);
	double *yscore = m_colScores.GetScorePtr(ScoreStream::SS_YSCORE);
	double *pp_prob = m_colScores.GetScorePtr(ScoreStream::SS_PP_PROB);
	double *ip_prob = m_colScores.GetScorePtr(ScoreStream::SS_IP_PROB);
	double *a_ratio = m_colScores.GetScorePtr(ScoreStream::SS_A_RATIO);
	double *x_ratio = m_colScores.GetScorePtr(ScoreStream::SS_X_RATIO);
	TRACEPOS(m_pStream, "SearchHit.End(SearchScore): ");
	WORD nScores = ENCODE_OPTIONAL(bvalue, expect, homologyscore, hyperscore, identityscore, ionscore, nextscore, pvalue, star, yscore, pp_prob, ip_prob, a_ratio, x_ratio);
	m_pState->IncludedScores |= nScores;
	m_pStream->WriteWord(nScores);
	if (bvalue != NULL) {
		m_pStream->WriteDouble(*bvalue);
	}
	if (expect != NULL) {
		m_pStream->WriteDouble(*expect);
	}
	if (homologyscore != NULL) {
		m_pStream->WriteDouble(*homologyscore);
	}
	if (hyperscore != NULL) {
		m_pStream->WriteDouble(*hyperscore);
	}
	if (identityscore != NULL) {
		m_pStream->WriteDouble(*identityscore);
	}
	if (ionscore != NULL) {
		m_pStream->WriteDouble(*ionscore);
	}
	if (nextscore != NULL) {
		m_pStream->WriteDouble(*nextscore);
	}
	if (pvalue != NULL) {
		m_pStream->WriteDouble(*pvalue);
	}
	if (star != NULL) {
		m_pStream->WriteDouble(*star);
	}
	if (yscore != NULL) {
		m_pStream->WriteDouble(*yscore);
	}
	if (pp_prob != NULL) {
		m_pStream->WriteFloat((float)*pp_prob);
	}
	if (ip_prob != NULL) {
		m_pStream->WriteFloat((float)*ip_prob);
	}
	if (a_ratio != NULL) {
		m_pStream->WriteFloat((float)*a_ratio);
	}
	if (x_ratio != NULL) {
		m_pStream->WriteFloat((float)*x_ratio);
	}
	if (m_pModInfos != NULL) {
		m_pStream->WriteStream(m_pModInfos);
		delete m_pModInfos;
	}
	if (m_pAltProts != NULL) {
		m_pStream->WriteStream(m_pAltProts);
		delete m_pAltProts;
	}
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 3, (DWORD, WORD, WORD), (offEndPos - m_offStartPos, m_nModCount, m_nAltCount));
	m_pStream->Seek(offEndPos);
}

OutputStream *SearchHit::BeginChild(const char *szName) {
	if (strcmp(szName, "search_score") == 0) {
		return &m_colScores;
	} else {
		int nCmp = strcmp(szName, "analysis_result");
		if (nCmp == 0) {
			return &m_colScores;
		} else if (nCmp < 0) {
			if (strcmp(szName, "alternative_protein") == 0) {
				++m_nAltCount;
				if (m_pAltProts == NULL) {
					m_pAltProts = new MemoryStream();
				}
				return m_pAltProts;
			}
		} else {
			if (strcmp(szName, "modification_info") == 0) {
				++m_nModCount;
				if (m_pModInfos == NULL) {
					m_pModInfos = new MemoryStream();
				}
				return m_pModInfos;
			}
		}
	}
	return NULL;
}

bool SearchResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SearchResult.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteDWord(0);
	m_nSearchHits = 0;
	return true;
}

void SearchResult::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteDWord(m_nSearchHits);
	m_pStream->Seek(offEndPos);
}

OutputStream *SearchResult::BeginChild(const char *szName) {
	if (strcmp(szName, "search_hit") == 0) {
		++m_nSearchHits;
		return m_pStream;
	}
	return NULL;
}

bool SearchDatabase::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SearchDatabase.__init__(): ");
	const XML_Char *URL = Attr(pszAttrs, "URL");
	const XML_Char *database_name = Attr(pszAttrs, "database_name");
	const XML_Char *orig_database_url = Attr(pszAttrs, "orig_database_url");
	const XML_Char *database_release_date = Attr(pszAttrs, "database_release_date");
	const XML_Char *database_release_identifier = Attr(pszAttrs, "database_release_identifier");
	const XML_Char *size_in_db_entries = Attr(pszAttrs, "size_in_db_entries");
	const XML_Char *size_of_residues = Attr(pszAttrs, "size_of_residues");
	BYTE nFlags = ENCODE_OPTIONAL(URL, database_name, orig_database_url, database_release_date, database_release_identifier, size_in_db_entries, size_of_residues);
	if (stricmp(Attr(pszAttrs, "type"), "NA") == 0) {
		nFlags |= 0x80;
	}
	m_pStream->WriteByte(nFlags);
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "local_path"));
	if (URL != NULL) {
		EncodeStringToFile(m_pStream, URL);
	}
	if (database_name != NULL) {
		EncodeStringToFile(m_pStream, database_name);
	}
	if (orig_database_url != NULL) {
		EncodeStringToFile(m_pStream, orig_database_url);
	}
	if (database_release_date != NULL) {
		EncodeStringToFile(m_pStream, database_release_date);
	}
	if (database_release_identifier != NULL) {
		EncodeStringToFile(m_pStream, database_release_identifier);
	}
	if (size_in_db_entries != NULL) {
		m_pStream->WriteInt(AS_INT(size_in_db_entries));
	}
	if (size_of_residues != NULL) {
		m_pStream->WriteInt(AS_INT(size_of_residues));
	}
	return true;
}

bool DistributionPoint::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "DistributionPoint.__init__(): ");
	WRITE_STRUCTURE(m_pStream, 10, (float, int, float, float, int, float, float, int, float, float), (AS_FLOAT(Attr(pszAttrs, "fvalue")), AS_INT(Attr(pszAttrs, "obs_1_distr")), AS_FLOAT(Attr(pszAttrs, "model_1_pos_distr")), AS_FLOAT(Attr(pszAttrs, "model_1_neg_distr")), AS_INT(Attr(pszAttrs, "obs_2_distr")), AS_FLOAT(Attr(pszAttrs, "model_2_pos_distr")), AS_FLOAT(Attr(pszAttrs, "model_2_neg_distr")), AS_INT(Attr(pszAttrs, "obs_3_distr")), AS_FLOAT(Attr(pszAttrs, "model_3_pos_distr")), AS_FLOAT(Attr(pszAttrs, "model_3_neg_distr"))));
	return true;
}

bool EnzymaticSearchConstraint::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "EnzymaticSearchConstraint.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "enzyme"));
	WRITE_STRUCTURE(m_pStream, 2, (int32_t, int32_t), (AS_INT(Attr(pszAttrs, "max_num_internal_cleavages")), AS_INT(Attr(pszAttrs, "min_number_termini"))));
	return true;
}

bool SequenceSearchConstraint::Begin(State *pState, const XML_Char **pszAttrs) {
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "sequence"));
	return true;
}

bool AminoacidModification::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "AminoacidModification.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "aminoacid"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "massdiff"));
	m_pStream->WriteFloat(AS_FLOAT(Attr(pszAttrs, "mass")));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "variable"));
	const XML_Char *peptide_terminus = Attr(pszAttrs, "peptide_terminus");
	const XML_Char *symbol = Attr(pszAttrs, "symbol");
	const XML_Char *binary = Attr(pszAttrs, "binary");
	const XML_Char *description = Attr(pszAttrs, "description");
	m_pStream->WriteByte(ENCODE_OPTIONAL(peptide_terminus, symbol, binary, description));
	if (peptide_terminus != NULL) {
		EncodeStringToFile(m_pStream, peptide_terminus);
	}
	if (symbol != NULL) {
		EncodeStringToFile(m_pStream, symbol);
	}
	if (binary != NULL) {
		EncodeStringToFile(m_pStream, binary);
	}
	if (description != NULL) {
		EncodeStringToFile(m_pStream, description);
	}
	return true;
}

bool TerminalModification::Begin(State *pState, const XML_Char **pszAttrs) {
	ASSERT("NYI: TerminalModification") //FIXME: implement
	return true;
}

bool Parameter::Begin(State *pState, const XML_Char **pszAttrs) {
	/*t = Attr(pszAttrs, "value");
	m_pStream->WriteByte(ENDCODE_OPTIONAL(1, t));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "name"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "value"));
	if (t != NULL) {
		EncodeStringToFile(m_pStream, t);
	}*/
	return true;
}

bool SearchSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SearchSummary.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	m_out_data_type = Attr(pszAttrs, "out_data_type");
	m_out_data = Attr(pszAttrs, "out_data");
	m_pStream->WriteByte(0);
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "base_name"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "search_engine"));
	if (m_out_data_type != NULL) {
		EncodeStringToFile(m_pStream, m_out_data_type);
	}
	if (m_out_data != NULL) {
		EncodeStringToFile(m_pStream, m_out_data);
	}
	m_pSearchDatabase = NULL;
	m_pEnzymaticSearchConstraint = NULL;
	m_nSequenceSearchConstraintCount = 0;
	m_nAminoacidModificationCount = 0;
	m_nTerminalModificationCount = 0;
	m_nParameterCount = 0;
	m_pSequenceSearchConstraint = NULL;
	m_pAminoacidModification = NULL;
	m_pTerminalModification = NULL;
	m_pParameter = NULL;
	return true;
}

void SearchSummary::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteByte(ENCODE_OPTIONAL(m_out_data_type, m_out_data, m_pSearchDatabase, m_pEnzymaticSearchConstraint));
	m_pStream->Seek(offEndPos);
	if (m_pSearchDatabase != NULL) {
		m_pStream->WriteStream(m_pSearchDatabase);
		delete m_pSearchDatabase;
	}
	if (m_pEnzymaticSearchConstraint != NULL) {
		m_pStream->WriteStream(m_pEnzymaticSearchConstraint);
		delete m_pEnzymaticSearchConstraint;
	}
	WRITE_STRUCTURE(m_pStream, 4, (WORD, WORD, WORD, WORD), (m_nSequenceSearchConstraintCount, m_nAminoacidModificationCount, m_nTerminalModificationCount, m_nParameterCount));
	if (m_pSequenceSearchConstraint != NULL) {
		m_pStream->WriteStream(m_pSequenceSearchConstraint);
		delete m_pSequenceSearchConstraint;
	}
	if (m_pAminoacidModification != NULL) {
		m_pStream->WriteStream(m_pAminoacidModification);
		delete m_pAminoacidModification;
	}
	if (m_pTerminalModification != NULL) {
		m_pStream->WriteStream(m_pTerminalModification);
		delete m_pTerminalModification;
	}
	if (m_pParameter != NULL) {
		m_pStream->WriteStream(m_pParameter);
		delete m_pParameter;
	}
}

OutputStream *SearchSummary::BeginChild(const char *szName) {
	if (strcmp(szName, "sequence_search_constraint") == 0) {
		if (m_pSequenceSearchConstraint == NULL) {
			m_pSequenceSearchConstraint = new MemoryStream();
		}
		++m_nSequenceSearchConstraintCount;
		return m_pSequenceSearchConstraint;
	}
	if (strcmp(szName, "aminoacid_modification") == 0) {
		if (m_pAminoacidModification == NULL) {
			m_pAminoacidModification = new MemoryStream();
		}
		++m_nAminoacidModificationCount;
		return m_pAminoacidModification;
	}
	if (strcmp(szName, "terminal_modification") == 0) {
		if (m_pTerminalModification == NULL) {
			m_pTerminalModification = new MemoryStream();
		}
		++m_nTerminalModificationCount;
		return m_pTerminalModification;
	}
	if (strcmp(szName, "parameter") == 0) {
		if (m_pParameter == NULL) {
			m_pParameter = new MemoryStream();
		}
		++m_nParameterCount;
		return m_pParameter;
	}
	if (strcmp(szName, "search_database") == 0) {
		if (m_pSearchDatabase != NULL) {
			return NULL;
		}
		m_pSearchDatabase = new MemoryStream();
		return m_pSearchDatabase;
	}
	if (strcmp(szName, "enzymatic_search_constraint") == 0) {
		if (m_pEnzymaticSearchConstraint != NULL) {
			return NULL;
		}
		m_pEnzymaticSearchConstraint = new MemoryStream();
		return m_pEnzymaticSearchConstraint;
	}
	return NULL;
}

bool DatabaseRefreshTimestamp::Begin(State *pState, const XML_Char **pszAttrs) {
	/*XML_Char *min_num_enz_term = Attr(pszAttrs, "min_num_enz_term");
	m_pStream->WriteByte(ENCODE_OPTIONAL(min_num_enz_term));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "database"));
	m_pStream->WriteInt(AS_INT(min_num_enz_term));*/
	return true;
}

bool XpressratioTimestamp::Begin(State *pState, const XML_Char **pszAttrs) {
	//m_pStream->WriteInt(AS_INT(Attr(pszAttrs, "xpress_light")));
	return true;
}

bool AnalysisTimestamp::Begin(State *pState, const XML_Char **pszAttrs) {
	//This data is excluded from the binary file
	return true;
}

OutputStream *AnalysisTimestamp::BeginChild(const char *szName) {
	return NullStream(); //we don't care about this
}

bool SpectrumQuery::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "SpectrumQuery.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	pState->QueryOffset = m_offStartPos;
	const XML_Char *retention_time_sec = Attr(pszAttrs, "retention_time_sec");
	const XML_Char *search_specification = Attr(pszAttrs, "search_specification");
	WRITE_STRUCTURE(m_pStream, 4, (DWORD, DWORD, WORD, BYTE), (0, 0, 0, ENCODE_OPTIONAL(retention_time_sec, search_specification)));
	WRITE_STRUCTURE(m_pStream, 5, (DWORD, DWORD, float, int32_t, DWORD), (AS_INT(Attr(pszAttrs, "start_scan")), AS_INT(Attr(pszAttrs, "end_scan")), AS_FLOAT(Attr(pszAttrs, "precursor_neutral_mass")), AS_INT(Attr(pszAttrs, "assumed_charge")), AS_INT(Attr(pszAttrs, "index"))));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "spectrum"));
	if (retention_time_sec != NULL) {
		m_pStream->WriteFloat(AS_FLOAT(retention_time_sec));
	}
	if (search_specification != NULL) {
		EncodeStringToFile(m_pStream, search_specification);
	}
	m_offResultsPos = m_pStream->Tell();
	m_nSearchResults = 0;
	return true;
}

void SpectrumQuery::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 3, (DWORD, DWORD, WORD), (offEndPos - m_offStartPos, m_offResultsPos - m_offStartPos, m_nSearchResults));
	m_pStream->Seek(offEndPos);
}

OutputStream *SpectrumQuery::BeginChild(const char *szName) {
	if (strcmp(szName, "search_result") == 0) {
		++m_nSearchResults;
		return m_pStream;
	}
	return NULL;
}

bool MsmsRunSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "MsmsRunSummary.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	const XML_Char *msManufacturer = Attr(pszAttrs, "msManufacturer");
	const XML_Char *msModel = Attr(pszAttrs, "msModel");
	const XML_Char *msIonization = Attr(pszAttrs, "msIonization");
	const XML_Char *msMassAnalyzer = Attr(pszAttrs, "msMassAnalyzer");
	const XML_Char *msDetector = Attr(pszAttrs, "msDetector");
	WRITE_STRUCTURE(m_pStream, 5, (DWORD, DWORD, DWORD, DWORD, BYTE), (0, 0, 0, 0, ENCODE_OPTIONAL(msManufacturer, msModel, msIonization, msMassAnalyzer, msDetector)));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "base_name"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "raw_data_type"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "raw_data"));
	if (msManufacturer != NULL) {
		EncodeStringToFile(m_pStream, msManufacturer);
	}
	if (msModel != NULL) {
		EncodeStringToFile(m_pStream, msModel);
	}
	if (msIonization != NULL) {
		EncodeStringToFile(m_pStream, msIonization);
	}
	if (msMassAnalyzer != NULL) {
		EncodeStringToFile(m_pStream, msMassAnalyzer);
	}
	if (msDetector != NULL) {
		EncodeStringToFile(m_pStream, msDetector);
	}
	m_offQueriesPos = m_pStream->Tell();
	m_pSampleEnzyme = NULL;
	m_pSearchSummary = NULL;
	m_nSpectrumQueries = 0;
	return true;
}

void MsmsRunSummary::End() {
	off_t offOtherDataOffset = m_pStream->Tell();
	m_pStream->WriteStream(m_pSampleEnzyme);
	m_pStream->WriteStream(m_pSearchSummary);
	delete m_pSampleEnzyme;
	delete m_pSearchSummary;
	//AnalysisTimestamp
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 4, (DWORD, DWORD, DWORD, DWORD), (offEndPos - m_offStartPos, m_nSpectrumQueries, m_offQueriesPos - m_offStartPos, offOtherDataOffset - m_offStartPos));
	m_pStream->Seek(offEndPos);
}

OutputStream *MsmsRunSummary::BeginChild(const char *szName) {
	if (strcmp(szName, "spectrum_query") == 0) {
		++m_nSpectrumQueries;
		return m_pStream;
	} else if (strcmp(szName, "sample_enzyme") == 0) {
		m_pSampleEnzyme = new MemoryStream();
		return m_pSampleEnzyme;
	} else if (strcmp(szName, "search_summary") == 0) {
		m_pSearchSummary = new MemoryStream();
		return m_pSearchSummary;
	} else if (strcmp(szName, "analysis_timestamp") == 0) {
		return NullStream();
	}
	return NULL;
}

bool DatasetDerivation::Begin(State *pState, const XML_Char **pszAttrs) {
	ASSERT_MSG("DatasetDerivation is not implemented\n");
	return false;
}

bool Point::Begin(State *pState, const XML_Char **pszAttrs) {
	return true; //we don't care about this
}

bool PosmodelDistribution::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "PosmodelDistribution.__init__(): ");
	BYTE nType = 0;
	const XML_Char *szType = Attr(pszAttrs, "type");
	if (szType != NULL) {
		int nCmp = stricmp(szType, "extremevalue");
		if (nCmp == 0) {
			nType = 3;
		} else if (nCmp < 0) {
			if (stricmp(szType, "discrete") == 0) {
				nType = 1;
			} else if (stricmp(szType, "evd") == 0) {
				nType = 5;
			}
		} else {
			if (stricmp(szType, "gamma") == 0) {
				nType = 2;
			} else if (stricmp(szType, "gaussian") == 0) {
				nType = 4;
			}
		}
	}
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 2, (WORD, BYTE), (0, nType));
	m_nParams = 0;
	return true;
}

void PosmodelDistribution::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nParams);
	m_pStream->Seek(offEndPos);
}

OutputStream *PosmodelDistribution::BeginChild(const char *szName) {
	if (strcmp(szName, "parameter") == 0) {
		++m_nParams;
		return m_pStream;
	}
	return NULL;
}

bool NegmodelDistribution::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "NegmodelDistribution.__init__(): ");
	BYTE nType = 0;
	const XML_Char *szType = Attr(pszAttrs, "type");
	if (szType != NULL) {
		int nCmp = stricmp(szType, "extremevalue");
		if (nCmp == 0) {
			nType = 3;
		} else if (nCmp < 0) {
			if (stricmp(szType, "discrete") == 0) {
				nType = 1;
			} else if (stricmp(szType, "evd") == 0) {
				nType = 5;
			}
		} else {
			if (stricmp(szType, "gamma") == 0) {
				nType = 2;
			} else if (stricmp(szType, "gaussian") == 0) {
				nType = 4;
			}
		}
	}
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 2, (WORD, BYTE), (0, nType));
	m_nParams = 0;
	return true;
}

void NegmodelDistribution::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nParams);
	m_pStream->Seek(offEndPos);
}

OutputStream *NegmodelDistribution::BeginChild(const char *szName) {
	if (strcmp(szName, "parameter") == 0) {
		++m_nParams;
		return m_pStream;
	}
	return NULL;
}

bool MixturemodelDistribution::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "MixturemodelDistribution.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "name"));
	m_bHadPos = false;
	m_pNegDist = NULL;
	return true;
}

void MixturemodelDistribution::End() {
	if (m_pNegDist != NULL) {
		m_pStream->WriteStream(m_pNegDist);
		delete m_pNegDist;
	}
}

OutputStream *MixturemodelDistribution::BeginChild(const char *szName) {
	if (strcmp(szName, "posmodel_distribution") == 0) {
		m_bHadPos = true;
		return m_pStream;
	} else if (strcmp(szName, "negmodel_distribution") == 0) {
		if (m_bHadPos) {
			return m_pStream;
		}
		m_pNegDist = new MemoryStream();
		return m_pNegDist;
	}
	return NULL;
}

bool Mixturemodel::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Mixturemodel.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteWord(0);
	/*WRITE_STRUCTURE(m_pStream, 3, (WORD, int, float), (Attr(pszAttrs, "precursor_ion_charge"), Attr(pszAttrs, "prior_probability")));
	EncodeStringToFile(stream, Attr(pszAttrs, "comments"));
	EncodeStringToFile(stream, Attr(pszAttrs, "est_tot_correct"));
	EncodeStringToFile(stream, Attr(pszAttrs, "tot_num_spectra"));
	EncodeStringToFile(stream, Attr(pszAttrs, "num_iterations"));*/
	m_nModels = 0;
	return true;
}

void Mixturemodel::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nModels);
	m_pStream->Seek(offEndPos);
}

OutputStream *Mixturemodel::BeginChild(const char *szName) {
	if (strcmp(szName, "mixturemodel_distribution") == 0) {
		++m_nModels;
		return m_pStream;
	} else if (strcmp(szName, "point") == 0) {
		return NullStream();
	}
	return NULL;
}
		
bool Inputfile::Begin(State *pState, const XML_Char **pszAttrs) {
	return true; //FIXME: Do we care about this?
}
	
bool RocDataPoint::Begin(State *pState, const XML_Char **pszAttrs) {
	return true; //we don't care about this
}

bool ErrorPoint::Begin(State *pState, const XML_Char **pszAttrs) {
	return true; //#we don't care about this
}
		
bool InteractSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	return true; //we don't care about this
}

OutputStream *InteractSummary::BeginChild(const char *szName) {
	if (strcmp(szName, "inputfile") == 0) {
		return NullStream();
	}
	return NULL; //we don't care about this
}

bool AnalysisSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	const XML_Char *version = Attr(pszAttrs, "version");
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 11, (DWORD, WORD, WORD, WORD, WORD, WORD, WORD, WORD, WORD, WORD, BYTE), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (version == NULL ? 0 : 0x80) | GetEngineCode(Attr(pszAttrs, "analysis"))));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "time"));
	if (version != NULL) {
		EncodeStringToFile(m_pStream, version);
	}
	m_nPeptides = 0;
	m_nInteracts = 0;
	m_nLibras = 0;
	m_nAsaps = 0;
	m_nXpresss = 0;
	m_nFiles = 0;
	m_nRocs = 0;
	m_nErrors = 0;
	m_nMixtures = 0;
	m_pInteract = NULL;
	m_pLibra = NULL;
	m_pAsap = NULL;
	m_pXpress = NULL;
	m_pFile = NULL;
	m_pRoc = NULL;
	m_pError = NULL;
	m_pMixture = NULL;
	return true;
}

void AnalysisSummary::End() {
	if (m_pInteract != NULL) {
		m_pStream->WriteStream(m_pInteract);
		delete m_pInteract;
	}
	if (m_pLibra != NULL) {
		m_pStream->WriteStream(m_pLibra);
		delete m_pLibra;
	}
	if (m_pAsap != NULL) {
		m_pStream->WriteStream(m_pAsap);
		delete m_pAsap;
	}
	if (m_pXpress != NULL) {
		m_pStream->WriteStream(m_pXpress);
		delete m_pXpress;
	}
	if (m_pFile != NULL) {
		m_pStream->WriteStream(m_pFile);
		delete m_pFile;
	}
	if (m_pRoc != NULL) {
		m_pStream->WriteStream(m_pRoc);
		delete m_pRoc;
	}
	if (m_pError != NULL) {
		m_pStream->WriteStream(m_pError);
		delete m_pError;
	}
	if (m_pMixture != NULL) {
		m_pStream->WriteStream(m_pMixture);
		delete m_pMixture;
	}
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 10, (DWORD, WORD, WORD, WORD, WORD, WORD, WORD, WORD, WORD, WORD), (offEndPos - m_offStartPos, m_nPeptides, m_nInteracts, m_nLibras, m_nAsaps, m_nXpresss, m_nFiles, m_nRocs, m_nErrors, m_nMixtures));
	m_pStream->Seek(offEndPos);
}

OutputStream *AnalysisSummary::BeginChild(const char *szName) {
	if (strcmp(szName, "peptideprophet_summary") == 0) {
		++m_nPeptides;
		return m_pStream;
	} else if (strcmp(szName, "interact_summary") == 0) {
		++m_nInteracts;
		if (m_pInteract ==NULL) {
			m_pInteract = new MemoryStream();
		}
		return m_pInteract;
	} else if (strcmp(szName, "libra_summary") == 0) {
		++m_nLibras;
		if (m_pLibra == NULL) {
			m_pLibra = new MemoryStream();
		}
		return m_pLibra;
	} else if (strcmp(szName, "asapratio_summary") == 0) {
		++m_nAsaps;
		if (m_pAsap == NULL) {
			m_pAsap = new MemoryStream();
		}
		return m_pAsap;
	} else if (strcmp(szName, "xpressratio_summary") == 0) {
		++m_nXpresss;
		if (m_pXpress == NULL) {
			m_pXpress = new MemoryStream();
		}
		return m_pXpress;
	} else if (strcmp(szName, "inputfile") == 0) { 
		++m_nFiles;
		if (m_pFile == NULL) {
			m_pFile = new MemoryStream();
		}
		return m_pFile;
	} else if (strcmp(szName, "roc_data_point") == 0) {
		++m_nRocs;
		if (m_pRoc == NULL) {
			m_pRoc = new MemoryStream();
		}
		return m_pRoc;
	} else if (strcmp(szName, "error_point") == 0) {
		++m_nErrors;
		if (m_pError == NULL) {
			m_pError = new MemoryStream();
		}
		return m_pError;
	} else if (strcmp(szName, "mixturemodel") == 0 || strcmp(szName, "mixture_model") == 0) {
		++m_nMixtures;
		if (m_pMixture == NULL) {
			m_pMixture = new MemoryStream();
		}
		return m_pMixture;
	}
	return NULL;
}

bool MsmsPipelineAnalysis::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "MsmsPipelineAnalysis.__init__(): ");
	m_pState = pState;
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 4, (WORD, WORD, WORD, WORD), (0, 0, 0, 0));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "summary_xml"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "date"));
	//EncodeStringToFile(m_pStream, Attr(pszAttrs, "summary_xml"));
	m_nRuns = 0;
	m_nDatasets = 0;
	m_nSummaries = 0;
	m_pDatasetDerivation = NULL;
	m_pAnalysisSummary = NULL;
	return true;
}

void MsmsPipelineAnalysis::End() {
	if (m_pDatasetDerivation != NULL) {
		m_pStream->WriteStream(m_pDatasetDerivation);
		delete m_pDatasetDerivation;
	}
	if (m_pAnalysisSummary != NULL) {
		m_pStream->WriteStream(m_pAnalysisSummary);
		delete m_pAnalysisSummary;
	}
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 4, (WORD, WORD, WORD, WORD), (m_pState->IncludedScores, m_nRuns, m_nDatasets, m_nSummaries));
	m_pStream->Seek(offEndPos);
}

OutputStream *MsmsPipelineAnalysis::BeginChild(const char *szName) {
	if (strcmp(szName, "msms_run_summary") == 0) {
		++m_nRuns;
		return m_pStream;
	} else if (strcmp(szName, "dataset_derivation") == 0) {
		if (m_pDatasetDerivation == NULL) {
			m_pDatasetDerivation = new MemoryStream();
		}
		++m_nDatasets;
		return m_pDatasetDerivation;
	} else if (strcmp(szName, "analysis_summary") == 0) {
		if (m_pAnalysisSummary == NULL) {
			m_pAnalysisSummary = new MemoryStream();
		}
		++m_nSummaries;
		return m_pAnalysisSummary;
	}
	return NULL;
}

//List of handlers
TAG_HANDLERS_BEGIN() //Ordered with most frequent at the top for efficency
	{ "search_score", &SearchScore::New },
	{ "parameter", &Parameter::New },
	{ "search_hit", &SearchHit::New },
	{ "mod_aminoacid_mass", &ModAminoacidMass::New },
	{ "modification_info", &ModificationInfo::New },
	{ "search_score_summary", &SearchScoreSummary::New },
	{ "analysis_result", &AnalysisResult::New },
	{ "spectrum_query", &SpectrumQuery::New },
	{ "search_result", &SearchResult::New },
	{ "peptideprophet_result", &PeptideprophetResult::New },
	{ "interprophet_result", &InterprophetResult::New },
	{ "asapratio_result", &AsapratioResult::New },
	{ "xpressratio_result", &XpressratioResult::New },
	{ "point", &Point::New },
	{ "alternative_protein", &AlternativeProtein::New },
	{ "aminoacid_modification", &AminoacidModification::New },
	{ "analysis_timestamp", &AnalysisTimestamp::New },
	{ "distribution_point", &DistributionPoint::New },
	{ "roc_data_point", &RocDataPoint::New },
	{ "error_point", &ErrorPoint::New },
	{ "inputfile", &Inputfile::New },
	{ "specificity", &Specificity::New },
	{ "search_summary", &SearchSummary::New },
	{ "search_database", &SearchDatabase::New },
	{ "sample_enzyme", &SampleEnzyme::New },
	{ "msms_run_summary", &MsmsRunSummary::New },
	{ "enzymatic_search_constraint", &EnzymaticSearchConstraint::New },
	{ "database_refresh_timestamp", &DatabaseRefreshTimestamp::New },
	{ "posmodel_distribution", PosmodelDistribution::New },
    { "negmodel_distribution", NegmodelDistribution::New },
    { "mixturemodel_distribution", MixturemodelDistribution::New },
	{ "analysis_summary", &AnalysisSummary::New },
	{ "mixture_model", &Mixturemodel::New },
	{ "mixturemodel", &Mixturemodel::New },
	{ "interact_summary", &InteractSummary::New },
	{ "peptideprophet_summary", &PeptideprophetSummary::New },
	{ "msms_pipeline_analysis", &MsmsPipelineAnalysis::New },
	//{ "roc_error_data", RocErrorData::New },
	{ "sequence_search_constraint", &SequenceSearchConstraint::New },
	{ "terminal_modification", &TerminalModification::New },
	{ "xpressratio_timestamp", &XpressratioTimestamp::New },
	{ "dataset_derivation", &DatasetDerivation::New }
TAG_HANDLERS_END()

void EncodePeptides(State &state) {
	off_t offIndexStart = state.osFile.Tell();
	state.osFile.Seek(0);
	state.osFile.WriteDWord(offIndexStart);
	state.osFile.Seek(offIndexStart);
	PeptideInstances<DWORD> **pPeptides;
	DWORD nPeptides = state.Peptides.ConsolidateAndGet(&pPeptides);
	state.osFile.WriteDWord(nPeptides);
	for (DWORD i = 0; i < nPeptides; ++i) {
		EncodeStringToFile(&state.osFile, pPeptides[i]->GetPeptide());
		DWORD nOccurances = pPeptides[i]->GetCount();
		state.osFile.WriteWord((WORD)nOccurances);
		for (DWORD j = 0; j < nOccurances; ++j) {
			state.osFile.Write(&pPeptides[i]->Get(j), sizeof(PeptideInstances<DWORD>::IndexData));
		}
	}
	free(pPeptides);
}
