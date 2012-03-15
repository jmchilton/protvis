#ifndef __HANDLERS_H__
	#define __HANDLERS_H__

	#include <string.h>
	#include "../common/handlers.h"

	typedef struct _State : public BaseState {
		_State(char *szFilePath) : BaseState(szFilePath) { }
	} State;

	class Parameter : public TagHandler {
		/*struct Parameter {
			String name;
			String value;
		}*/
		TAG_HANDLER(Parameter)
	};

	class ModAminoacidMass : public TagHandler {
		/*struct ModAminoacidMass {
			unsigned int position;
			double mass;
		}*/
		TAG_HANDLER(ModAminoacidMass)
	};

	class ModificationInfo : public TagHandler {
		/*struct ModificationInfo {
			WORD mod_aminoacid_mass__count;
			BYTE OptionalFlags;
			//String modified_peptide; //ONLY IF (OptionalFlags & 0x04)
			double mod_nterm_mass; //ONLY IF (OptionalFlags & 0x01)
			double mod_cterm_mass; //ONLY IF (OptionalFlags & 0x02)
			ModAminoacidMass mod_aminoacid_mass[mod_aminoacid_mass__count];
		}*/
		TAG_HANDLER(ModificationInfo)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nMassCount;
	};

	class Annotation : public TagHandler {
		/*struct Annotation {
			BYTE OptionalFlags;
			String protein_description;
			String ipi_name; //ONLY IF (OptionalFlags & 0x01)
			String refseq_name; //ONLY IF (OptionalFlags & 0x02)
			String swissprot_name; //ONLY IF (OptionalFlags & 0x04)
			String ensembl_name; //ONLY IF (OptionalFlags & 0x08)
			String trembl_name; //ONLY IF (OptionalFlags & 0x10)
			String locus_link_name; //ONLY IF (OptionalFlags & 0x20)
			String flybase; //ONLY IF (OptionalFlags & 0x40)
		}*/
		TAG_HANDLER(Annotation)
	};

	class AnalysisResult : public TagHandler {
		/*struct AnalysisResult {
			WORD info__count;
			DWORD id;
			String analysis;
			Object info[info__count];
		}*/
		TAG_HANDLER(AnalysisResult)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nInfos;
	};

	class PeptideParentProtein : public TagHandler {
		/*//Deprecated
		struct PeptideParentProtein {
			String protein_name;
		}*/
		TAG_HANDLER(PeptideParentProtein)
	};
	
	class IndistinguishableProtein : public TagHandler {
		/*struct IndistinguishableProtein {
			WORD parameter__count; MSB set when Annotation included
			String protein_name;
			Annotation annotation; //ONLY IF (parameter__count & 0x8000)
			Parameter parameter[parameter__count & 0x7FFF];
		}*/
		TAG_HANDLER(IndistinguishableProtein)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			MemoryStream *m_pParameter;
			off_t m_offStartPos;
			WORD m_nParameters;
	};
	
	class IndistinguishablePeptide : public TagHandler {
		/*struct IndistinguishablePeptide {
			String peptide_sequence;
			WORD modification_info__count;
			ModificationInfo modification_info[modification_info__count];
		}*/
		TAG_HANDLER(IndistinguishablePeptide)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nModifications;
	};
	
	class Peptide : public TagHandler {
		/*struct Peptide {
			WORD modification_info__count;
			WORD parameter__count;
			WORD peptide_parent_protein__count;
			WORD indistinguishable_peptide__count;
			DWORD charge;
			DWORD n_enzymatic_termini;
			double initial_probability;
			double weight; //default to 1.0
			int n_sibling_peptides_bin; //default to 0
			int n_instances;
			WORD OptionalFlags; //0x8000 for is_nondegenerate_evidence == "Y", 0x4000 for is_contributing_evidence == "Y"
			String peptide_sequence;
			double nsp_adjusted_probability; //ONLY IF (OptionalFlags & 0x01)
			double ni_adjusted_probability; //ONLY IF (OptionalFlags & 0x02)
			double exp_sibling_ion_instances; //ONLY IF (OptionalFlags & 0x04)
			double exp_sibling_ion_bin; //ONLY IF (OptionalFlags & 0x08)
			double exp_tot_instances; //ONLY IF (OptionalFlags & 0x10)
			double n_enzymatic_termini; //ONLY IF (OptionalFlags & 0x20)
			double calc_neutral_pep_mass; //ONLY IF (OptionalFlags & 0x40)
			String peptide_group_designator; //ONLY IF (OptionalFlags & 0x80)
			ModificationInfo modification_info[modification_info__count];
			Parameter parameter[parameter__count];
			PeptideParentProtein peptide_parent_protein[peptide_parent_protein__count];
			IndistinguishablePeptide indistinguishable_peptide[indistinguishable_peptide__count];
		}*/
		TAG_HANDLER(Peptide)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			MemoryStream *m_pParameter;
			MemoryStream *m_pParent;
			MemoryStream *m_pIndistinguishable;
			off_t m_offStartPos;
			WORD m_nModifications;
			WORD m_nParameters;
			WORD m_nParents;
			WORD m_nIndistinguishables;
	};

	class Protein : public TagHandler {
		/*struct Protein {
			BYTE OptionalFlags;
			WORD peptide__count;
			WORD analysis_result__count;
			WORD indistinguishable_protein__count;
			WORD parameter__count;
			double probability;
			int n_indistinguishable_proteins;
			String protein_name;
			String group_sibling_id;
			double percent_coverage; //ONLY IF (OptionalFlags & 0x01)
			int total_number_peptides; //ONLY IF (OptionalFlags & 0x02)
			String subsuming_protein_entry; //ONLY IF (OptionalFlags & 0x04)
			String pct_spectrum_ids; //ONLY IF (OptionalFlags & 0x08)
			//String unique_stripped_peptides; //ONLY IF (OptionalFlags & 0x10)
			Peptide peptide[peptide__count];
			Annotation annotation; //ONLY IF (OptionalFlags & 0x20)
			Parameter parameter[parameter__count];
			AnalysisResult analysis_result[analysis_result__count];
			IndistinguishableProtein indistinguishable_protein[indistinguishable_protein__count];
		}*/
		TAG_HANDLER(Protein)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			MemoryStream *m_pAnnotation;
			MemoryStream *m_pResult;
			MemoryStream *m_pProtein;
			MemoryStream *m_pParameter;
			off_t m_offStartPos;
			WORD m_nResults;
			WORD m_nProteins;
			WORD m_nPeptides;
			WORD m_nParameters;
			BYTE m_nFlags;
	};

	class ProteinGroup : public TagHandler {
		/*struct ProteinGroup {
			double probability;
			WORD protein__count;
			BYTE OptionalFlags;
			String group_number;
			String pseudo_name; //ONLY IF (OptionalFlags & 0x01)
			Protein protein[protein__count];
		}*/
		TAG_HANDLER(ProteinGroup)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nProteins;
	};

	class NspDistribution : public TagHandler {
		/*struct NspDistribution {
			int bin_no;
			double pos_freq;
			double neg_freq;
			double pos_to_neg_ratio;
			BYTE OptionalFlags;
			double nsp_lower_bound_incl; //ONLY IF (OptionalFlags & 0x01)
			String nsp_upper_bound_excl; //ONLY IF (OptionalFlags & 0x02)
			double nsp_lower_bound_excl; //ONLY IF (OptionalFlags & 0x04)
			String nsp_upper_bound_incl; //ONLY IF (OptionalFlags & 0x08)
			double alt_pos_to_neg_ratio; //ONLY IF (OptionalFlags & 0x10)
		}*/
		TAG_HANDLER(NspDistribution)
	};

	class NiDistribution : public TagHandler {
		/*struct NiDistribution {
			int bin_no;
			double pos_freq;
			double neg_freq;
			double pos_to_neg_ratio;
			BYTE OptionalFlags;
			double ni_lower_bound_incl; //ONLY IF (OptionalFlags & 0x01)
			String ni_upper_bound_excl; //ONLY IF (OptionalFlags & 0x02)
			double ni_lower_bound_excl; //ONLY IF (OptionalFlags & 0x04)
			String ni_upper_bound_incl; //ONLY IF (OptionalFlags & 0x08)
			double alt_pos_to_neg_ratio; //ONLY IF (OptionalFlags & 0x10)
		}*/
		TAG_HANDLER(NiDistribution)
	};

	class NspInformation : public TagHandler {
		/*struct NspInformation {
			String neighboring_bin_smoothing;
			WORD nsp_distribution;
			NspDistribution nsp_distribution[nsp_distribution__count];
		}*/
		TAG_HANDLER(NspInformation)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nDistributions;
	};

	class NiInformation : public TagHandler {
		/*struct NiInformation {
			//String neighboring_bin_smoothing;
			WORD ni_distribution;
			NiDistribution ni_distribution[ni_distribution__count];
		}*/
		TAG_HANDLER(NiInformation)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nDistributions;
	};

	class ProteinSummaryDataFilter : public TagHandler {
		/*struct ProteinSummaryDataFilter {
			double min_probability;
			double sensitivity;
			double false_positive_error_rate;
			BYTE OptionalFlags;
			double predicted_num_correct; //ONLY IF (OptionalFlags & 0x01)
			double predicted_num_incorrect; //ONLY IF (OptionalFlags & 0x02)
		}*/
		TAG_HANDLER(ProteinSummaryDataFilter)
	};

	class ProteinprophetDetails : public TagHandler {
		/*struct ProteinprophetDetails {
			DWORD RecordSize;
			WORD protein_summary_data_filter__count;
			BYTE Flags; //0x80 for occam_flag="Y", 0x40 for groups_flag="Y", 0x20 for degen_flag="Y", 0x10 for nsp_flag="Y"
			String initial_peptide_wt_iters;
			String final_peptide_wt_iters;
			String nsp_distribution_iters;
			String run_options; //ONLY IF (Flags & 0x01)
			NspInformation nsp_information;
			NiInformation ni_information;
			ProteinSummaryDataFilter protein_summary_data_filter[protein_summary_data_filter__count];
		}*/
		TAG_HANDLER(ProteinprophetDetails)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			MemoryStream *m_pNI;
			MemoryStream *m_pFilter;
			off_t m_offStartPos;
			WORD m_nFilters;
			WORD m_nState;
	};

	class ProgramDetails : public TagHandler {
		/*struct Details {
			BYTE Type;
			Object detail;
		}
		struct ProgramDetails {
			String analysis;
			String time;
			//String version; //ONLY IF (OptionalFlags & 0x01)
			WORD details__count;
			Details details[details__count];
		}*/
		TAG_HANDLER(ProgramDetails)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

	private:
		off_t m_offStartPos;
		WORD m_nDetails;
	};

	class DataFilter : public TagHandler {
		/*struct DataFilter {
			String number;
			String parent_file;
			String description;
			//String windows_parent; //ONLY IF (OptionalFlags & 0x01)
		}*/
		TAG_HANDLER(DataFilter)
	};

	class DatasetDerivation : public TagHandler {
		/*struct DatasetDerivation {
			String generation_no;
			WORD data_filter__count;
			DataFilter data_filter[data_filter__count];
		}*/
		TAG_HANDLER(DatasetDerivation)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nFilters;
	};

	class AnalysisSummary : public TagHandler {
		TAG_HANDLER(AnalysisSummary)
		virtual OutputStream *BeginChild(const char *szName);
	};

	class ProteinSummaryHeader : public TagHandler {
		/*struct ProteinSummaryHeader {
			double min_peptide_probability;
			double min_peptide_probability;
			double num_predicted_correct_prots;
			double initial_min_peptide_prob;
			int num_input_1_spectra;
			int num_input_2_spectra;
			int num_input_3_spectra;
			int num_input_4_spectra;
			int num_input_5_spectra;
			BYTE OptionalFlags;
			String reference_database;
			String source_files;
			String source_files_alt;
			String sample_enzyme;
			String win_cyg_reference_database; //ONLY IF (OptionalFlags & 0x01)
			String residue_substitution_list; //ONLY IF (OptionalFlags & 0x02)
			String organism; //ONLY IF (OptionalFlags & 0x04)
			String win_cyg_source_files; //ONLY IF (OptionalFlags & 0x08)
			String source_file_xtn; //ONLY IF (OptionalFlags & 0x10)
			double total_no_spectrum_ids; //ONLY IF (OptionalFlags & 0x20)
			ProgramDetails program_details;
		}*/
		TAG_HANDLER(ProteinSummaryHeader)
		virtual OutputStream *BeginChild(const char *szName);
	};

	class ProteinSummary : public TagHandler {
		/*struct ProteinSummary {
			WORD protein_group__count;
			WORD dataset_derivation__count;
			WORD analysis_summary__count;
			String summary_xml;
			ProteinGroup protein_group[protein_group__count];
			ProteinSummaryHeader protein_summary_header;
			DatasetDerivation dataset_derivation[dataset_derivation__count];
			AnalysisSummary analysis_summary[analysis_summary__count];
		}*/
		TAG_HANDLER(ProteinSummary)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			State *m_pState;
			MemoryStream *m_pProteinSummaryHeader;
			MemoryStream *m_pDatasetDerivation;
			MemoryStream *m_pAnalysisSummary;
			off_t m_offStartPos;
			WORD m_nGroups;
			WORD m_nDatasets;
			WORD m_nSummaries;
	};

#endif
