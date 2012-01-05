#!/usr/bin/python

#pepXML definition at http://www.ncbi.nlm.nih.gov/IEB/ToolBox/CPP_DOC/lxr/source/src/algo/ms/formats/pepxml/pepXML.xsd

import struct
import os
import xml.sax
import xml.parsers.expat
from cStringIO import StringIO
from CommonXML import *

#Util functions
def GetEngineCode(name):
	if name == "interprophet":
		return 1
	return 0 #unknown

#Encoding Info
class EncodingStatus:
	def __init__(self, links):
		self.IncludedScores = 0
		self.Peptides = {}
		self.QueryOffset = 0
		self.Links = links

	def AddPeptide(self, peptide, hit_offset):
		try:
			self.Peptides[peptide].append([hit_offset, self.QueryOffset])
		except:
			self.Peptides[peptide] = [[hit_offset, self.QueryOffset]]

	def GetLink(name):
		try:
			return self.Links[name]
		except:
			return 0xFFFF


#Search results
class ResultType:
	Undefined = 0
	SpectrumQuery = 1
	SearchResult = 2
	SearchHit = 3
	SearchScore = 4
	Modification = 5
	
class Result:
	def __init__(self, Type = ResultType.Undefined, Query = -1, Hit = -1):
		self.Type = Type
		self.QueryOffset = Query
		self.HitOffset = Hit
		self.HitMatches = 0
		self.TotalMatches = 0
		self.HitInfo = None

	def __str__(self):
		fields = ["   Type: ", str(self.Type), "\n",
			"   QueryOffset: ", str(self.QueryOffset), "\n",
			"   HitOffset: ", str(self.HitOffset), "\n",
			"   TotalMatches: ", str(self.TotalMatches), "\n",
			"   HitInfo: ", str(self.HitInfo), "\n"]
		return "".join(fields)


#XML helpers
class SaxHandler(SaxHandlerBase):
	def __init__(self, stream, stat):
		SaxHandlerBase.__init__(self, stream, stat)
		self.Handlers = {
			"search_score": SearchScore,
			"parameter": Parameter,
			"search_hit": SearchHit,
			"mod_aminoacid_mass": ModAminoacidMass,
			"modification_info": ModificationInfo,
			"search_score_summary": SearchScoreSummary,
			"analysis_result": AnalysisResult,
			"spectrum_query": SpectrumQuery,
			"search_result": SearchResult,
			"peptideprophet_result": PeptideprophetResult,
			"interprophet_result": InterprophetResult,
			"asapratio_result": AsapratioResult,
			"xpressratio_result": XpressratioResult,
			"point": Point,
			"alternative_protein": AlternativeProtein,
			"aminoacid_modification": AminoacidModification,
			"analysis_timestamp": AnalysisTimestamp,
			"distribution_point": DistributionPoint,
			"roc_data_point": RocDataPoint,
			"error_point": ErrorPoint,
			"inputfile": Inputfile,
			"specificity": Specificity,
			"search_summary": SearchSummary,
			"search_database": SearchDatabase,
			"sample_enzyme": SampleEnzyme,
			"msms_run_summary": MsmsRunSummary,
			"enzymatic_search_constraint": EnzymaticSearchConstraint,
			"database_refresh_timestamp": DatabaseRefreshTimestamp,
			"posmodel_distribution": PosmodelDistribution,
     		"negmodel_distribution": NegmodelDistribution,
     		"mixturemodel_distribution": MixturemodelDistribution,
			"analysis_summary": AnalysisSummary,
			"mixture_model": Mixturemodel,
			"mixturemodel": Mixturemodel,
			"interact_summary": InteractSummary,
			"roc_error_data": RocErrorData,
			"peptideprophet_summary": PeptideprophetSummary,
			"msms_pipeline_analysis": MsmsPipelineAnalysis,
			"sequence_search_constraint": SequenceSearchConstraint,
			"terminal_modification": TerminalModification,
			"xpressratio_timestamp": XpressratioTimestamp,
			"dataset_derivation": DatasetDerivation }


#XML element classes
class Specificity(TagHandler):
	"""
	struct Specificity {
		char sense; //C or N
		BYTE OptionalFlags;
		String cut;
		String min_spacing; //ONLY IF (OptionalFlags & 0x01)
		String no_cut; //ONLY IF (OptionalFlags & 0x02)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "Specificity.__init__(): ")
		min_spacing = TryGet(attr, "min_spacing")
		no_cut = TryGet(attr, "no_cut")
		stream.write(struct.pack("=cB", str(attr["sense"]), EncodeOptional(min_spacing, no_cut)))
		EncodeStringToFile(stream, attr["cut"])
		if min_spacing != None:
			EncodeStringToFile(stream, min_spacing)
		if no_cut != None:
			EncodeStringToFile(stream, no_cut)

	#No need for end, there should be no child elements

class SampleEnzyme(TagHandler):
	"""
	struct SampleEnzyme {
		BYTE Flags; (Flags & 0x3): 0 = specific, 1 = semispecific, 2 = nonspecific; (Flags & 0xC): 0 = not independent, 4 = independent, 8 = not specified; (Flags & 0x10): has description
		String name;
		String description; //ONLY IF (Flags & 0x10)
		WORD specificity__count;
		Specificity specificity;
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SampleEnzyme.__init__(): ")
		Flags = 0x00
		try:
			fidelity = attr["fidelity"]
			if fidelity == "semispecific":
				Flags = 0x01
			elif semispecific == "nonspecific":
				Flags = 0x02
			#else Flags = 0x00
		except:
			Flags = 0x00
		try:
			independent = attr["independent"]
			if independent == "true":
				Flags |= 0x04
			#else Flags |= 0x00
		except:
			Flags |= 0x08
		description = TryGet(attr, "description")
		if description != None:
			Flags |= 0x10
		stream.write(struct.pack("=B", Flags))
		EncodeStringToFile(stream, attr["name"])
		if description != None:
			EncodeStringToFile(stream, description)
		self.CountPos = stream.tell()
		stream.write(struct.pack("=H", 0))
		self.Specificities = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.CountPos)
		self.Stream.write(struct.pack("=H", self.Specificities))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "specificity":
			self.Specificities += 1
			return self.Stream
		raise ValueError(name)

class ModAminoacidMass(TagHandler):
	"""
	struct ModAminoacidMass {
		unsigned int position;
		double mass;
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ModAminoAcidMass.__init__(): ")
		stream.write(struct.pack("=Id", int(attr["position"]), float(attr["mass"])))

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("ModAminoacidMass.SearchAll(", i, "): ", f.tell())
			[position, mass] = struct.unpack("=Id", f.read(4 + 8))
			stat.SearchItemInt("mod_aminoacid_position", position)
			stat.SearchItemFloat("mod_aminoacid_mass", mass)
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		return [struct.unpack("=Id", f.read(4 + 8)) for i in xrange(count)]

class ModificationInfo(TagHandler):
	"""
	struct ModificationInfo {
		WORD mod_aminoacid_mass__count;
		BYTE OptionalFlags;
		//String modified_peptide; //ONLY IF (OptionalFlags & 0x04)
		double mod_nterm_mass; //ONLY IF (OptionalFlags & 0x01)
		double mod_cterm_mass; //ONLY IF (OptionalFlags & 0x02)
		ModAminoacidMass mod_aminoacid_mass[mod_aminoacid_mass__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ModificationInfo.__init__(): ")
		self.StartPos = stream.tell()
		mod_nterm_mass = TryGet(attr, "mod_nterm_mass")
		mod_cterm_mass = TryGet(attr, "mod_cterm_mass")
		stream.write(struct.pack("=HB", 0, EncodeOptional(mod_nterm_mass, mod_cterm_mass)))
		if mod_nterm_mass != None:
			stream.write(struct.pack("=d", mod_nterm_mass))
		if mod_cterm_mass != None:
			stream.write(struct.pack("=d", mod_cterm_mass))
		self.MassCount = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.MassCount))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "mod_aminoacid_mass":
			self.MassCount += 1
			return self.Stream
		raise ValueError(name)

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("ModificationInfo.SearchAll(", i, "): ", f.tell())
			[mod_aminoacid_mass__count, OptionalFlags] = struct.unpack("=HB", f.read(2 + 1))
			if OptionalFlags & 0x01:
				stat.SearchItemFloat("mod_nterm_mass", struct.unpack("=d", f.read(8))[0])
			if OptionalFlags & 0x02:
				stat.SearchItemFloat("mod_cterm_mass", struct.unpack("=d", f.read(8))[0])
			ModAminoacidMass.SearchAll(f, stat, mod_aminoacid_mass__count)
			i += 1

	@staticmethod
	def GetInfo(f):
		[mod_aminoacid_mass__count, OptionalFlags] = struct.unpack("=HB", f.read(2 + 1))
		dic = {}
		if OptionalFlags & 0x01:
			dic["mod_nterm_mass"] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x02:
			dic["mod_cterm_mass"] = struct.unpack("=d", f.read(8))
		dic["mod_aminoacid_mass"] = ModAminoacidMass.GetInfoAll(f, mod_aminoacid_mass__count)

