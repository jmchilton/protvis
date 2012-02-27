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

bool Parameter::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Parameter.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "name"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "value"));
	return true;
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

bool Annotation::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Annotation.__init__(): ");
	const XML_Char *ipi_name = Attr(pszAttrs, "ipi_name");
	const XML_Char *refseq_name = Attr(pszAttrs, "refseq_name");
	const XML_Char *swissprot_name = Attr(pszAttrs, "swissprot_name");
	const XML_Char *ensembl_name = Attr(pszAttrs, "ensembl_name");
	const XML_Char *trembl_name = Attr(pszAttrs, "trembl_name");
	const XML_Char *locus_link_name = Attr(pszAttrs, "locus_link_name");
	const XML_Char *flybase = Attr(pszAttrs, "flybase");
	m_pStream->WriteByte(ENCODE_OPTIONAL(ipi_name, refseq_name, swissprot_name, ensembl_name, trembl_name, locus_link_name, flybase));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "protein_description"));
	if (ipi_name != NULL) {
		EncodeStringToFile(m_pStream, ipi_name);
	}
	if (refseq_name != NULL) {
		EncodeStringToFile(m_pStream, refseq_name);
	}
	if (swissprot_name != NULL) {
		EncodeStringToFile(m_pStream, swissprot_name);
	}
	if (ensembl_name != NULL) {
		EncodeStringToFile(m_pStream, ensembl_name);
	}
	if (trembl_name != NULL) {
		EncodeStringToFile(m_pStream, trembl_name);
	}
	if (locus_link_name != NULL) {
		EncodeStringToFile(m_pStream, locus_link_name);
	}
	if (flybase != NULL) {
		EncodeStringToFile(m_pStream, flybase);
	}
	return true;
}

bool AnalysisResult::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "AnalysisResult.__init__(): ");
	const XML_Char *_id = Attr(pszAttrs, "id");
	int id = 1;
	if (_id != NULL) {
		id = AS_INT(_id);
	}
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 2, (WORD, int), (0, id));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "analysis"));
	m_nInfos = 0;
	return true;
}

void AnalysisResult::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nInfos);
	m_pStream->Seek(offEndPos);
}

OutputStream *AnalysisResult::BeginChild(const char *szName) {
	++m_nInfos;
	return m_pStream;
}

bool PeptideParentProtein::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "PeptideParentProtein.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "protein_name"));
	return true;
}
	
bool IndistinguishableProtein::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "IndistinguishableProtein.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteWord(0);
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "protein_name"));
	m_nParameters = 0;
	m_pParameter = NULL;
	return true;
}

void IndistinguishableProtein::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nParameters);
	m_pStream->Seek(offEndPos);
	if (m_pParameter != NULL) {
		m_pStream->WriteStream(m_pParameter);
		delete m_pParameter;
	}
}

OutputStream *IndistinguishableProtein::BeginChild(const char *szName) {
	if (strcmp(szName, "annotation") == 0) {
		m_nParameters |= 0x8000;
		if (m_pParameter != NULL) {
			m_pStream->WriteStream(m_pParameter);
			delete m_pParameter;
			m_pParameter = NULL;
		}
		return m_pStream;
	} else if (strcmp(szName, "parameter") == 0) {
		m_nParameters += 1;
		if (m_nParameters & 0x8000) {
			return m_pStream;
		} else {
			if (m_pParameter == NULL) {
				m_pParameter = new MemoryStream();
			}
			return m_pParameter;
		}
	}
	return NULL;
}
	
bool IndistinguishablePeptide::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "IndistinguishablePeptide.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "peptide_sequence"));
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteWord(0);
	m_nModifications = 0;
	return true;
}

void IndistinguishablePeptide::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nModifications);
	m_pStream->Seek(offEndPos);
}

OutputStream *IndistinguishablePeptide::BeginChild(const char *szName) {
	if (strcmp(szName, "modification_info") == 0) {
		m_nModifications += 1;
		return m_pStream;
	}
	return NULL;
}
	
