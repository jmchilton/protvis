#ifndef __HANDLERS_H__
	#define __HANDLERS_H__

	#include <string.h>
	#include "scorestream.h"
	#include "peptideindex.h"
	#include "../common/handlers.h"

	typedef struct _State : public BaseState {
		PeptideIndex<DWORD> Peptides;
		DWORD QueryOffset;
		WORD IncludedScores;

		_State(char *szFilePath) : BaseState(szFilePath), IncludedScores(0) { }
	} State;

	class Specificity : public TagHandler {
		/*struct Specificity {
			char sense; //C or N
			BYTE OptionalFlags;
			String cut;
			String min_spacing; //ONLY IF (OptionalFlags & 0x01)
			String no_cut; //ONLY IF (OptionalFlags & 0x02)
		}*/
		TAG_HANDLER(Specificity)
	};

	class SampleEnzyme : public TagHandler {
		/*struct SampleEnzyme {
			BYTE Flags; (Flags & 0x3): 0 = specific, 1 = semispecific, 2 = nonspecific; (Flags & 0xC): 0 = not independent, 4 = independent, 8 = not specified; (Flags & 0x10): has description
			String name;
			String description; //ONLY IF (Flags & 0x10)
			WORD specificity__count;
			Specificity specificity;
		}*/
		TAG_HANDLER(SampleEnzyme)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offCountPos;
			WORD m_nSpecificities;
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

	class AlternativeProtein : public TagHandler {
		/*struct AlternativeProtein {
			BYTE OptionalFlags;
			String protein;
			String protein_descr; //ONLY IF (OptionalFlags & 0x01)
			int num_tol_term; //ONLY IF (OptionalFlags & 0x02)
			double protein_mw; //ONLY IF (OptionalFlags & 0x04)
		}*/
		TAG_HANDLER(AlternativeProtein)
	};

	class SearchScoreSummary : public TagHandler {
		/*struct SearchScoreSummary {
			WORD parameter__count;
			Parameter parameter[parameter__count];
		}*/
		TAG_HANDLER(SearchScoreSummary)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);
	};

	class PeptideprophetResult : public TagHandler {
		/*//Deprecated
		struct PeptideprophetResult {
			float probability;
			BYTE OptionalFlags;
			String all_ntt_prob; //ONLY IF (OptionalFlags & 0x01)
			String analysis; //ONLY IF (OptionalFlags & 0x02)
			SearchScoreSummary search_score_summary; //ONLY IF (OptionalFlags & 0x04)
		}*/
		TAG_HANDLER(PeptideprophetResult)
		virtual OutputStream *BeginChild(const char *szName);
	};
	
	class InterprophetResult : public TagHandler {
		/*//Deprecated
		struct InterprophetResult {
			float probability;
			BYTE OptionalFlags;
			String all_ntt_prob; //ONLY IF (OptionalFlags & 0x01)
			String analysis; //ONLY IF (OptionalFlags & 0x02)
			SearchScoreSummary search_score_summary; //ONLY IF (OptionalFlags & 0x04)
		}*/
		TAG_HANDLER(InterprophetResult)
		virtual OutputStream *BeginChild(const char *szName);
	};
	
	class AsapratioResult : public TagHandler {
		TAG_HANDLER(AsapratioResult)
	};
	
	class XpressratioResult : public TagHandler {
		TAG_HANDLER(XpressratioResult)
	};

	class AnalysisResult : public TagHandler {
		/*struct AnalysisResult {
			BYTE OptionalFlags; //0x01 for peptideprophet, 0x02 for interprophet, 0x04 for asapratio, 0x08 for xpressratio
			float peptideprophet_probability; //ONLY IF (OptionalFlags & 0x01)
			float interprophet_probability; //ONLY IF (OptionalFlags & 0x02)
			float asapratio_probability; //ONLY IF (OptionalFlags & 0x04)
			float xpressratio_probability; //ONLY IF (OptionalFlags & 0x08)
		}
		//Deprecated
		struct AnalysisResult {
			String analysis;
			//DWORD id;
			WORD peptideprophet_result__count;
			WORD interprophet_result__count;
			WORD asapratio_result__count;
			WORD xpressratio_result__count;
			PeptideprophetResult peptideprophet_result;
			InterprophetResult interprophet_result;
			AsapratioResult asapratio_result;
			XpressratioResult xpressratio_result;
		}*/
		TAG_HANDLER(AnalysisResult)
		virtual OutputStream *BeginChild(const char *szName);
	};

	class SearchScore : public TagHandler {
		/*struct SearchScore {
			WORD OptionalFlags;
			double bvalue; //ONLY IF (OptionalFlags & 0x01)
			double expect; //ONLY IF (OptionalFlags & 0x02)
			double homologyscore; //ONLY IF (OptionalFlags & 0x04)
			double hyperscore; //ONLY IF (OptionalFlags & 0x08)
			double identityscore; //ONLY IF (OptionalFlags & 0x10)
			double ionscore; //ONLY IF (OptionalFlags & 0x20)
			double nextscore; //ONLY IF (OptionalFlags & 0x40)
			double pvalue; //ONLY IF (OptionalFlags & 0x80)
			double star; //ONLY IF (OptionalFlags & 0x100)
			double yscore; //ONLY IF (OptionalFlags & 0x200)
			float pp_prob; //ONLY IF (OptionalFlags & 0x400)
			float ip_prob; //ONLY IF (OptionalFlags & 0x800)
			float ap_prob; //ONLY IF (OptionalFlags & 0x1000)
			float ep_prob; //ONLY IF (OptionalFlags & 0x2000)
		}*/
		TAG_HANDLER(SearchScore)
	};

	class SearchHit : public TagHandler {
		/*struct SearchHit {
			DWORD RecordSize; //Size in bytes of this record, not including this 4 byte value
			WORD modification_info__count;
			WORD alternative_protein__count;
			//WORD analysis_result__count;
			DWORD DataOffset;
			double calc_neutral_pep_mass;
			double massdiff;
			WORD OptionalFlags; //0x8000 = is_rejected=1
			BYTE num_tot_proteins;
			String peptide;
			String protein;
			String protein_descr; //ONLY IF (OptionalFlags & 0x01)
			char peptide_prev_aa; //ONLY IF (OptionalFlags & 0x02)
			char peptide_next_aa; //ONLY IF (OptionalFlags & 0x04)
			BYTE num_matched_ions; //ONLY IF (OptionalFlags & 0x08)
			DWORD tot_num_ions; //ONLY IF (OptionalFlags & 0x10)
			//BYTE is_rejected;
			//WORD hit_rank;
			int num_tol_term; //ONLY IF (OptionalFlags & 0x20)
			int num_missed_cleavages; //ONLY IF (OptionalFlags & 0x40)
			String calc_pI; //ONLY IF (OptionalFlags & 0x80)
			double protein_mw; //ONLY IF (OptionalFlags & 0x100)
			SearchScore search_score;
			Modification modification_info[modification_info__count];
			Alternative alternative_protein[alternative_protein__count];
			//AnalysisResult analysis_result[analysis_result__count];
			//Parameter parameter[];
		}*/
		TAG_HANDLER(SearchHit)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			ScoreStream m_colScores;
			off_t m_offStartPos;
			State *m_pState;
			MemoryStream *m_pModInfos;
			MemoryStream *m_pAltProts;
			WORD m_nModCount;
			WORD m_nAltCount;
	};

	class SearchResult : public TagHandler {
		/*struct SearchResult {
			//int search_id;
			DWORD search_hit__count;
			SearchHit search_hit[search_hit__count];
		}*/
		TAG_HANDLER(SearchResult)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			DWORD m_nSearchHits;
	};

	class SearchDatabase : public TagHandler {
		/*struct SearchDatabase {
			BYTE Flags; //Flags & 0x80: 0 = AA, 0x80 = NA
			String local_path;
			//BYTE type
			String URL; //ONLY IF (Flags & 0x01)
			String database_name; //ONLY IF (Flags & 0x02)
			String orig_database_url; //ONLY IF (Flags & 0x04)
			String database_release_date; //ONLY IF (Flags & 0x08)
			String database_release_identifier; //ONLY IF (Flags & 0x10)
			int size_in_db_entries; //ONLY IF (Flags & 0x20)
			int size_of_residues; //ONLY IF (Flags & 0x40)
		}*/
		TAG_HANDLER(SearchDatabase)
	};

	class DistributionPoint : public TagHandler {
		/*struct DistributionPoint {
			flaot fvalue;
			int obs_1_distr;
			float model_1_pos_distr;
			float model_1_neg_distr;
			int obs_2_distr;
			float model_2_pos_distr;
			float model_2_neg_distr;
			int obs_3_distr;
			float model_3_pos_distr;
			float model_3_neg_distr;
		}*/
		TAG_HANDLER(DistributionPoint)
	};

	class EnzymaticSearchConstraint : public TagHandler {
		/*struct EnzymaticSearchConstraint {
			String enzyme;
			int max_num_internal_cleavages;
			int min_number_termini;
		}*/
		TAG_HANDLER(EnzymaticSearchConstraint)
	};

	class SequenceSearchConstraint : public TagHandler {
		/*struct SequenceSearchConstraint {
			String sequence;
		}*/
		TAG_HANDLER(SequenceSearchConstraint)
	};

	class AminoacidModification : public TagHandler {
		/*struct AminoacidModification {
			String aminoacid;
			String massdiff;
			float mass;
			String variable;
			BYTE OptionalFlags;
			String peptide_terminus; //ONLY IF (OptionalFlags & 0x01)
			String symbol; //ONLY IF (OptionalFlags & 0x02)
			String binary; //ONLY IF (OptionalFlags & 0x04)
			String description; //ONLY IF (OptionalFlags & 0x08)
		}*/
		TAG_HANDLER(AminoacidModification)
	};

	class TerminalModification : public TagHandler {
		TAG_HANDLER(TerminalModification)
	};

	class Parameter : public TagHandler {
		/*struct Parameter {
			BYTE OptionalFlags
			String name;
			String value
			String type; //ONLY IF (OptionalFlags & 0x01)
		}*/
		TAG_HANDLER(Parameter)
	};

	class SearchSummary : public TagHandler {
		/*enum MassType {
			monoisotopic,
			average
		}
		struct SearchSummary {
			BYTE OptionalFlags;
			//MassType precursor_mass_type; //OptionalFlags & 0x80: 0 = monoisotopic, 0x80 = average
			//MassType fragment_mass_type; //OptionalFlags & 0x40: 0 = monoisotopic, 0x40 = average
			String base_name;
			String search_engine;
			//unsigned int search_id;
			String out_data_type; //ONLY IF (OptionalFlags & 0x01)
			String out_data; //ONLY IF (OptionalFlags & 0x02)
			SearchDatabase search_database; //ONLY IF (OptionalFlags & 0x04)
			EnzymaticSearchConstraint enzymatic_search_constraint; //ONLY IF (OptionalFlags & 0x08)
			WORD sequence_search_constraint__count;
			WORD aminoacid_modification__count;
			WORD terminal_modification__count;
			WORD parameter__count;
			SequenceSearchConstraint sequence_search_constraint[sequence_search_constraint__count];
			AminoacidModification aminoacid_modification[aminoacid_modification__count];
			TerminalModification terminal_modification[terminal_modification__count];
			Parameter parameter[parameter__count];
		}*/
		TAG_HANDLER(SearchSummary)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			const XML_Char *m_out_data_type;
			const XML_Char *m_out_data;
			MemoryStream *m_pSearchDatabase;
			MemoryStream *m_pEnzymaticSearchConstraint;
			WORD m_nSequenceSearchConstraintCount;
			WORD m_nAminoacidModificationCount;
			WORD m_nTerminalModificationCount;
			WORD m_nParameterCount;
			MemoryStream *m_pSequenceSearchConstraint;
			MemoryStream *m_pAminoacidModification;
			MemoryStream *m_pTerminalModification;
			MemoryStream *m_pParameter;
	};

	class DatabaseRefreshTimestamp : public TagHandler {
		/*struct DatabaseRefreshTimestamp {
			BYTE OptionalFlags;
			String database;
			int min_num_enz_term; //ONLY IF (OptionalFlags & 0x01)
		}*/
		TAG_HANDLER(DatabaseRefreshTimestamp)
	};

	class XpressratioTimestamp : public TagHandler {
		/*struct XpressratioTimestamp {
			int xpress_light;
		}*/
		TAG_HANDLER(XpressratioTimestamp)
	};

	class AnalysisTimestamp : public TagHandler {
		/*struct AnalysisTimestamp {
			String time;
			String analysis;
			int id;
			WORD database_refresh_timestamp__count;
			WORD xpressratio_timestamp__count;
			DatabaseRefreshTimestamp database_refresh_timestamp[database_refresh_timestamp__count];
			XpressratioTimestamp xpressratio_timestamp[xpressratio_timestamp__count];
		}*/
		TAG_HANDLER(AnalysisTimestamp)
		virtual OutputStream *BeginChild(const char *szName);
	};

	class SpectrumQuery : public TagHandler {
		/*struct SpectrumQuery {
			DWORD RecordSize;
			DWORD search_result__offset;
			WORD search_result__count;
			BYTE OptionalFlags;
			unsigned int start_scan;
			unsigned int end_scan;
			float precursor_neutral_mass;
			int assumed_charge;
			unsigned int index;
			String spectrum;
			float retention_time_sec; //ONLY IF (OptionalFlags & 0x01)
			String search_specification; //ONLY IF (OptionalFlags & 0x02)
			SearchResult search_result[search_result__count];
		}*/
		TAG_HANDLER(SpectrumQuery)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			off_t m_offResultsPos;
			WORD m_nSearchResults;
	};

	class MsmsRunSummary : public TagHandler {
		/*struct MsmsRunSummary {
			DWORD RecordSize; //Size in bytes of this record, not including this 4 byte value
			DWORD spectrum_query__count;
			DWORD spectrum_query__offset;
			DWORD OtherDataOffset;
			BYTE OptionalFlags;
			String base_name;
			String raw_data_type;
			String raw_data;
			String msManufacturer; //ONLY IF (OptionalFlags & 0x01)
			String msModel; //ONLY IF (OptionalFlags & 0x02)
			String msIonization; //ONLY IF (OptionalFlags & 0x04)
			String msMassAnalyzer; //ONLY IF (OptionalFlags & 0x08)
			String msDetector; //ONLY IF (OptionalFlags & 0x10)
			SpectrumQuery spectrum_query[spectrum_query__count];
			SampleEnzyme sample_enzyme;
			SearchSummary search_summary;
			//AnalysisTimestamp analysis_timestamp[];
		}*/
		TAG_HANDLER(MsmsRunSummary)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			off_t m_offQueriesPos;
			MemoryStream *m_pSampleEnzyme;
			MemoryStream *m_pSearchSummary;
			DWORD m_nSpectrumQueries;
	};

	class DatasetDerivation : public TagHandler {
		TAG_HANDLER(DatasetDerivation)
	};

	class Point : public TagHandler {
		TAG_HANDLER(Point)
	};

	class PosmodelDistribution : public TagHandler {
		/*enum Type {
			NotSpecified
			discrete,
			gaussian,
			extremevalue,
			gamma,
			evd
		}
		struct PosmodelDistribution {
			WORD parameter__count;
			Type type;
			Parameter parameter[parameter__count];
		}*/
		TAG_HANDLER(PosmodelDistribution)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);
		
		private:
			off_t m_offStartPos;
			WORD m_nParams;
	};

	class NegmodelDistribution : public TagHandler {
		/*enum Type {
			NotSpecified
			discrete,
			gaussian,
			extremevalue,
			gamma,
			evd
		}
		struct NegmodelDistribution {
			WORD parameter__count;
			Type type;
			Parameter parameter[parameter__count];
		}*/
		TAG_HANDLER(NegmodelDistribution)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);
		
		private:
			off_t m_offStartPos;
			WORD m_nParams;
	};

	class MixturemodelDistribution : public TagHandler {
		/*struct MixturemodelDistribution {
			String name;
			PosmodelDistribution posmodel_distribution;
			NegmodelDistribution negmodel_distribution;
		}*/
		TAG_HANDLER(MixturemodelDistribution)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			MemoryStream *m_pNegDist;
			bool m_bHadPos;
	};

	class Mixturemodel : public TagHandler {
		/*struct Mixturemodel {
			WORD mixturemodel_distribution__count;
			//int precursor_ion_charge;
			//float prior_probability;
			//String comments;
			//String est_tot_correct;
			//String tot_num_spectra;
			//String num_iterations;
			MixturemodelDistribution mixturemodel_distribution[mixturemodel_distribution__count];
		}*/
		TAG_HANDLER(Mixturemodel)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nModels;
	};
		
	class Inputfile : public TagHandler {
		TAG_HANDLER(Inputfile)
	};
		
	class RocDataPoint : public TagHandler {
		TAG_HANDLER(RocDataPoint)
	};
		
	class ErrorPoint : public TagHandler {
		TAG_HANDLER(ErrorPoint)
	};
		
	class InteractSummary : public TagHandler {
		TAG_HANDLER(InteractSummary)
		virtual OutputStream *BeginChild(const char *szName);
	};

	class AnalysisSummary : public TagHandler {
		/*enum EngineCode {
			Unknown,
			interprophet,
			HaveVersion = 0x80
		}
		struct AnalysisSummary {
			DWORD RecordSize;
			WORD peptideprophet_summary__count;
			WORD interact_summary__count;
			WORD libra_summary__count;
			WORD asapratio_summary__count;
			WORD xpressratio_summary__count;
			WORD inputfile__count;
			WORD roc_data_point__count;
			WORD error_point__count;
			WORD mixture_model__count;
			EngineCode analysis;
			String time;
			String version; //ONLY IF (EngineCode & 0x80)
			PeptideprophetSummary peptideprophet_summary[peptideprophet_summary__count];
			InteractSummary interact_summary[interact_summary__count];
			LibraSummary libra_summary[libra_summary__count];
			AsapratioSummary asapratio_summary[asapratio_summary__count];
			XpressratioSummary xpressratio_summary[xpressratio_summary__count];
			Inputfile inputfile[inputfile__count];
			RocDataPoint roc_data_point[roc_data_point__count];
			ErrorPoint error_point[error_point__count];
			MixtureModel mixture_model[mixture_model__count];
		}*/
		TAG_HANDLER(AnalysisSummary)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			off_t m_offStartPos;
			WORD m_nPeptides;
			WORD m_nInteracts;
			WORD m_nLibras;
			WORD m_nAsaps;
			WORD m_nXpresss;
			WORD m_nFiles;
			WORD m_nRocs;
			WORD m_nErrors;
			WORD m_nMixtures;
			MemoryStream *m_pInteract;
			MemoryStream *m_pLibra;
			MemoryStream *m_pAsap;
			MemoryStream *m_pXpress;
			MemoryStream *m_pFile;
			MemoryStream *m_pRoc;
			MemoryStream *m_pError;
			MemoryStream *m_pMixture;
	};

	class MsmsPipelineAnalysis : public TagHandler {
		/*struct MsmsPipelineAnalysis {
			WORD IncludedScores;
			WORD msms_run_summary__count;
			WORD dataset_derivation__count;
			WORD analysis_summary__count;
			String summary_xml;
			String date;
			//String name; //ONLY IF (OptionalFlags & 0x01)
			MsmsRunSummary msms_run_summary[msms_run_summary__count];
			DatasetDerivation dataset_derivation[dataset_derivation__count];
			AnalysisSummary analysis_summary[analysis_summary__count];
		}*/
		TAG_HANDLER(MsmsPipelineAnalysis)
		virtual void End();
		virtual OutputStream *BeginChild(const char *szName);

		private:
			State *m_pState;
			off_t m_offStartPos;
			WORD m_nRuns;
			WORD m_nDatasets;
			WORD m_nSummaries;
			MemoryStream *m_pDatasetDerivation;
			MemoryStream *m_pAnalysisSummary;
	};

	void EncodePeptides(State &state);

#endif