class AlternativeProtein(TagHandler):
	"""
	struct AlternativeProtein {
		BYTE OptionalFlags;
		String protein;
		String protein_descr; //ONLY IF (OptionalFlags & 0x01)
		int num_tol_term; //ONLY IF (OptionalFlags & 0x02)
		double protein_mw; //ONLY IF (OptionalFlags & 0x04)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "AlternativeProtein.__init__(): ")
		protein_descr = TryGet(attr, "protein_descr")
		num_tol_term = TryGet(attr, "num_tol_term")
		protein_mw = TryGet(attr, "protein_mw")
		stream.write(struct.pack("=B", EncodeOptional(protein_descr, num_tol_term, protein_mw)))
		EncodeStringToFile(stream, attr["protein"])
		if protein_descr != None:
			EncodeStringToFile(stream, protein_descr)
		if num_tol_term != None:
			stream.write(struct.pack("=i", int(num_tol_term)))
		if protein_mw != None:
			stream.write(struct.pack("=d", float(protein_mw)))

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("AlternativeProtein.SearchAll(", i, "): ", f.tell())
			[OptionalFlags] = struct.unpack("=B", f.read(1))
			stat.SearchItemString("alternative_protein", DecodeStringFromFile(f))
			if OptionalFlags & 0x01:
				stat.SearchItemString("alternative_protein_descr", DecodeStringFromFile(f))
			if OptionalFlags & 0x02:
				stat.SearchItemInt("alternative_num_tol_term", struct.unpack("=i", f.read(4))[0])
			if OptionalFlags & 0x04:
				stat.SearchItemFloat("alternative_protein_mw", struct.unpack("=d", f.read(8))[0])
			i += 1

	@staticmethod
	def GetInfo(f):
		[OptionalFlags] = struct.unpack("=B", f.read(1))
		dic = { "protein": DecodeStringFromFile(f) }
		if OptionalFlags & 0x01:
			dic["protein_descr"] = DecodeStringFromFile(f)
		if OptionalFlags & 0x02:
			[dic["num_tol_term"]] = struct.unpack("=i", f.read(4))
		if OptionalFlags & 0x04:
			[dic["protein_mw"]] = struct.unpack("=d", f.read(8))
		return dic

class SearchScoreSummary(TagHandler):
	"""
	struct SearchScoreSummary {
		WORD parameter__count;
		Parameter parameter[parameter__count];
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SearchScoreSummary.__init__(): ")
		"""self.ParamCount = 0
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))"""

	def End(self):
		"""EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.ParamCount))
		self.Stream.seek(EndPos)"""

	def BeginChild(self, name):
		"""if name == "parameter":
			self.ParamCount += 1
			return self.Stream
		raise ValueError(name)"""
		return self.Stream

	@staticmethod
	def GetInfoAll(f):
		"""[count] = struct.unpack("=H", f.read(2))
		return Parameter.GetInfoAll(f, count)"""
		return None

class PeptideprophetResult(TagHandler):
	"""//Deprecated
	struct PeptideprophetResult {
		float probability;
		BYTE OptionalFlags;
		String all_ntt_prob; //ONLY IF (OptionalFlags & 0x01)
		String analysis; //ONLY IF (OptionalFlags & 0x02)
		SearchScoreSummary search_score_summary; //ONLY IF (OptionalFlags & 0x04)
	}
	"""

	"""def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "PeptideprophetResult.__init__(): ")
		all_ntt_prob = TryGet(attr, "all_ntt_prob")
		analysis = TryGet(attr, "analysis")
		self.OptionalFlags = EncodeOptional(all_ntt_prob, analysis)
		self.OptionalPos = stream.tell() + 4
		stream.write(struct.pack("=fB", float(attr["probability"]), 0))
		if all_ntt_prob != None:
			EncodeStringToFile(stream, all_ntt_prob)
		if analysis != None:
			EncodeStringToFile(stream, analysis)

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.OptionalPos)
		self.Stream.write(struct.pack("=B", self.OptionalFlags))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "search_score_summary":
			if self.OptionalFlags & 0x04:
				raise IndexError("search_score_summary[1]")
			self.OptionalFlags |= 0x04
			return self.Stream
		raise ValueError(name)

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		i = 0
		results = []
		while i < count:
			TRACEPOS("PeptideprophetResult.GetInfoAll(", i, "): ", f.tell())
			[probability, OptionalFlags] = struct.unpack("=fB", f.read(4 + 1))
			res = { "probability": probability }
			if OptionalFlags & 0x01:
				res["all_ntt_prob"] = DecodeStringFromFile(f)
			if OptionalFlags & 0x02:
				res["analysis"] = DecodeStringFromFile(f)
			if OptionalFlags & 0x04:
				res["search_score_summary"] = SearchScoreSummary.GetInfoAll(f)
			results.append(res)
			i += 1
		return results"""
	def __init__(self, stream, stat, attr):
		stream["pp_prob"] = attr["probability"]

	def BeginChild(self, name):
		if name == "search_score_summary":
			return NullStream()
		raise ValueError(name)
	
class InterprophetResult(TagHandler):
	"""//Deprecated
	struct InterprophetResult {
		float probability;
		BYTE OptionalFlags;
		String all_ntt_prob; //ONLY IF (OptionalFlags & 0x01)
		String analysis; //ONLY IF (OptionalFlags & 0x02)
		SearchScoreSummary search_score_summary; //ONLY IF (OptionalFlags & 0x04)
	}
	"""

	"""def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "InterprophetResult.__init__(): ")
		all_ntt_prob = TryGet(attr, "all_ntt_prob")
		analysis = TryGet(attr, "analysis")
		self.OptionalFlags = EncodeOptional(all_ntt_prob, analysis)
		self.OptionalPos = stream.tell() + 4
		stream.write(struct.pack("=fB", float(attr["probability"]), 0))
		if all_ntt_prob != None:
			EncodeStringToFile(stream, all_ntt_prob)
		if analysis != None:
			EncodeStringToFile(stream, analysis)

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.OptionalPos)
		self.Stream.write(struct.pack("=B", self.OptionalFlags))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "search_score_summary":
			if self.OptionalFlags & 0x04:
				raise IndexError("search_score_summary[1]")
			self.OptionalFlags |= 0x04
			return self.Stream
		raise ValueError(name)

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		i = 0
		results = []
		while i < count:
			TRACEPOS("InterprophetResult.GetInfoAll(", i, "): ", f.tell())
			[probability, OptionalFlags] = struct.unpack("=fB", f.read(4 + 1))
			res = { "probability": probability }
			if OptionalFlags & 0x01:
				res["all_ntt_prob"] = DecodeStringFromFile(f)
			if OptionalFlags & 0x02:
				res["analysis"] = DecodeStringFromFile(f)
			if OptionalFlags & 0x04:
				res["search_score_summary"] = SearchScoreSummary.GetInfoAll(f)
			results.append(res)
			i += 1
		return results"""
	
	def __init__(self, stream, stat, attr):
		stream["ip_prob"] = attr["probability"]

	def BeginChild(self, name):
		if name == "search_score_summary":
			return NullStream()
		raise ValueError(name)
	
class AsapratioResult(TagHandler):
	def __init__(self, stream, stat, attr):
		raise NotImplementedError("AsapratioResult")

	@staticmethod
	def SearchAll(f, stat, count):
		raise NotImplementedError("AsapratioResult")
		i = 0
		while i < count:
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		raise NotImplementedError("AsapratioResult")
		i = 0
		while i < count:
			i += 1
	
class XpressratioResult(TagHandler):
	def __init__(self, stream, stat, attr):
		raise NotImplementedError("XpressratioResult")

	@staticmethod
	def SearchAll(f, stat, count):
		raise NotImplementedError("XpressratioResult")
		i = 0
		while i < count:
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		raise NotImplementedError("XpressratioResult")
		i = 0
		while i < count:
			i += 1

class AnalysisResult(TagHandler):
	"""
	struct AnalysisResult {
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
	}
	"""

	"""def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "AnalysisResult.__init__(): ")
		EncodeStringToFile(stream, attr["analysis"])
		self.PPCount = 0
		self.IPCount = 0
		self.ARCount = 0
		self.XRCount = 0
		self.PeptideprophetResult = None
		self.InterprophetResult = None
		self.AsapratioResult = None
		self.XpressratioResult = None

	def End(self):
		self.Stream.write(struct.pack("=HHHH", self.PPCount, self.IPCount, self.ARCount, self.XRCount))
		if self.PeptideprophetResult != None:
			self.Stream.write(self.PeptideprophetResult.getvalue())
		if self.InterprophetResult != None:
			self.Stream.write(self.InterprophetResult.getvalue())
		if self.AsapratioResult != None:
			self.Stream.write(self.AsapratioResult.getvalue())
		if self.XpressratioResult != None:
			self.Stream.write(self.XpressratioResult.getvalue())

	def BeginChild(self, name):
		if name == "peptideprophet_result":
			if self.PeptideprophetResult == None:
				self.PeptideprophetResult = StringIO()
			self.PPCount += 1
			return self.PeptideprophetResult
		if name == "interprophet_result":
			if self.InterprophetResult == None:
				self.InterprophetResult = StringIO()
			self.IPCount += 1
			return self.InterprophetResult
		if name == "asapratio_result":
			if self.AsapratioResult == None:
				self.AsapratioResult = StringIO()
			self.ARCount += 1
			return self.AsapratioResult
		if name == "xpressratio_result":
			if self.XpressratioResult == None:
				self.XpressratioResult = StringIO()
			self.XRCount += 1
			return self.XpressratioResult

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("AnalysisResult.SearchAll(", i, "): ", f.tell())
			DecodeStringFromFile(f) #FIXME: Search this?
			[peptideprophet_result__count, interprophet_result__count, asapratio_result__count, xpressratio_result__count] = struct.unpack("=HHHH", f.read(2 + 2 + 2 + 2))
			if peptideprophet_result__count > 0:
				PeptideprophetResult.SearchAll(f, stat, peptideprophet_result__count)
			if interprophet_result__count > 0:
				InterprophetResult.SearchAll(f, stat, interprophet_result__count)
			if asapratio_result__count > 0:
				AsapratioResult.SearchAll(f, stat, asapratio_result__count)
			if xpressratio_result__count > 0:
				XpressratioResult.SearchAll(f, stat, xpressratio_result__count)
			i += 1

	@staticmethod
	def GetInfo(f):
		TRACEPOS("AnalysisResult.GetInfo(): ", f.tell())
		info = {}
		info["analysis"] = DecodeStringFromFile(f)
		[peptideprophet_result__count, interprophet_result__count, asapratio_result__count, xpressratio_result__count] = struct.unpack("=HHHH", f.read(2 + 2 + 2 + 2))
		if peptideprophet_result__count > 0:
			info["peptideprophet_result"] = PeptideprophetResult.GetInfoAll(f, peptideprophet_result__count)
		if interprophet_result__count > 0:
			info["interprophet_result"] = InterprophetResult.GetInfoAll(f, interprophet_result__count)
		if asapratio_result__count > 0:
			info["asapratio_result"] = AsapratioResult.GetInfoAll(f, asapratio_result__count)
		if xpressratio_result__count > 0:
			info["xpressratio_result"] = XpressratioResult.GetInfoAll(f, xpressratio_result__count)
		return info"""
		
	def __init__(self, stream, stat, attr):
		self.Had = 0

	def BeginChild(self, name):
		if name == "peptideprophet_result":
			if self.Had & 0x01:
				raise IndexError("peptideprophet_result[1]")
			else:
				self.Had |= 0x01
			return self.Stream
		if name == "interprophet_result":
			if self.Had & 0x02:
				raise IndexError("interprophet_result[1]")
			else:
				self.Had |= 0x02
			return self.Stream
		if name == "asapratio_result":
			if self.Had & 0x04:
				raise IndexError("asapratio_result[1]")
			else:
				self.Had |= 0x04
			return self.Stream
		if name == "xpressratio_result":
			if self.Had & 0x08:
				raise IndexError("xpressratio_result[1]")
			else:
				self.Had |= 0x08
			return self.Stream

	"""@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("AnalysisResult.SearchAll(", i, "): ", f.tell())
			DecodeStringFromFile(f) #FIXME: Search this?
			[peptideprophet_result__count, interprophet_result__count, asapratio_result__count, xpressratio_result__count] = struct.unpack("=HHHH", f.read(2 + 2 + 2 + 2))
			if peptideprophet_result__count > 0:
				PeptideprophetResult.SearchAll(f, stat, peptideprophet_result__count)
			if interprophet_result__count > 0:
				InterprophetResult.SearchAll(f, stat, interprophet_result__count)
			if asapratio_result__count > 0:
				AsapratioResult.SearchAll(f, stat, asapratio_result__count)
			if xpressratio_result__count > 0:
				XpressratioResult.SearchAll(f, stat, xpressratio_result__count)
			i += 1

	@staticmethod
	def GetInfo(f):
		TRACEPOS("AnalysisResult.GetInfo(): ", f.tell())
		info = {}
		info["analysis"] = DecodeStringFromFile(f)
		[peptideprophet_result__count, interprophet_result__count, asapratio_result__count, xpressratio_result__count] = struct.unpack("=HHHH", f.read(2 + 2 + 2 + 2))
		if peptideprophet_result__count > 0:
			info["peptideprophet_result"] = PeptideprophetResult.GetInfoAll(f, peptideprophet_result__count)
		if interprophet_result__count > 0:
			info["interprophet_result"] = InterprophetResult.GetInfoAll(f, interprophet_result__count)
		if asapratio_result__count > 0:
			info["asapratio_result"] = AsapratioResult.GetInfoAll(f, asapratio_result__count)
		if xpressratio_result__count > 0:
			info["xpressratio_result"] = XpressratioResult.GetInfoAll(f, xpressratio_result__count)
		return info"""

class SearchScore(TagHandler):
	"""
	struct SearchScore {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		stream[attr["name"]] = attr["value"]

	@staticmethod
	def SearchAll(f, stat):
		TRACEPOS("SearchScore.SearchAll(): ", f.tell())
		[OptionalFlags] = struct.unpack("=H", f.read(2))
		results = {}
		if OptionalFlags & 0x01:
			[bvalue] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("bvalue", bvalue)
			results["bvalue"] = bvalue
		if OptionalFlags & 0x02:
			[expect] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("expect", expect)
			results["expect"] = expect
		if OptionalFlags & 0x04:
			[homologyscore] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("homologyscore", homologyscore)
			results["homologyscore"] = homologyscore
		if OptionalFlags & 0x08:
			[hyperscore] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("hyperscore", hyperscore)
			results["hyperscore"] = hyperscore
		if OptionalFlags & 0x10:
			[identityscore] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("identityscore", identityscore)
			results["identityscore"] = identityscore
		if OptionalFlags & 0x20:
			[ionscore] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("ionscore", ionscore)
			results["ionscore"] = ionscore
		if OptionalFlags & 0x40:
			[nextscore] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("nextscore", nextscore)
			results["nextscore"] = nextscore
		if OptionalFlags & 0x80:
			[pvalue] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("pvalue", pvalue)
			results["pvalue"] = pvalue
		if OptionalFlags & 0x100:
			[star] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("star", star)
			results["star"] = star
		if OptionalFlags & 0x200:
			[yscore] = struct.unpack("=d", f.read(8))
			stat.SearchItemFloat("yscore", yscore)
			results["yscore"] = yscore
		if OptionalFlags & 0x400:
			[pp_prob] = struct.unpack("=f", f.read(4))
			stat.SearchItemFloat("pp_prob", pp_prob)
			results["pp_prob"] = pp_prob
		if OptionalFlags & 0x800:
			ip_prob = struct.unpack("=f", f.read(4))
			stat.SearchItemFloat("ip_prob", ip_prob)
			results["ip_prob"] = ip_prob
		if OptionalFlags & 0x1000:
			ap_prob = struct.unpack("=f", f.read(4))
			stat.SearchItemFloat("ap_prob", ap_prob)
			results["ap_prob"] = ap_prob
		if OptionalFlags & 0x2000:
			ep_prob = struct.unpack("=f", f.read(4))
			stat.SearchItemFloat("ep_prob", ep_prob)
			results["ep_prob"] = ep_prob
		return results

	@staticmethod
	def GetInfo(f, dic):
		TRACEPOS("SearchScore.GetInfo(): ", f.tell())
		[OptionalFlags] = struct.unpack("=H", f.read(2))
		if OptionalFlags & 0x01:
			[dic["bvalue"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x02:
			[dic["expect"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x04:
			[dic["homologyscore"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x08:
			[dic["hyperscore"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x10:
			[dic["identityscore"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x20:
			[dic["ionscore"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x40:
			[dic["nextscore"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x80:
			[dic["pvalue"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x100:
			[dic["star"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x200:
			[dic["yscore"]] = struct.unpack("=d", f.read(8))
		if OptionalFlags & 0x400:
			[dic["pp_prob"]] = struct.unpack("=f", f.read(4))
		if OptionalFlags & 0x800:
			[dic["ip_prob"]] = struct.unpack("=f", f.read(4))
		if OptionalFlags & 0x1000:
			[dic["ap_prob"]] = struct.unpack("=f", f.read(4))
		if OptionalFlags & 0x2000:
			[dic["ep_prob"]] = struct.unpack("=f", f.read(4))

	@staticmethod
	def CompareHits(a, b):
		#returns:
		# >0 if b is better than a
		#  0 if b is equivelent to a
		# <0 if b is worse than a
		try:
			return a["ip_prob"] - b["ip_prob"] #interprophet probability
		except:
			try:
				return a["pp_prob"] - b["pp_prob"] #peptideprophet probability
			except:
				try:
					return a["hyperscore"] - b["hyperscore"] #x-tandem
				except:
					try:
						return a["ionscore"] - b["ionscore"] #mascot
					except:
						try:
							return a["expect"] - b["expect"] #omssa
						except:
							return 0 #unknown

	@staticmethod
	def KeyExpect(hit):
		return hit.HitInfo["expect"]
		

class SearchHit(TagHandler):
	"""
	struct SearchHit {
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
		DWORD cs; //ONLY IF (OptionalFlags & 0x10)
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SearchHit.__init__(): ")
		self.Stat = stat
		try:
			if attr["is_rejected"] == "1":
				Flags = 0x8000
			else:
				Flags = 0x0000
		except:
			Flags = 0x0000
		protein_descr = TryGet(attr, "protein_descr")
		peptide_prev_aa = TryGet(attr, "peptide_prev_aa")
		peptide_next_aa = TryGet(attr, "peptide_next_aa")
		num_matched_ions = TryGet(attr, "num_matched_ions")
		tot_num_ions = TryGet(attr, "tot_num_ions")
		num_tol_term = TryGet(attr, "num_tol_term")
		num_missed_cleavages = TryGet(attr, "num_missed_cleavages")
		calc_pI = TryGet(attr, "calc_pI")
		protein_mw = TryGet(attr, "protein_mw")
		Flags |= EncodeOptional(protein_descr, peptide_prev_aa, peptide_next_aa, num_matched_ions, tot_num_ions, num_tol_term, num_missed_cleavages, calc_pI, protein_mw)
		self.StartPos = stream.tell()
		stream.write(struct.pack("=IHHIddHB", 0, 0, 0, 0, float(attr["calc_neutral_pep_mass"]), float(attr["massdiff"]), Flags, int(attr["num_tot_proteins"])))
		TRACEPOSXML(stream, "SearchHit.__init__(peptide): ")
		peptide = attr["peptide"]
		stat.AddPeptide(peptide, self.StartPos)
		EncodeStringToFile(stream, peptide)
		EncodeStringToFile(stream, attr["protein"])
		if protein_descr != None:
			EncodeStringToFile(stream, protein_descr)
		if peptide_prev_aa != None:
			if len(peptide_prev_aa) == 0:
				stream.write(struct.pack("=B", 0))
			else:
				stream.write(struct.pack("=c", str(peptide_prev_aa)))
		if peptide_next_aa != None:
			if len(peptide_next_aa) == 0:
				stream.write(struct.pack("=B", 0))
			else:
				stream.write(struct.pack('=c', str(peptide_next_aa)))
		if num_matched_ions != None:
			stream.write(struct.pack("=B", int(num_matched_ions)))
		if tot_num_ions != None:
			stream.write(struct.pack("=I", int(tot_num_ions)))
		if num_tol_term != None:
			stream.write(struct.pack("=i", int(num_tol_term)))
		if num_missed_cleavages != None:
			stream.write(struct.pack("=i", int(num_missed_cleavages)))
		if calc_pI != None:
			EncodeStringToFile(stream, calc_pI)
		if protein_mw != None:
			stream.write(struct.pack("=d", protein_mw))
		DataOffset = stream.tell()
		stream.seek(self.StartPos + 4 + 2 + 2)
		stream.write(struct.pack("=I", DataOffset - self.StartPos))
		stream.seek(DataOffset)
		self.ModCount = 0
		self.AltCount = 0
		self.Scores = {}
		self.ModInfos = None
		self.AltProts = None

	def End(self):
		bvalue = TryGet(self.Scores, "bvalue")
		expect = TryGet(self.Scores, "expect")
		homologyscore = TryGet(self.Scores, "homologyscore")
		hyperscore = TryGet(self.Scores, "hyperscore")
		identityscore = TryGet(self.Scores, "identityscore")
		ionscore = TryGet(self.Scores, "ionscore")
		nextscore = TryGet(self.Scores, "nextscore")
		pvalue = TryGet(self.Scores, "pvalue")
		star = TryGet(self.Scores, "star")
		yscore = TryGet(self.Scores, "yscore")
		pp_prob = TryGet(self.Scores, "pp_prob")
		ip_prob = TryGet(self.Scores, "ip_prob")
		ap_prob = TryGet(self.Scores, "ap_prob")
		ep_prob = TryGet(self.Scores, "ep_prob")
		TRACEPOSXML(self.Stream, "SearchHit.End(SearchScore): ")
		Scores = EncodeOptional(bvalue, expect, homologyscore, hyperscore, identityscore, ionscore, nextscore, pvalue, star, yscore, pp_prob, ip_prob, ap_prob, ep_prob)
		self.Stat.IncludedScores |= Scores
		self.Stream.write(struct.pack("=H", Scores))
		if bvalue != None:
			self.Stream.write(struct.pack("=d", float(bvalue)))
		if expect != None:
			self.Stream.write(struct.pack("=d", float(expect)))
		if homologyscore != None:
			self.Stream.write(struct.pack("=d", float(homologyscore)))
		if hyperscore != None:
			self.Stream.write(struct.pack("=d", float(hyperscore)))
		if identityscore != None:
			self.Stream.write(struct.pack("=d", float(identityscore)))
		if ionscore != None:
			self.Stream.write(struct.pack("=d", float(ionscore)))
		if nextscore != None:
			self.Stream.write(struct.pack("=d", float(nextscore)))
		if pvalue != None:
			self.Stream.write(struct.pack("=d", float(pvalue)))
		if star != None:
			self.Stream.write(struct.pack("=d", float(star)))
		if yscore != None:
			self.Stream.write(struct.pack("=d", float(yscore)))
		if pp_prob != None:
			self.Stream.write(struct.pack("=f", float(pp_prob)))
		if ip_prob != None:
			self.Stream.write(struct.pack("=f", float(ip_prob)))
		if ap_prob != None:
			self.Stream.write(struct.pack("=f", float(ap_prob)))
		if ep_prob != None:
			self.Stream.write(struct.pack("=f", float(ep_prob)))
		if self.ModInfos != None:
			self.Stream.write(self.ModInfos.getvalue())
		if self.AltProts != None:
			self.Stream.write(self.AltProts.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IHH", EndPos - self.StartPos, self.ModCount, self.AltCount))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "search_score":
			return self.Scores
		elif name == "modification_info":
			self.ModCount += 1
			if self.ModInfos == None:
				self.ModInfos = StringIO()
			return self.ModInfos
		elif name == "alternative_protein":
			self.AltCount += 1
			if self.AltProts == None:
				self.AltProts = StringIO()
			return self.AltProts
		elif name == "analysis_result":
			return self.Scores
		raise ValueError(name)
		
	@staticmethod
	def SearchAllBestHit(f, stat, count):
		i = 0
		BestScore = None
		BestScorePos = -1
		Hits = 0
		while i < count:
			s = stat.copy()
			StartPos = f.tell()
			TRACEPOS("SearchHit.SearchAllBestHit(", i, "): ", f.tell())
			[RecordSize, modification_info__count, alternative_protein__count, DataOffset, calc_neutral_pep_mass, massdiff, OptionalFlags, num_tot_proteins] = struct.unpack("=IHHIddHB", f.read(4 + 2 + 2 + 4 + 8 + 8 + 2 + 1))
			peptide = DecodeStringFromFile(f)
			PeptideFull = peptide
			protein = DecodeStringFromFile(f)
			s.SearchItemString("Protein", protein)
			if OptionalFlags & 0x01:
				protein_descr = DecodeStringFromFile(f)
				s.SearchItemString("ProteinDescr", protein_descr)
			if OptionalFlags & 0x02:
				[peptide_prev_aa] = struct.unpack("=c", f.read(1))
				PeptideFull = peptide_prev_aa + PeptideFull
			if OptionalFlags & 0x04:
				[peptide_next_aa] = struct.unpack("=c", f.read(1))
				PeptideFull += peptide_next_aa
			"""if OptionalFlags & 0x08:
				[num_matched_ions] = struct.unpack("=B", f.read(1))
				#FIXME: Check?
			if OptionalFlags & 0x10:
				[tot_num_ions] = struct.unpack("=I", f.read(4))
				#FIXME: Check?
			if OptionalFlags & 0x20:
				[num_tol_term] = struct.unpack("=i", f.read(4))
				#FIXME: Check?
			if OptionalFlags & 0x40:
				[num_missed_cleavages] = struct.unpack("=i", f.read(4))
				#FIXME: Check?
			if OptionalFlags & 0x80:
				calc_pI = DecodeStringFromFile(f)
				#FIXME: Check?
			if OptionalFlags & 0x100:
				[protein_mw] = struct.unpack("=d", f.read(8))
				#FIXME: Check?"""
			f.seek(StartPos + DataOffset)
			score = SearchScore.SearchAll(f, s)
			if modification_info__count > 0:
				ModificationInfo.SearchAll(f, s, modification_info__count)
			if alternative_protein__count > 0:
				AlternativeProtein.SearchAll(f, s, alternative_protein__count)
			s.SearchItemString("Peptide", PeptideFull)
			if s.IsMatched():
				Hits += 1
				if BestScore == None or SearchScore.CompareHits(BestScore, score) > 0:
					BestScore = score
					BestScorePos = StartPos
			else:
				f.seek(StartPos + RecordSize)
			i += 1
		if BestScore != None:
			EndPos = f.tell()
			f.seek(BestScorePos)
			info = SearchHit.GetInfo(f)
			f.seek(EndPos)
			return [BestScorePos, Hits, info]
		return None

	@staticmethod
	def GetScores(f, offset):
		f.seek(offset + 4 + 2 + 2)
		[DataOffset] = struct.unpack("=I", f.read(4))
		f.seek(offset + DataOffset)
		results = {}
		SearchScore.GetInfo(f, results)
		return results

	@staticmethod
	def EatAll(f, count):
		i = 0
		while i < count:
			TRACEPOS("SearchHit.EatAll(", i, "): ", f.tell())
			f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1

	@staticmethod
	def GetInfo(f):
		TRACEPOS("SearchHit.GetInfo(): ", f.tell())
		[RecordSize, modification_info__count, alternative_protein__count, DataOffset, calc_neutral_pep_mass, massdiff, OptionalFlags, num_tot_proteins] = struct.unpack("=IHHIddHB", f.read(4 + 2 + 2 + 4 + 8 + 8 + 2 + 1))
		dic = {}
		dic["calc_neutral_pep_mass"] = calc_neutral_pep_mass
		dic["massdiff"] = massdiff
		dic["num_tot_proteins"] = num_tot_proteins
		TRACEPOS("SearchHit.GetInfo(peptide): ", f.tell())
		dic["peptide"] = DecodeStringFromFile(f)
		dic["protein"] = DecodeStringFromFile(f)
		if OptionalFlags & 0x01:
			dic["protein_descr"] = DecodeStringFromFile(f)
		if OptionalFlags & 0x02:
			[dic["peptide_prev_aa"]] = struct.unpack("=c", f.read(1))
		if OptionalFlags & 0x04:
			[dic["peptide_next_aa"]] = struct.unpack("=c", f.read(1))
		if OptionalFlags & 0x08:
			[dic["num_matched_ions"]] = struct.unpack("=B", f.read(1))
		if OptionalFlags & 0x10:
			[dic["tot_num_ions"]] = struct.unpack("=I", f.read(4))
		if OptionalFlags & 0x20:
			[dic["num_tol_term"]] = struct.unpack("=i", f.read(4))
		if OptionalFlags & 0x40:
			[dic["num_missed_cleavages"]] = struct.unpack("=i", f.read(4))
		if OptionalFlags & 0x80:
			dic["calc_pI"] = DecodeStringFromFile(f)
		if OptionalFlags & 0x100:
			[dic["protein_mw"]] = struct.unpack("=d", f.read(8))
		SearchScore.GetInfo(f, dic)
		dic["modification_info"] = [ModificationInfo.GetInfo(f) for i in xrange(modification_info__count)]
		dic["alternative_protein"] = [AlternativeProtein.GetInfo(f) for i in xrange(alternative_protein__count)]
		return dic

	@staticmethod
	def GetInfoFirstEatRest(f, count):
		TRACEPOS("SearchResult.GetInfoFirstEatRest(): ", f.tell())
		info = SearchHit.GetInfo(f)
		if count > 1:
			SearchHit.EatAll(f, count - 1)
		return info

	@staticmethod
	def GetInfoSeek(f, offset):
		f.seek(offset)
		TRACEPOS("SearchResult.GetInfoSeek(): ", offset)
		return SearchHit.GetInfo(f)

	@staticmethod
	def BestHitAndCountAll(hits, count):
		i = 0
		while i < count:
			Best = None
			TotalHits = 0
			for h in hits:
				if h != None:
					TotalHits += h[0]
					if Best == None or SearchScore.CompareHits(Best, h[1]) > 0:
						Best = h[1]
			return [TotalHits, Best]
			i += 1

class SearchResult(TagHandler):
	"""
	struct SearchResult {
		//int search_id;
		DWORD search_hit__count;
		SearchHit search_hit[search_hit__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SearchResult.__init__(): ")
		self.StartPos = stream.tell()
		stream.write(struct.pack("=I", 0))
		self.SearchHits = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=I", self.SearchHits))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "search_hit":
			self.SearchHits += 1
			return self.Stream
		raise ValueError(name)

	@staticmethod
	def SearchAllBestHitAndCount(f, stat, count):
		i = 0
		BestHitOffset = -1
		BestHitInfo = None
		BestHitMatches = 0
		BestHitTotal = 0
		while i < count:
			TRACEPOS("SearchResult.SearchAllBestHitAndCount(", i, "): ", f.tell())
			[search_hit__count] = struct.unpack("=I", f.read(4))
			r = SearchHit.SearchAllBestHit(f, stat, search_hit__count)
			if r != None:
				[off, hits, info] = r
				if BestHitInfo == None or SearchScore.CompareHits(BestHitInfo, info) > 0:
					BestHitOffset = off
					BestHitInfo = info
					BestHitMatches = hits
					BestHitTotal = search_hit__count
			i += 1
		return [BestHitOffset, BestHitMatches, BestHitTotal, BestHitInfo]

	@staticmethod
	def GetCount(f):
		TRACEPOS("SearchResult.GetCount(): ", f.tell())
		[search_hit__count] = struct.unpack("=I", f.read(4))
		return search_hit__count

	@staticmethod
	def GetCountAndEat(f):
		TRACEPOS("SearchResult.GetCountAndEat(): ", f.tell())
		[search_hit__count] = struct.unpack("=I", f.read(4))
		SearchHit.EatAll(f, search_hit__count)
		return search_hit__count

	@staticmethod
	def GetBestHitInfoAll(f, count):
		i = 0
		BestHitInfo = None
		TotalHits = 0
		BestHitOffset = 0
		while i < count:
			TRACEPOS("SearchResult.GetBestHitInfoAll(", i, "): ", f.tell())
			[search_hit__count] = struct.unpack("=I", f.read(4))
			offset = f.tell()
			info = SearchHit.GetInfoFirstEatRest(f, search_hit__count)
			TotalHits += search_hit__count
			if BestHitInfo == None or SearchScore.CompareHits(BestHitInfo, info) > 0:
				BestHitInfo = info
				BestHitOffset = offset
			i += 1
		return [BestHitOffset, TotalHits, BestHitInfo]
		"""#the best hit is always the first one in the list
		i = 0
		BestResultIndex = -1
		BestHitIndex = -1
		BestHitInfo = None
		TotalHits = 0
		while i < count:
			[search_hit__count] = struct.unpack("=I", f.read(4))
			[idx, info] = SearchHit.GetInfoBestAll(f, search_hit__count)
			TotalHits += search_hit__count
			if BestHitInfo == None or SearchScore.CompareHits(BestHitInfo, info) > 0:
				BestResultIndex = i
				BestHitIndex = idx
				BestHitInfo = info
			i += 1
		return [BestResultIndex, BestHitIndex, TotalHits, BestHitInfo]"""

class SearchDatabase(TagHandler):
	"""
	struct SearchDatabase {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SearchDatabase.__init__(): ")
		URL = TryGet(attr, "URL")
		database_name = TryGet(attr, "database_name")
		orig_database_url = TryGet(attr, "orig_database_url")
		database_release_date = TryGet(attr, "database_release_date")
		database_release_identifier = TryGet(attr, "database_release_identifier")
		size_in_db_entries = TryGet(attr, "size_in_db_entries")
		size_of_residues = TryGet(attr, "size_of_residues")
		OptionalFlags = EncodeOptional(URL, database_name, orig_database_url, database_release_date, database_release_identifier, size_in_db_entries, size_of_residues)
		if attr["type"] == "NA":
			OptionalFlags |= 0x80
		stream.write(struct.pack("=B", OptionalFlags))
		EncodeStringToFile(stream, attr["local_path"])
		if URL != None:
			EncodeStringToFile(stream, URL)
		if database_name != None:
			EncodeStringToFile(stream, database_name)
		if orig_database_url != None:
			EncodeStringToFile(stream, orig_database_url)
		if database_release_date != None:
			EncodeStringToFile(stream, database_release_date)
		if database_release_identifier != None:
			EncodeStringToFile(stream, database_release_identifier)
		if size_in_db_entries != None:
			stream.write(struct.pack("=i", int(size_in_db_entries)))
		if size_of_residues != None:
			stream.write(struct.pack("=i", int(size_of_residues)))

class DistributionPoint(TagHandler):
	"""
	struct DistributionPoint {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "DistributionPoint.__init__(): ")
		stream.write(struct.pack("=fiffiffiff", float(attr["fvalue"]), int(attr["obs_1_distr"]), float(attr["model_1_pos_distr"]), float(attr["model_1_neg_distr"]), int(attr["obs_2_distr"]), float(attr["model_2_pos_distr"]), float(attr["model_2_neg_distr"]), int(attr["obs_3_distr"]), float(attr["model_3_pos_distr"]), float(attr["model_3_neg_distr"])))

class EnzymaticSearchConstraint(TagHandler):
	"""
	struct EnzymaticSearchConstraint {
		String enzyme;
		int max_num_internal_cleavages;
		int min_number_termini;
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "EnzymaticSearchConstraint.__init__(): ")
		EncodeStringToFile(stream, attr["enzyme"])
		stream.write(struct.pack("=ii", int(attr["max_num_internal_cleavages"]), int(attr["min_number_termini"])))

class SequenceSearchConstraint(TagHandler):
	"""
	struct SequenceSearchConstraint {
		String sequence;
	}
	"""

	def __init__(self, stream, stat, attr):
		EncodeStringToFile(stream, attr["sequence"])

class AminoacidModification(TagHandler):
	"""
	struct AminoacidModification {
		String aminoacid;
		String massdiff;
		float mass;
		String variable;
		BYTE OptionalFlags;
		String peptide_terminus; //ONLY IF (OptionalFlags & 0x01)
		String symbol; //ONLY IF (OptionalFlags & 0x02)
		String binary; //ONLY IF (OptionalFlags & 0x04)
		String description; //ONLY IF (OptionalFlags & 0x08)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "AminoacidModification.__init__(): ")
		EncodeStringToFile(stream, attr["aminoacid"])
		EncodeStringToFile(stream, attr["massdiff"])
		stream.write(struct.pack("=f", float(attr["mass"])))
		EncodeStringToFile(stream, attr["variable"])
		peptide_terminus = TryGet(attr, "peptide_terminus")
		symbol = TryGet(attr, "symbol")
		binary = TryGet(attr, "binary")
		description = TryGet(attr, "description")
		stream.write(struct.pack("=B", EncodeOptional(peptide_terminus, symbol, binary, description)))
		if peptide_terminus != None:
			EncodeStringToFile(stream, peptide_terminus)
		if symbol != None:
			EncodeStringToFile(stream, symbol)
		if binary != None:
			EncodeStringToFile(stream, binary)
		if description != None:
			EncodeStringToFile(stream, description)

class TerminalModification(TagHandler):
	def __init__(self, stream, stat, attr):
		print("NYI: TerminalModification") #FIXME: implement

class Parameter(TagHandler):
	"""
	struct Parameter {
		BYTE OptionalFlags
		String name;
		String value
		String type; //ONLY IF (OptionalFlags & 0x01)
	}
	"""

	def __init__(self, stream, stat, attr):
		"""t = TryGet(attr, "value")
		stream.write(struct.pack("=B", EncodeOptional(t)))
		EncodeStringToFile(stream, attr["name"])
		EncodeStringToFile(stream, attr["value"])
		if t != None:
			EncodeStringToFile(stream, t)"""
		return
		
	@staticmethod
	def SearchAll(f, stat, count, prepend):
		"""i = 0
		while i < count:
			[OptionalFlags] = struct.unpack("=B", f.read(1))
			stat.SearchItemString(prepend + "_name", DecodeStringFromFile(f))
			stat.SearchItemString(prepend + "_value", DecodeStringFromFile(f))
			if OptionalFlags & 0x01:
				stat.SearchItemString(prepend + "_type", DecodeStringFromFile(f))"""
		return

	@staticmethod
	def GetInfoAll(f, count):
		"""i = 0
		results = {}
		while i < count:
			[OptionalFlags] = struct.unpack("=B", f.read(1))
			results[DecodeStringFromFile(f)] = DecodeStringFromFile(f)
			if OptionalFlags & 0x01:
				DecodeStringFromFile(f) #we don't care about this
			i += 1
		return results"""

class SearchSummary(TagHandler):
	"""
	enum MassType {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SearchSummary.__init__(): ")
		self.StartPos = stream.tell()
		self.out_data_type = TryGet(xml, "out_data_type")
		self.out_data = TryGet(xml, "out_data")
		self.Stream.write(struct.pack("=B", 0))
		EncodeStringToFile(self.Stream, attr["base_name"])
		EncodeStringToFile(self.Stream, attr["search_engine"])
		if self.out_data_type != None:
			EncodeStringToFile(self.Stream, self.out_data_type)
		if self.out_data != None:
			EncodeStringToFile(self.Stream, self.out_data)
		self.SearchDatabase = None
		self.EnzymaticSearchConstraint = None
		self.SequenceSearchConstraintCount = 0
		self.AminoacidModificationCount = 0
		self.TerminalModificationCount = 0
		self.ParameterCount = 0
		self.SequenceSearchConstraint = None
		self.AminoacidModification = None
		self.TerminalModification = None
		self.Parameter = None

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=B", EncodeOptional(self.out_data_type, self.out_data, self.SearchDatabase, self.EnzymaticSearchConstraint)))
		self.Stream.seek(EndPos)
		if self.SearchDatabase != None:
			self.Stream.write(self.SearchDatabase.getvalue())
		if self.EnzymaticSearchConstraint != None:
			self.Stream.write(self.EnzymaticSearchConstraint.getvalue())
		self.Stream.write(struct.pack("=HHHH", self.SequenceSearchConstraintCount, self.AminoacidModificationCount, self.TerminalModificationCount, self.ParameterCount))
		if self.SequenceSearchConstraint != None:
			self.Stream.write(self.SequenceSearchConstraint.getvalue())
		if self.AminoacidModification != None:
			self.Stream.write(self.AminoacidModification.getvalue())
		if self.TerminalModification != None:
			self.Stream.write(self.TerminalModification.getvalue())
		if self.Parameter != None:
			self.Stream.write(self.Parameter.getvalue())

	def BeginChild(self, name):
		if name == "search_database":
			if self.SearchDatabase != None:
				raise IndexError()
			self.SearchDatabase = StringIO()
			return self.SearchDatabase
		if name == "enzymatic_search_constraint":
			if self.EnzymaticSearchConstraint != None:
				raise IndexError()
			self.EnzymaticSearchConstraint = StringIO()
			return self.EnzymaticSearchConstraint
		if name == "sequence_search_constraint":
			if self.SequenceSearchConstraint == None:
				self.SequenceSearchConstraint = StringIO()
			return self.SequenceSearchConstraint
		if name == "aminoacid_modification":
			if self.AminoacidModification == None:
				self.AminoacidModification = StringIO()
			return self.AminoacidModification
		if name == "terminal_modification":
			if self.TerminalModification == None:
				self.TerminalModification = StringIO()
			return self.TerminalModification
		if name == "parameter":
			if self.Parameter == None:
				self.Parameter = StringIO()
			return self.Parameter

class DatabaseRefreshTimestamp(TagHandler):
	"""
	struct DatabaseRefreshTimestamp {
		BYTE OptionalFlags;
		String database;
		int min_num_enz_term; //ONLY IF (OptionalFlags & 0x01)
	}
	"""

	def __init__(self, stream, stat, attr):
		"""min_num_enz_term = TryGet(attr, "min_num_enz_term")
		stream.write(struct.pack("=B", EncodeOptional(min_num_enz_term)))
		EncodeStringToFile(stream, attr["database"])
		stream.write(struct.pack("=i", int(min_num_enz_term)))"""
		return

class XpressratioTimestamp(TagHandler):
	"""
	struct XpressratioTimestamp {
		int xpress_light;
	}
	"""

	def __init__(self, stream, stat, attr):
		"""stream.write(struct.pack("=i", int(attr["xpress_light"])))"""
		return

class AnalysisTimestamp(TagHandler):
	"""
	struct AnalysisTimestamp {
		String time;
		String analysis;
		int id;
		WORD database_refresh_timestamp__count;
		WORD xpressratio_timestamp__count;
		DatabaseRefreshTimestamp database_refresh_timestamp[database_refresh_timestamp__count];
		XpressratioTimestamp xpressratio_timestamp[xpressratio_timestamp__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		#This data is excluded from the binary file
		return

	def BeginChild(self, name):
		#we don't care about this
		return None

class SpectrumQuery(TagHandler):
	"""
	struct SpectrumQuery {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SpectrumQuery.__init__(): ")
		self.StartPos = stream.tell()
		stat.QueryOffset = self.StartPos
		retention_time_sec = TryGet(attr, "retention_time_sec")
		search_specification = TryGet(attr, "search_specification")
		stream.write(struct.pack("=IIHBIIfiI", 0, 0, 0, EncodeOptional(retention_time_sec, search_specification), int(attr["start_scan"]), int(attr["end_scan"]), float(attr["precursor_neutral_mass"]), int(attr["assumed_charge"]), int(attr["index"])))
		EncodeStringToFile(stream, attr["spectrum"])
		if retention_time_sec != None:
			stream.write(struct.pack("=f", float(retention_time_sec)))
		if search_specification != None:
			EncodeStringToFile(stream, search_specification)
		self.ResultsPos = stream.tell()
		self.SearchResults = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IIH", EndPos - self.StartPos, self.ResultsPos - self.StartPos, self.SearchResults))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "search_result":
			self.SearchResults += 1
			return self.Stream
		raise ValueError(name)
		
	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			s = stat.copy()
			TRACEPOS("SpectrumQuery.SearchAll(", i, "): ", f.tell())
			StartPos = f.tell()
			[RecordSize, _, search_result__count, OptionalFlags, _1, _2, precursor_neutral_mass, _3, _4] = struct.unpack("=IIHBIIfiI", f.read(4 + 4 + 2 + 1 + 4 + 4 + 4 + 4 + 4))
			spectrum = DecodeStringFromFile(f)
			s.SearchItemFloat("NeutralMass", precursor_neutral_mass)
			retention_time_sec = None
			search_specification = None
			if OptionalFlags & 0x01:
				retention_time_sec = struct.unpack("=f", f.read(4))
				s.SearchItemFloat("RetentionTime", retention_time_sec)
			if OptionalFlags & 0x02:
				search_specification = DecodeStringFromFile(f)
				s.SearchItemString("SearchSpec", search_specification)
			result = None
			if s.IsMatched():
				result = Result(ResultType.SpectrumQuery)
				[result.HitOffset, result.TotalHits, result.HitInfo] = SearchResult.GetBestHitInfoAll(f, search_result__count)
				result.HitMatches = result.TotalHits
			else:
				[off, matches, total, info] = SearchResult.SearchAllBestHitAndCount(f, s, search_result__count)
				if info != None:
					result = Result(ResultType.SearchHit)
					result.HitOffset = off
					result.HitMatches = matches
					result.TotalHits = total
					result.HitInfo = info
			if result != None:
				result.precursor_neutral_mass = precursor_neutral_mass
				result.retention_time_sec = retention_time_sec
				result.search_specification = search_specification
				result.QueryOffset = StartPos
				stat.Results.append(result)
			i += 1

	@staticmethod
	def GetScores(f, qoff, hoff):
		f.seek(qoff + 4 + 4 + 2 + 1 + 4 + 4 + 4 + 4 + 4)
		spectrum = DecodeStringFromFile(f)
		results = SearchHit.GetScores(f, hoff)
		return [spectrum, results]

	@staticmethod
	def GetHitInfoSeek(f, query, hit):
		f.seek(query + 4 + 4 + 2 + 1 + 4 + 4 + 4 + 4 + 4)
		spectrum = DecodeStringFromFile(f)
		dic = SearchHit.GetInfoSeek(f, hit)
		dic["spectrum"] = spectrum
		return dic


class MsmsRunSummary(TagHandler):
	"""
	struct MsmsRunSummary {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "MsmsRunSummary.__init__(): ")
		self.StartPos = stream.tell()
		msManufacturer = TryGet(attr, "msManufacturer")
		msModel = TryGet(attr, "msModel")
		msIonization = TryGet(attr, "msIonization")
		msMassAnalyzer = TryGet(attr, "msMassAnalyzer")
		msDetector = TryGet(attr, "msDetector")
		stream.write(struct.pack("=IIIIB", 0, 0, 0, 0, EncodeOptional(msManufacturer, msModel, msIonization, msMassAnalyzer, msDetector)))
		EncodeStringToFile(stream, attr["base_name"])
		EncodeStringToFile(stream, attr["raw_data_type"])
		EncodeStringToFile(stream, attr["raw_data"])
		if msManufacturer != None:
			EncodeStringToFile(stream, msManufacturer)
		if msModel != None:
			EncodeStringToFile(stream, msModel)
		if msIonization != None:
			EncodeStringToFile(stream, msIonization)
		if msMassAnalyzer != None:
			EncodeStringToFile(stream, msMassAnalyzer)
		if msDetector != None:
			EncodeStringToFile(stream, msDetector)
		self.QueriesPos = stream.tell()
		self.SampleEnzyme = None
		self.SearchSummary = None
		self.SpectrumQueries = 0

	def End(self):
		OtherDataOffset = self.Stream.tell()
		self.Stream.write(self.SampleEnzyme.getvalue())
		self.Stream.write(self.SearchSummary.getvalue())
		#AnalysisTimestamp
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IIII", EndPos - self.StartPos, self.SpectrumQueries, self.QueriesPos - self.StartPos, OtherDataOffset - self.StartPos))
		self.Stream.seek(EndPos)
	
	def BeginChild(self, name):
		if name == "sample_enzyme":
			self.SampleEnzyme = StringIO()
			return self.SampleEnzyme
		elif name == "search_summary":
			self.SearchSummary = StringIO()
			return self.SearchSummary
		elif name == "spectrum_query":
			self.SpectrumQueries += 1
			return self.Stream
		elif name == "analysis_timestamp":
			return NullStream()
		raise ValueError(name)
		
	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("MsmsRunSummary.SearchAll(", i, "): ", f.tell())
			StartPos = f.tell()
			[RecordSize, spectrum_query__count, spectrum_query__offset] = struct.unpack("=III", f.read(4 + 4 + 4))
			f.seek(StartPos + spectrum_query__offset)
			SpectrumQuery.SearchAll(f, stat.copy(), spectrum_query__count)
			stat.TotalQueries += spectrum_query__count
			f.seek(StartPos + RecordSize)
			i += 1

class DatasetDerivation(TagHandler):
	def __init__(self, stream, stat, attr):
		return
		
	@staticmethod
	def SearchAll(f, dic, count):
		i = 0
		while i < count:
			print("NYI: DatasetDerivation.Search") #FIXME: Implement
			i += 1

class Point(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return

class PosmodelDistribution(TagHandler):
	"""
	enum Type {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "PosmodelDistribution.__init__(): ")
		Types = { None: 0, "discrete": 1, "gaussian": 2, "extremevalue": 3, "gamma": 4, "evd": 5, "non-parametric": 6 }
		self.StartPos = stream.tell()
		stream.write(struct.pack("=HB", 0, Types[TryGet(attr, "type")]))
		self.Params = 0
		
	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Params))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "parameter":
			self.Params = 1
			return self.Stream
		raise ValueError(name)
		
class NegmodelDistribution(TagHandler):
	"""
	enum Type {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "NegmodelDistribution.__init__(): ")
		Types = { None: 0, "discrete": 1, "gaussian": 2, "extremevalue": 3, "gamma": 4, "evd": 5, "non-parametric": 6 }
		self.StartPos = stream.tell()
		stream.write(struct.pack("=HB", 0, Types[TryGet(attr, "type")]))
		self.Params = 0
		
	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Params))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "parameter":
			self.Params = 1
			return self.Stream
		raise ValueError(name)
		
class MixturemodelDistribution(TagHandler):
	"""
	struct MixturemodelDistribution {
		String name;
		PosmodelDistribution posmodel_distribution;
		NegmodelDistribution negmodel_distribution;
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "MixturemodelDistribution.__init__(): ")
		EncodeStringToFile(stream, attr["name"])
		self.HadPos = 0
		self.NegDist = None
		
	def End(self):
		if self.HadPos == 0:
			raise IndexError()
		if self.NegDist != None:
			self.Stream.write(self.NegDist.getvalue())

	def BeginChild(self, name):
		if name == "posmodel_distribution":
			self.HadPos = 1
			return self.Stream
		elif name == "negmodel_distribution":
			if self.HadPos > 0:
				return self.Stream
			self.NegDist = StringIO()
			return self.NegDist
		raise ValueError(name)

class Mixturemodel(TagHandler):
	"""
	struct Mixturemodel {
		WORD mixturemodel_distribution__count;
		/*int precursor_ion_charge;
		float prior_probability;
		String comments;
		String est_tot_correct;
		String tot_num_spectra;
		String num_iterations;*/
		MixturemodelDistribution mixturemodel_distribution[mixturemodel_distribution__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "Mixturemodel.__init__(): ")
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))
		"""stream.write(struct.pack("=Hif", 0, attr["precursor_ion_charge"], attr["prior_probability"]))
		EncodeStringToFile(stream, attr["comments"])
		EncodeStringToFile(stream, attr["est_tot_correct"])
		EncodeStringToFile(stream, attr["tot_num_spectra"])
		EncodeStringToFile(stream, attr["num_iterations"])"""
		self.Models = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Models))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "mixturemodel_distribution":
			self.Models += 1
			return self.Stream
		if name == "point":
			return NullStream()
		raise ValueError(name)
		
class Inputfile(TagHandler):
	def __init__(self, stream, stat, attr):
		#FIXME: Do we care about this?
		return
		
class RocDataPoint(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return
		
class ErrorPoint(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return
		
class InteractSummary(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return

	def BeginChild(self, name):
		#we don't care about this
		return NullStream()

class RocErrorData(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return

	def BeginChild(self, name):
		#we don't care about this
		return NullStream()

class PeptideprophetSummary(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return

	def BeginChild(self, name):
		#we don't care about this
		return NullStream()

class AnalysisSummary(TagHandler):
	"""
	enum EngineCode {
		Unknown,
		interprophet,
		HaveVersion = 0x80
	}
	struct AnalysisSummary {
		DWORD RecordSize;
		//WORD peptideprophet_summary__count;
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
	}
	"""

	def __init__(self, stream, stat, attr):
		version = TryGet(attr, "version")
		self.StartPos = stream.tell()
		stream.write(struct.pack("=IHHHHHHHHHB", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (EncodeOptional(version) << 7) | GetEngineCode(attr["analysis"])))
		EncodeStringToFile(stream, attr["time"])
		if version != None:
			EncodeStringToFile(stream, version)
		self.Peptides = 0
		self.Interacts = 0
		self.Libras = 0
		self.Asaps = 0
		self.Xpresss = 0
		self.Files = 0
		self.Rocs = 0
		self.Errors = 0
		self.Mixtures = 0
		self.Interact = None
		self.Libra = None
		self.Asap = None
		self.Xpress = None
		self.File = None
		self.Roc = None
		self.Error = None
		self.Mixture = None

	def End(self):
		if self.Interact != None:
			self.Stream.write(self.Interact.getvalue())
		if self.Libra != None:
			self.Stream.write(self.Libra.getvalue())
		if self.Asap != None:
			self.Stream.write(self.Asap.getvalue())
		if self.Xpress != None:
			self.Stream.write(self.Xpress.getvalue())
		if self.File != None:
			self.Stream.write(self.File.getvalue())
		if self.Roc != None:
			self.Stream.write(self.Roc.getvalue())
		if self.Error != None:
			self.Stream.write(self.Error.getvalue())
		if self.Mixture != None:
			self.Stream.write(self.Mixture.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IHHHHHHHHH", EndPos - self.StartPos, self.Peptides, self.Interacts, self.Libras, self.Asaps, self.Xpresss, self.Files, self.Rocs, self.Errors, self.Mixtures))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "peptideprophet_summary":
			self.Peptides += 1
			return self.Stream
		if name == "interact_summary":
			self.Interacts += 1
			if self.Interact == None:
				self.Interact = StringIO()
			return self.Interact
		if name == "libra_summary":
			self.Libras += 1
			if self.Libra == None:
				self.Libra = StringIO()
			return self.Libra
		if name == "asapratio_summary":
			self.Asaps += 1
			if self.Asap == None:
				self.Asap = StringIO()
			return self.Asap
		if name == "xpressratio_summary":
			self.Xpresss += 1
			if self.Xpress == None:
				self.Xpress = StringIO()
			return self.Xpress
		if name == "inputfile": 
			self.Files += 1
			if self.File == None:
				self.File = StringIO()
			return self.File
		if name == "roc_data_point":
			self.Rocs += 1
			if self.Roc == None:
				self.Roc = StringIO()
			return self.Roc
		if name == "error_point":
			self.Errors += 1
			if self.Error == None:
				self.Error = StringIO()
			return self.Error
		if name == "mixturemodel" or name == "mixture_model":
			self.Mixtures += 1
			if self.Mixture == None:
				self.Mixture = StringIO()
			return self.Mixture
		raise ValueError(name)
		
	@staticmethod
	def EatAll(f, dic, count):
		i = 0
		while i < count:
			[RecordSize] = struct.unpack(f.read(4))
			f.seek(RecordSize - 4, 1)
			i += 1
		return

class MsmsPipelineAnalysis(TagHandler):
	"""
	struct MsmsPipelineAnalysis {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "MsmsPipelineAnalysis.__init__(): ")
		self.Stat = stat
		self.StartPos = stream.tell()
		stream.write(struct.pack("=HHHH", 0, 0, 0, 0))
		EncodeStringToFile(stream, attr["summary_xml"])
		EncodeStringToFile(stream, attr["date"])
		#EncodeStringToFile(stream, xml.attrib["summary_xml"])
		self.Runs = 0
		self.Datasets = 0
		self.Summaries = 0
		self.DatasetDerivation = None
		self.AnalysisSummary = None

	def End(self):
		if self.DatasetDerivation != None:
			self.Stream.write(self.DatasetDerivation.getvalue())
		if self.AnalysisSummary != None:
			self.Stream.write(self.AnalysisSummary.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=HHHH", self.Stat.IncludedScores, self.Runs, self.Datasets, self.Summaries))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "msms_run_summary":
			self.Runs += 1
			return self.Stream
		elif name == "dataset_derivation":
			if self.DatasetDerivation == None:
				self.DatasetDerivation = StringIO()
			return self.DatasetDerivation
		elif name == "analysis_summary":
			if self.AnalysisSummary == None:
				self.AnalysisSummary = StringIO()
			return self.AnalysisSummary
		raise ValueError(name)

	@staticmethod
	def Search(f, stat):
		"""
		To search everything relevent, make dic { None: "search terms" }
		"""
		TRACEPOS("MsmsPipelineAnalysis.Search(): ", f.tell())
		[scores, msms_run_summary__count, dataset_derivation__count, analysis_summary__count] = struct.unpack("=HHHH", f.read(2 + 2 + 2 + 2))
		EatStringFromFile(f) #don't bother searching the summary filename
		EatStringFromFile(f) #don't bother searching the date
		if msms_run_summary__count > 0:
			MsmsRunSummary.SearchAll(f, stat, msms_run_summary__count)
		#if dataset_derivation__count > 0:
		#	DatasetDerivation.SearchAll(f, stat, dataset_derivation__countt)
		#if analysis_summary__count > 0:
		#	AnalysisSummary.SearchAll(f, stat, analysis_summary__count)
		return scores

	@staticmethod
	def GetAvaliableScores(f):
		return struct.unpack("=H", f.read(2))[0]
		

#externally usable functions

def ConvertFilename(FileName):
	return os.path.splitext(FileName)[0] + ".pepBIN"

def IsConverted(FileName):
	return os.path.isfile(ConvertFilename(FileName))

def ToBinary(FileName, Dest = None, Links = None):
	"""
	struct _PeptideInstance {
		String Peptide;
		DWORD Occurances;
		DWORD Offsets[Occurances];
	}
	
	struct PepBIN {
		DWORD PeptideIndexOffset;
		MsmsPipelineAnalysis msms_pipeline_analysis;
		DWORD PeptideCount;
		_PeptideInstance Peptides[PeptideCount];
	}
	"""
	if Dest == None:
		Dest = open(ConvertFilename(FileName), "w")
	Dest.write(struct.pack("=I", 0))
	stat = EncodingStatus(Links)
	parser = xml.sax.make_parser()
	parser.setFeature("http://xml.org/sax/features/external-general-entities", False)
	parser.setContentHandler(SaxHandler(Dest, stat))
	parser.parse(open(FileName, "r"))
	EndPos = Dest.tell()
	Dest.seek(0)
	Dest.write(struct.pack("=I", EndPos))
	Dest.seek(EndPos)
	Dest.write(struct.pack("=I", len(stat.Peptides)))
	for peptide, offsets in stat.Peptides.items():
		EncodeStringToFile(Dest, peptide)
		Dest.write(struct.pack("=H", len(offsets)))
		for hit, query in offsets:
			Dest.write(struct.pack("=II", hit, query))
	Dest.close()

def SearchBasic(FileName, terms):
	f = open(FileName, "r")
	f.seek(4) #skip the peptide index offset
	stat = SearchStatus({ None: SplitPhrase(terms.upper()) })
	scores = MsmsPipelineAnalysis.Search(f, stat)
	f.close()
	#PrintResults(stat.Results)
	return [scores, stat.TotalQueries, stat.Results]

def SearchAdvanced(FileName, terms_dict):
	f = open(FileName, "r")
	f.seek(4) #skip the peptide index offset
	terms = {}
	for k, v in terms_dict.items():
		terms[k] = SplitPhrase(v.upper())
	stat = SearchStatus(terms)
	scores = MsmsPipelineAnalysis.Search(f, stat)
	f.close()
	#PrintResults(stat.Results)
	return [scores, stat.TotalQueries, stat.Results]

def SearchPeptide(FileName, peptide):
	f = open(FileName, "r")
	[PeptideIndexOffset] = struct.unpack("=I", f.read(4))
	scores = MsmsPipelineAnalysis.GetAvaliableScores(f)
	f.seek(PeptideIndexOffset)
	[peptides] = struct.unpack("=I", f.read(4))
	peptide = peptide.upper()
	while peptides > 0:
		pep = DecodeStringFromFile(f)
		[occurrances] = struct.unpack("=H", f.read(2))
		if pep == peptide:
			offsets = [struct.unpack("II", f.read(4 + 4)) for i in xrange(occurrances)]
			info = [SpectrumQuery.GetHitInfoSeek(f, query, hit) for hit, query in offsets]
			f.close()
			return [scores, info]
		else:
			f.seek(occurrances * (4 + 4), 1)
		peptides -= 1
	f.close()
	return [socres, None]

def GetScores(FileName, qoff, hoff):
	f = open(FileName, "r")
	results = SpectrumQuery.GetScores(f, qoff, hoff)
	f.close()
	return results

def GetAvaliableScores(FileName):
	f = open(FileName, "r")
	f.seek(4) #skip the peptide index offset
	scores = MsmsPipelineAnalysis.GetAvaliableScores(f)
	f.close()
	return scores

def SearchEngineName(scores):
	if scores & 0x800:
		return "Interprophet Probability"
	elif scores & 0x400:
		return "Peptideprophet Probability"
	elif scores & 0x08:
		return "X-Tandem Hyperscore"
	elif scores & 0x20:
		return "Mascot Ionscore"
	elif scores & 0x02:
		return "Omssa Expect"
	return "unknown"

def SearchEngineOnlyName(scores):
	if scores & 0x08:
		return "X-Tandem Hyperscore"
	elif scores & 0x20:
		return "Mascot Ionscore"
	elif scores & 0x02:
		return "Omssa Expect"
	return "unknown"

def DefaultSortColumn(scores):
	if scores & 0x800:
		return "ip_prob"
	if scores & 0x400:
		return "pp_prob"
	if scores & 0x08:
		return "hyperscore"
	elif scores & 0x20:
		return "ionscore"
	return "expect"

def GetColumns():
	return [{"name":"peptide", "title": "Peptide"}, {"name": "protein", "title": "Protein"}, {"name": "massdiff", "title": "Mass Difference"}, {"name": score, "title": score}]

#FIXME: DEBUG
def PrintResults(results):
	print("Results:")
	for r in results:
		print(r)

#HTTP server functions
from HttpUtil import *;

def DisplayList(request, query, fname):
	scores = GetAvaliableScores(fname)
	score = SearchEngineName(scores)
	sortcol = DefaultSortColumn(scores)
	head_results = "<tr class=\\\"link\\\"><th><span onclick=\\\"SortRestults('peptide');\\\">Peptide</span></th><th><span onclick=\\\"SortRestults('protein');\\\">Protein</span></th><th><span onclick=\\\"SortRestults('massdiff');\\\">Mass Difference</span></th><th><span onclick=\\\"SortRestults('" + DefaultSortColumn(scores) + "');\\\">" + score + "</span></th></tr>"
	head_peptides = "<tr class=\\\"link\\\"><th><span onclick=\\\"SortPeptides('spectrum');\\\">Spectrum</span></th><th><span onclick=\\\"SortPeptides('massdiff');\\\">Mass Diff</span></th><th><span onclick=\\\"SortPeptides('" + sortcol + "');\\\">" + SearchEngineName(scores) + "</span></th>";
	if scores & 0x6C: #this is a prophet result
		head_peptides += "<th><span onclick=\\\"SortPeptides('engine');\\\">Search Engine</span></th><th><span onclick=\\\"SortPeptides('raw');\\\">Raw Score</span></th></tr>";
	head_peptides += "</tr>";
	return { "type": request.matchdict["type"], "file": query["file"], "sortcol": sortcol, "head_results": Literal(head_results), "head_peptides": Literal(head_peptides) }