bool Peptide::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Peptide.__init__(): ");
	const XML_Char *nsp_adjusted_probability = Attr(pszAttrs, "nsp_adjusted_probability");
	const XML_Char *ni_adjusted_probability = Attr(pszAttrs, "ni_adjusted_probability");
	const XML_Char *exp_sibling_ion_instances = Attr(pszAttrs, "exp_sibling_ion_instances");
	const XML_Char *exp_sibling_ion_bin = Attr(pszAttrs, "exp_sibling_ion_bin");
	const XML_Char *exp_tot_instances = Attr(pszAttrs, "exp_tot_instances");
	const XML_Char *n_enzymatic_termini = Attr(pszAttrs, "n_enzymatic_termini");
	const XML_Char *calc_neutral_pep_mass = Attr(pszAttrs, "calc_neutral_pep_mass");
	const XML_Char *peptide_group_designator = Attr(pszAttrs, "peptide_group_designator");
	const XML_Char *_weight = Attr(pszAttrs, "weight");
	double weight = 1.0;
	if (_weight != NULL) {
		weight = AS_DOUBLE(_weight);
	}
	const XML_Char *_n_sibling_peptides_bin = Attr(pszAttrs, "n_sibling_peptides_bin");
	int n_sibling_peptides_bin = 0;
	if (_n_sibling_peptides_bin != NULL) {
		n_sibling_peptides_bin = AS_INT(_n_sibling_peptides_bin);
	}
	m_offStartPos = m_pStream->Tell();
	WORD nFlags = YNBit(Attr(pszAttrs, "is_nondegenerate_evidence"), 0x8000) | YNBit(Attr(pszAttrs, "is_contributing_evidence"), 0x4000) | ENCODE_OPTIONAL(nsp_adjusted_probability, ni_adjusted_probability, exp_sibling_ion_instances, exp_sibling_ion_bin, exp_tot_instances, n_enzymatic_termini, calc_neutral_pep_mass, peptide_group_designator);
	WRITE_STRUCTURE(m_pStream, 11, (WORD, WORD, WORD, WORD, DWORD, DWORD, double, double, int, int, WORD), (0, 0, 0, 0, AS_INT(Attr(pszAttrs, "charge")), AS_INT(Attr(pszAttrs, "n_enzymatic_termini")), AS_DOUBLE(Attr(pszAttrs, "initial_probability")), weight, n_sibling_peptides_bin, AS_INT(Attr(pszAttrs, "n_instances")), nFlags));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "peptide_sequence"));
	if (nsp_adjusted_probability != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(nsp_adjusted_probability));
	}
	if (ni_adjusted_probability != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(ni_adjusted_probability));
	}
	if (exp_sibling_ion_instances != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(exp_sibling_ion_instances));
	}
	if (exp_sibling_ion_bin != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(exp_sibling_ion_bin));
	}
	if (exp_tot_instances != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(exp_tot_instances));
	}
	if (n_enzymatic_termini != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(n_enzymatic_termini));
	}
	if (calc_neutral_pep_mass != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(calc_neutral_pep_mass));
	}
	if (peptide_group_designator != NULL) {
		EncodeStringToFile(m_pStream, peptide_group_designator);
	}
	m_nModifications = 0;
	m_nParameters = 0;
	m_nParents = 0;
	m_nIndistinguishables = 0;
	m_pParameter = NULL;
	m_pParent = NULL;
	m_pIndistinguishable = NULL;
	return true;
}

void Peptide::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 4, (WORD, WORD, WORD, WORD), (m_nModifications, m_nParameters, m_nParents, m_nIndistinguishables));
	m_pStream->Seek(offEndPos);
	if (m_pParameter != NULL) {
		m_pStream->WriteStream(m_pParameter);
		delete m_pParameter;
	}
	if (m_pParent != NULL) {
		m_pStream->WriteStream(m_pParent);
		delete m_pParent;
	}
	if (m_pIndistinguishable != NULL) {
		m_pStream->WriteStream(m_pIndistinguishable);
		delete m_pIndistinguishable;
	}
}

OutputStream *Peptide::BeginChild(const char *szName) {
	if (strcmp(szName, "modification_info") == 0) {
		++m_nModifications;
		return m_pStream;
	}
	if (strcmp(szName, "parameter") == 0) {
		if (m_pParameter == NULL) {
			m_pParameter = new MemoryStream();
		}
		++m_nParameters;
		return m_pParameter;
	}
	if (strcmp(szName, "peptide_parent_protein") == 0) {
		if (m_pParent == NULL) {
			m_pParent = new MemoryStream();
		}
		++m_nParents;
		return m_pParent;
	}
	if (strcmp(szName, "indistinguishable_peptide") == 0) {
		if (m_pIndistinguishable == NULL) {
			m_pIndistinguishable = new MemoryStream();
		}
		++m_nIndistinguishables;
		return m_pIndistinguishable;
	}
	return NULL;
}

bool Protein::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "Protein.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	const XML_Char *percent_coverage = Attr(pszAttrs, "percent_coverage");
	const XML_Char *total_number_peptides = Attr(pszAttrs, "total_number_peptides");
	//const XML_Char *unique_stripped_peptides = Attr(pszAttrs, "unique_stripped_peptides");
	const XML_Char *subsuming_protein_entry = Attr(pszAttrs, "subsuming_protein_entry");
	const XML_Char *pct_spectrum_ids = Attr(pszAttrs, "pct_spectrum_ids");
	m_nFlags = ENCODE_OPTIONAL(percent_coverage, total_number_peptides, subsuming_protein_entry, pct_spectrum_ids);//, unique_stripped_peptides);
	WRITE_STRUCTURE(m_pStream, 7, (BYTE, WORD, WORD, WORD, WORD, double, int), (0, 0, 0, 0, 0, AS_DOUBLE(Attr(pszAttrs, "probability")), AS_INT(Attr(pszAttrs, "n_indistinguishable_proteins"))));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "protein_name"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "group_sibling_id"));
	if (percent_coverage != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(percent_coverage));
	}
	if (total_number_peptides != NULL) {
		m_pStream->WriteInt(AS_INT(total_number_peptides));
	}
	if (subsuming_protein_entry != NULL) {
		EncodeStringToFile(m_pStream, subsuming_protein_entry);
	}
	if (pct_spectrum_ids != NULL) {
		EncodeStringToFile(m_pStream, pct_spectrum_ids);
	}
	/*if (unique_stripped_peptides != NULL) {
		EncodeStringToFile(stream, unique_stripped_peptides)
	}*/
	m_nResults = 0;
	m_nProteins = 0;
	m_nPeptides = 0;
	m_nParameters = 0;
	m_pAnnotation = NULL;
	m_pResult = NULL;
	m_pProtein = NULL;
	m_pParameter = NULL;
	return true;
}

void Protein::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	if (m_pAnnotation != NULL) {
		m_nFlags |= 0x20;
	}
	WRITE_STRUCTURE(m_pStream, 5, (BYTE, WORD, WORD, WORD, WORD), (m_nFlags, m_nPeptides, m_nResults, m_nProteins, m_nParameters));
	m_pStream->Seek(offEndPos);
	if (m_pAnnotation != NULL) {
		m_pStream->WriteStream(m_pAnnotation);
	}
	if (m_pParameter != NULL) {
		m_pStream->WriteStream(m_pParameter);
	}
	if (m_pResult != NULL) {
		m_pStream->WriteStream(m_pResult);
	}
	if (m_pProtein != NULL) {
		m_pStream->WriteStream(m_pProtein);
	}
}

OutputStream *Protein::BeginChild(const char *szName) {
	if (strcmp(szName, "peptide") == 0) {
		++m_nPeptides;
		return m_pStream;
	} else if (strcmp(szName, "annotation") == 0) {
		if (m_pAnnotation == NULL) {
			m_pAnnotation = new MemoryStream();
		}
		return m_pAnnotation;
	} else if (strcmp(szName, "analysis_result") == 0) {
		if (m_pResult == NULL) {
			m_pResult = new MemoryStream();
		}
		++m_nResults;
		return m_pResult;
	} else if (strcmp(szName, "indistinguishable_protein") == 0) {
		if (m_pProtein == NULL) {
			m_pProtein = new MemoryStream();
		}
		++m_nProteins;
		return m_pProtein;
	} else if (strcmp(szName, "parameter") == 0) {
		if (m_pParameter == NULL) {
			m_pParameter = new MemoryStream();
		}
		++m_nParameters;
		return m_pParameter;
	}
	return NULL;
}

bool ProteinGroup::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ProteinGroup.__init__(): ");
	m_offStartPos = m_pStream->Tell() + 8;
	const XML_Char *pseudo_name = Attr(pszAttrs, "pseudo_name");
	WRITE_STRUCTURE(m_pStream, 3, (double, WORD, BYTE), (AS_DOUBLE(Attr(pszAttrs, "probability")), 0, ENCODE_OPTIONAL(pseudo_name)));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "group_number"));
	if (pseudo_name != NULL) {
		EncodeStringToFile(m_pStream, pseudo_name);
	}
	m_nProteins = 0;
	return true;
}

void ProteinGroup::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nProteins);
	m_pStream->Seek(offEndPos);
}

OutputStream *ProteinGroup::BeginChild(const char *szName) {
	if (strcmp(szName, "protein") == 0) {
		++m_nProteins;
		return m_pStream;
	}
	return NULL;
}

bool NspDistribution::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "NspDistribution.__init__(): ");
	const XML_Char *nsp_lower_bound_incl = Attr(pszAttrs, "nsp_lower_bound_incl");
	const XML_Char *nsp_upper_bound_excl = Attr(pszAttrs, "nsp_upper_bound_excl");
	const XML_Char *nsp_lower_bound_excl = Attr(pszAttrs, "nsp_lower_bound_excl");
	const XML_Char *nsp_upper_bound_incl = Attr(pszAttrs, "nsp_upper_bound_incl");
	const XML_Char *alt_pos_to_neg_ratio = Attr(pszAttrs, "alt_pos_to_neg_ratio");
	WRITE_STRUCTURE(m_pStream, 5, (int, double, double, double, BYTE), (AS_INT(Attr(pszAttrs, "bin_no")), AS_DOUBLE(Attr(pszAttrs, "pos_freq")), AS_DOUBLE(Attr(pszAttrs, "neg_freq")), AS_DOUBLE(Attr(pszAttrs, "pos_to_neg_ratio")), ENCODE_OPTIONAL(nsp_lower_bound_incl, nsp_upper_bound_excl, nsp_lower_bound_excl, nsp_upper_bound_incl, alt_pos_to_neg_ratio)));
	if (nsp_lower_bound_incl != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(nsp_lower_bound_incl));
	}
	if (nsp_upper_bound_excl != NULL) {
		EncodeStringToFile(m_pStream, nsp_upper_bound_excl);
	}
	if (nsp_lower_bound_excl != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(nsp_lower_bound_excl));
	}
	if (nsp_upper_bound_incl != NULL) {
		EncodeStringToFile(m_pStream, nsp_upper_bound_incl);
	}
	if (alt_pos_to_neg_ratio != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(alt_pos_to_neg_ratio));
	}
	return true;
}

bool NiDistribution::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "NiDistribution.__init__(): ");
	const XML_Char *ni_lower_bound_incl = Attr(pszAttrs, "ni_lower_bound_incl");
	const XML_Char *ni_upper_bound_excl = Attr(pszAttrs, "ni_upper_bound_excl");
	const XML_Char *ni_lower_bound_excl = Attr(pszAttrs, "ni_lower_bound_excl");
	const XML_Char *ni_upper_bound_incl = Attr(pszAttrs, "ni_upper_bound_incl");
	const XML_Char *alt_pos_to_neg_ratio = Attr(pszAttrs, "alt_pos_to_neg_ratio");
	WRITE_STRUCTURE(m_pStream, 5, (int, double, double, double, BYTE), (AS_INT(Attr(pszAttrs, "bin_no")), AS_DOUBLE(Attr(pszAttrs, "pos_freq")), AS_DOUBLE(Attr(pszAttrs, "neg_freq")), AS_DOUBLE(Attr(pszAttrs, "pos_to_neg_ratio")), ENCODE_OPTIONAL(ni_lower_bound_incl, ni_upper_bound_excl, ni_lower_bound_excl, ni_upper_bound_incl, alt_pos_to_neg_ratio)));
	if (ni_lower_bound_incl != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(ni_lower_bound_incl));
	}
	if (ni_upper_bound_excl != NULL) {
		EncodeStringToFile(m_pStream, ni_upper_bound_excl);
	}
	if (ni_lower_bound_excl != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(ni_lower_bound_excl));
	}
	if (ni_upper_bound_incl != NULL) {
		EncodeStringToFile(m_pStream, ni_upper_bound_incl);
	}
	if (alt_pos_to_neg_ratio != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(alt_pos_to_neg_ratio));
	}
	return true;
}

bool NspInformation::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "NspInformation.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "neighboring_bin_smoothing"));
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteWord(0);
	m_nDistributions = 0;
	return true;
}

void NspInformation::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nDistributions);
	m_pStream->Seek(offEndPos);
}

OutputStream *NspInformation::BeginChild(const char *szName) {
	if (strcmp(szName, "nsp_distribution") == 0) {
		++m_nDistributions;
		return m_pStream;
	}
	return NULL;
}

bool NiInformation::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "NiInformation.__init__(): ");
	//EncodeStringToFile(m_pStream, Attr(pszAttrs, "neighboring_bin_smoothing"));
	m_offStartPos = m_pStream->Tell();
	m_pStream->WriteWord(0);
	m_nDistributions = 0;
	return true;
}

void NiInformation::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nDistributions);
	m_pStream->Seek(offEndPos);
}

OutputStream *NiInformation::BeginChild(const char *szName) {
	if (strcmp(szName, "ni_distribution") == 0) {
		++m_nDistributions;
		return m_pStream;
	}
	return NULL;
}

bool ProteinSummaryDataFilter::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ProteinSummaryDataFilter.__init__(): ");
	const XML_Char *predicted_num_correct = Attr(pszAttrs, "predicted_num_correct");
	const XML_Char *predicted_num_incorrect = Attr(pszAttrs, "predicted_num_incorrect");
	WRITE_STRUCTURE(m_pStream, 4, (double, double, double, BYTE), (AS_DOUBLE(Attr(pszAttrs, "min_probability")), AS_DOUBLE(Attr(pszAttrs, "sensitivity")), AS_DOUBLE(Attr(pszAttrs, "false_positive_error_rate")), ENCODE_OPTIONAL(predicted_num_correct, predicted_num_incorrect)));
	if (predicted_num_correct != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(predicted_num_correct));
	}
	if (predicted_num_incorrect != NULL) {
		m_pStream->WriteDouble(AS_DOUBLE(predicted_num_incorrect));
	}
	return true;
}

bool ProteinprophetDetails::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ProteinprophetDetails.__init__(): ");
	m_offStartPos = m_pStream->Tell();
	const XML_Char *run_options = Attr(pszAttrs, "run_options");
	WRITE_STRUCTURE(m_pStream, 3, (DWORD, WORD, BYTE), (0, 0, YNBit(Attr(pszAttrs, "occam_flag"), 0x80) | YNBit(Attr(pszAttrs, "groups_flag"), 0x40) | YNBit(Attr(pszAttrs, "degen_flag"), 0x20) | YNBit(Attr(pszAttrs, "nsp_flag"), 0x10) | ENCODE_OPTIONAL(run_options)));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "initial_peptide_wt_iters"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "final_peptide_wt_iters"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "nsp_distribution_iters"));
	if (run_options != NULL) {
		EncodeStringToFile(m_pStream, Attr(pszAttrs, "run_options"));
	}
	m_nFilters = 0;
	m_pNI = NULL;
	m_pFilter = NULL;
	m_nState = 0;
	return true;
}

void ProteinprophetDetails::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	WRITE_STRUCTURE(m_pStream, 2, (DWORD, WORD), (offEndPos - m_offStartPos, m_nFilters));
	m_pStream->Seek(offEndPos);
	if (m_pNI != NULL) {
		m_pStream->WriteStream(m_pNI);
	}
	if (m_pFilter != NULL) {
		m_pStream->WriteStream(m_pFilter);
	}
}

OutputStream *ProteinprophetDetails::BeginChild(const char *szName) {
	if (strcmp(szName, "nsp_information") == 0) {
		m_nState = 1;
		return m_pStream;
	} else if (strcmp(szName, "ni_information") == 0) {
		if (m_nState == 1) {
			m_nState = 2;
			return m_pStream;
		} else {
			m_pNI = new MemoryStream();
			return m_pNI;
		}
	} else if (strcmp(szName, "protein_summary_data_filter") == 0) {
		++m_nFilters;
		if (m_nState == 2) {
			return m_pStream;
		} else if (m_nState == 1) {
			if (m_pNI != NULL) {
				m_pStream->WriteStream(m_pNI);
				delete m_pNI;
				m_pNI = NULL;
				if (m_pFilter != NULL) {
					m_pStream->WriteStream(m_pFilter);
					delete m_pFilter;
					m_pFilter = NULL;
				}
				return m_pStream;
			}
		}
		if (m_pFilter == NULL) {
			m_pFilter = new MemoryStream();
		}
		return m_pFilter;
	}
	return NULL;
}

bool ProgramDetails::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ProgramDetails.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "analysis"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "time"));
	//EncodeStringToFile(m_pStream, Attr(pszAttrs, "version"));
	m_pStream->WriteWord(0);
	m_offStartPos = m_pStream->Tell();
	m_nDetails = 0;
	return true;
}

void ProgramDetails::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nDetails);
	m_pStream->Seek(offEndPos);
}

OutputStream *ProgramDetails::BeginChild(const char *szName) {
	BYTE nType = strcmp(szName, "proteinprophet_details") == 0 ? 0 : 0xFF;
	if (nType == 0xFF) {
		printf("Unknown details type %s\n", szName);
		return NullStream();
	}
	m_pStream->WriteByte(nType);
	++m_nDetails;
	return m_pStream;
}

bool DataFilter::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "DataFilter.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "number"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "parent_file"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "description"));
	return true;
}

bool DatasetDerivation::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "DatasetDerivation.__init__(): ");
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "generation_no"));
	m_pStream->WriteWord(0);
	m_offStartPos = m_pStream->Tell();
	m_nFilters = 0;
	return true;
}

void DatasetDerivation::End() {
	off_t offEndPos = m_pStream->Tell();
	m_pStream->Seek(m_offStartPos);
	m_pStream->WriteWord(m_nFilters);
	m_pStream->Seek(offEndPos);
}

OutputStream *DatasetDerivation::BeginChild(const char *szName) {
	if (strcmp(szName, "data_filter") == 0) {
		++m_nFilters;
		return m_pStream;
	}
	return NULL;
}

bool AnalysisSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "AnalysisSummary.__init__(): ");
	//m_pStream->WriteByte(GetEngineCode(Attr(pszAttrs, "analysis")));
	return true;
}

OutputStream *AnalysisSummary::BeginChild(const char *szName) {
	return NullStream();
}

bool ProteinSummaryHeader::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ProteinSummaryHeader.__init__(): ");
	const XML_Char *win_cyg_reference_database = Attr(pszAttrs, "win_cyg_reference_database");
	const XML_Char *residue_substitution_list = Attr(pszAttrs, "residue_substitution_list");
	const XML_Char *organism = Attr(pszAttrs, "organism");
	const XML_Char *win_cyg_source_files = Attr(pszAttrs, "win_cyg_source_files");
	const XML_Char *source_file_xtn = Attr(pszAttrs, "source_file_xtn");
	const XML_Char *total_no_spectrum_ids = Attr(pszAttrs, "total_no_spectrum_ids");
	WRITE_STRUCTURE(m_pStream, 10, (double, double, double, double, int, int, int, int, int, BYTE), (AS_FLOAT(Attr(pszAttrs, "min_peptide_probability")), AS_FLOAT(Attr(pszAttrs, "min_peptide_probability")), AS_FLOAT(Attr(pszAttrs, "num_predicted_correct_prots")), AS_FLOAT(Attr(pszAttrs, "initial_min_peptide_prob")), AS_INT(Attr(pszAttrs, "num_input_1_spectra")), AS_INT(Attr(pszAttrs, "num_input_2_spectra")), AS_INT(Attr(pszAttrs, "num_input_3_spectra")), AS_INT(Attr(pszAttrs, "num_input_4_spectra")), AS_INT(Attr(pszAttrs, "num_input_5_spectra")), ENCODE_OPTIONAL(win_cyg_reference_database, residue_substitution_list, organism, win_cyg_source_files, source_file_xtn, total_no_spectrum_ids)));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "reference_database"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "source_files"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "source_files_alt"));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "sample_enzyme"));
	if (win_cyg_reference_database != NULL) {
		EncodeStringToFile(m_pStream, win_cyg_reference_database);
	}
	if (residue_substitution_list != NULL) {
		EncodeStringToFile(m_pStream, residue_substitution_list);
	}
	if (organism != NULL) {
		EncodeStringToFile(m_pStream, organism);
	}
	if (win_cyg_source_files != NULL) {
		EncodeStringToFile(m_pStream, win_cyg_source_files);
	}
	if (source_file_xtn != NULL) {
		EncodeStringToFile(m_pStream, source_file_xtn);
	}
	if (total_no_spectrum_ids != NULL) {
		EncodeStringToFile(m_pStream, total_no_spectrum_ids);
	}
	return true;
}

OutputStream *ProteinSummaryHeader::BeginChild(const char *szName) {
	if (strcmp(szName, "program_details") == 0) {
		return m_pStream;
	}
	return NULL;
}

bool ProteinSummary::Begin(State *pState, const XML_Char **pszAttrs) {
	TRACEPOS(m_pStream, "ProteinSummary.__init__(): ");
	m_pState = pState;
	m_offStartPos = m_pStream->Tell();
	WRITE_STRUCTURE(m_pStream, 3, (WORD, WORD, WORD), (0, 0, 0));
	EncodeStringToFile(m_pStream, Attr(pszAttrs, "summary_xml"));
	m_nGroups = 0;
	m_nDatasets = 0;
	m_nSummaries = 0;
	m_pProteinSummaryHeader = new MemoryStream();
	m_pDatasetDerivation = NULL;
	m_pAnalysisSummary = NULL;
	return true;
}

void ProteinSummary::End() {
	m_pStream->WriteStream(m_pProteinSummaryHeader);
	delete m_pProteinSummaryHeader;
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
	WRITE_STRUCTURE(m_pStream, 3, (WORD, WORD, WORD), (m_nGroups, m_nDatasets, m_nSummaries));
	m_pStream->Seek(offEndPos);
}

OutputStream *ProteinSummary::BeginChild(const char *szName) {
	if (strcmp(szName, "protein_group") == 0) {
		++m_nGroups;
		return m_pStream;
	} else if (strcmp(szName, "protein_summary_header") == 0) {
		return m_pProteinSummaryHeader;
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
	{ "peptide", &Peptide::New },
	{ "annotation", &Annotation::New },
	{ "protein", &Protein::New },
	{ "parameter", &Parameter::New },
	{ "protein_group", &ProteinGroup::New },
	{ "peptide_parent_protein", &PeptideParentProtein::New },
	{ "mod_aminoacid_mass", &ModAminoacidMass::New },
	{ "modification_info", &ModificationInfo::New },
	{ "indistinguishable_protein", &IndistinguishableProtein::New },
	{ "indistinguishable_peptide", &IndistinguishablePeptide::New },
	{ "protein_summary_data_filter", &ProteinSummaryDataFilter::New },
	{ "nsp_distribution", &NspDistribution::New },
	{ "ni_distribution", &NiDistribution::New },
	{ "nsp_information", &NspInformation::New },
	{ "ni_information", &NiInformation::New },
	{ "protein_summary_header", &ProteinSummaryHeader::New },
	{ "analysis_summary", &AnalysisSummary::New },
	{ "protein_summary", &ProteinSummary::New },
	{ "proteinprophet_details", &ProteinprophetDetails::New },
	{ "program_details", &ProgramDetails::New },
	{ "dataset_derivation", &DatasetDerivation::New },
	{ "analysis_result", &AnalysisResult::New },
	{ "data_filter", &DataFilter::New }
TAG_HANDLERS_END()