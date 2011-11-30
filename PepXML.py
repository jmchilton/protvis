#!/usr/bin/python

#pepXML definition at http://www.ncbi.nlm.nih.gov/IEB/ToolBox/CPP_DOC/lxr/source/src/algo/ms/formats/pepxml/pepXML.xsd

import struct
import os
#from xml.etree.ElementTree import ElementTree
import xml.sax
from xml.sax.saxutils import escape, unescape
import xml.parsers.expat
from cStringIO import StringIO

#Util functions
import sys;
def TRACE(*args):
	message = "".join([str(i) for i in args])
	print(message)
	return

def TRACEPOS(*args):
	#TRACE(*args)
	return

def TRACEPOSXML(stream, *args):
	"""if type(stream) is type(StringIO()):
		args += (str(stream.tell()), " (StringIO)")
	else:
		args += (str(stream.tell()),)
	TRACE(*args)"""
	return

def TryGetAttrib(elem, attr):
	try:
		return elem.attrib[attr]
	except:
		return None

def TryGet(dic, elem):
	try:
		return dic[elem]
	except:
		return None

def EncodeOptional(*attrs):
	Flags = 0
	Bit = 1
	for attr in attrs:
		if attr != None:
			Flags |= Bit
		Bit <<= 1
	return Flags

def EncodeStringToFile(f, s):
	l = len(s)
	f.write(struct.pack("=H{0}s".format(l), l, str(s)))

def EncodeString(f, s):
	l = len(s)
	return struct.pack("=H{0}s".format(l), l, str(s))

def DecodeStringFromFile(f):
	l = struct.unpack("=H", f.read(2))[0]
	return struct.unpack("={0}s".format(l), f.read(l))[0]

def EatStringFromFile(f):
	return f.seek(struct.unpack("=H", f.read(2))[0], 1)

def GetEngineCode(name):
	if name == "interprophet":
		return 1
	return 0 #unknown

#Encoding Info
class EncodingStatus:
	def __init__(self):
		self.IncludedScores = 0
		self.Peptides = {}

	def AddPeptide(self, peptide, offset):
		try:
			self.Peptides[peptide].append(offset)
		except:
			self.Peptides[peptide] = [offset]


#Search results
class ResultType:
	Undefined = 0
	SpectrumQuery = 1
	SearchResult = 2
	SearchHit = 3
	SearchScore = 4
	Modification = 5
	
class Result:
	def __init__(self, Type = ResultType.Undefined, Summary = -1, Query = -1, Result = -1, Hit = -1):
		self.Type = Type
		self.SummaryIndex = Summary
		self.QueryIndex = Query
		self.ResultIndex = Result
		self.HitIndex = Hit
		self.HitMatches = 0
		self.TotalMatches = 0
		self.HitInfo = None

	def __str__(self):
		fields = ["   Type: ", str(self.Type), "\n",
			"   QueryIndex: ", str(self.QueryIndex), "\n",
			"   ResultIndex: ", str(self.ResultIndex), "\n",
			"   HitIndex: ", str(self.HitIndex), "\n",
			"   TotalMatches: ", str(self.TotalMatches), "\n",
			"   precursor_neutral_mass: ", str(self.precursor_neutral_mass), "\n",
			"   retention_time_sec: ", str(self.retention_time_sec), "\n",
			"   search_specification: ", str(self.search_specification), "\n",
			"   HitInfo: ", str(self.HitInfo), "\n"]
		return "".join(fields)

class SearchStatus:
	def __init__(self, dic):
		self.Terms = dic
		self.Matched = {}
		self.Results = []
		self.TotalQueries = 0
		
	def copy(self):
		dic = {}
		for k in self.Terms:
			dic[k] = [i for i in self.Terms[k]]
		new = SearchStatus(dic)
		dic = {}
		for k in self.Matched:
			dic[k] = [i for i in self.Matched[k]]
		new.Matched = dic
		new.Results = self.Results
		return new

	def IsMatched(self):
		return len(self.Terms) == 0

	def _SearchItem(self, name, value, comparator):
		#returns:
		# -1 if this key is not required for searhing
		#  0 if this key was searched against the basic or specific search, but did not completly match either
		#  1 if matched either the basic or specific search
		phrases = None
		key = name
		try:
			phrases = self.Terms[name]
		except:
			try:
				phrases = self.Terms[None]
				key = None
			except:
				return -1
		i = 0
		count = len(phrases)
		while i < count:
			if comparator(value, phrases[i]) != 0:
				try:
					self.Matched[key].append(phrases[i])
				except:
					self.Matched[key] = [phrases[i]]
				del phrases[i]
				count -= 1
			else:
				i += 1
		if count == 0:
			del self.Terms[key]
			return 1
		return 0

	def SearchItemInt(self, name, value):
		def CmpInt(val, s):
			try:
				if val == int(s):
					return 1
				else:
					return 0
			except:
				return 0
		return self._SearchItem(name, value, CmpInt)

	def SearchItemFloat(self, name, value):
		def Precision(s):
			l = s.split(".")
			if len(l) == 1:
				l = s.split("e")
				if len(l) > 1:
					return -int(l[1])
				else:
					return 0;
			l = l[1].split("e")
			if len(l) > 1:
				[frac, exp] = l
				return len(frac) - int(exp) #works for + and - exp's
			else:
				return len(l[0])

		def CmpFloat(val, s):
			try:
				f = float(s)
				prec = Precision(s)
				if abs(val - f) < pow(10, -prec):
					return 1
				else:
					return 0
			except:
				return 0

		return self._SearchItem(name, value, CmpFloat)
	
	def SearchItemString(self, name, value):
		def CmpString(val, s):
			try:
				if val.upper().find(s) >= 0:
					return 1
				return 0
			except:
				return 0
		return self._SearchItem(name, value, CmpString)

def SplitPhrase(phrase):
	return phrase.split(); #FIXME: don't split quotes


#XML helpers
class NullStream:
	def write(bytes):
		#do nothing
		return

class TagHandler(object):
	def __new__(cls, stream, *args, **kwargs):
		obj = object.__new__(cls, *args, **kwargs)
		obj.Stream = stream
		return obj

	def End(self):
		return

	def BeginChild(self, name):
		raise NotImplementedError(name)

	def EndChild(self):
		return stream

class Eater:
	def End(self):
		return

	def BeginChild(self, name):
		return NullStream()

	def EndChild(self):
		return

class SaxHandler(xml.sax.ContentHandler):
	def __init__(self, stream, stat):
		self.Stream = stream
		self.Stat = stat
		self.State = []
		self.Handlers = {
			"specificity": Specificity,
			"sample_enzyme": SampleEnzyme,
			"mod_aminoacid_mass": ModAminoacidMass,
			"modification_info": ModificationInfo,
			"alternative_protein": AlternativeProtein,
			"search_score_summary": SearchScoreSummary,
			"peptideprophet_result": PeptideprophetResult,
			"interprophet_result": InterprophetResult,
			"asapratio_result": AsapratioResult,
			"xpressratio_result": XpressratioResult,
			"analysis_result": AnalysisResult,
			"search_score": SearchScore,
			"search_hit": SearchHit,
			"search_result": SearchResult,
			"search_database": SearchDatabase,
			"enzymatic_search_constraint": EnzymaticSearchConstraint,
			"sequence_search_constraint": SequenceSearchConstraint,
			"aminoacid_modification": AminoacidModification,
			"terminal_modification": TerminalModification,
			"parameter": Parameter,
			"search_summary": SearchSummary,
			"database_refresh_timestamp": DatabaseRefreshTimestamp,
			"xpressratio_timestamp": XpressratioTimestamp,
			"analysis_timestamp": AnalysisTimestamp,
			"spectrum_query": SpectrumQuery,
			"msms_run_summary": MsmsRunSummary,
			"dataset_derivation": DatasetDerivation,
			"point": Point,
			"mixturemodel": Mixturemodel,
			"inputfile": Inputfile,
			"roc_data_point": RocDataPoint,
			"error_point": ErrorPoint,
			"interact_summary": InteractSummary,
			"analysis_summary": AnalysisSummary,
			"msms_pipeline_analysis": MsmsPipelineAnalysis}

	def startElement(self, name, attrs):
		#try:
			if len(self.State) > 0:
				stream = self.State[-1].BeginChild(name)
			else:
				stream = self.Stream
			self.State.append(self.Handlers[name](stream, self.Stat, attrs))
		#except:
		#	print("Ignoring unknown element '" + name + "'")
		#	self.State.append(Eater())

	def endElement(self, name):
		stream = self.State.pop().End()
		#State[-1].EndChild(stream) #Not used



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
		EncodeStringToFile(stream, unescape(attr["cut"]))
		if min_spacing != None:
			EncodeStringToFile(stream, unescape(min_spacing))
		if no_cut != None:
			EncodeStringToFile(stream, unescape(no_cut))

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
		EncodeStringToFile(stream, unescape(attr["name"]))
		if description != None:
			EncodeStringToFile(stream, unescape(description))
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
		EncodeStringToFile(stream, unescape(attr["protein"]))
		if protein_descr != None:
			EncodeStringToFile(stream, unescape(protein_descr))
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
		self.ParamCount = 0
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.ParamCount))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "parameter":
			self.ParamCount += 1
			return self.Stream
		raise ValueError(name)

	@staticmethod
	def GetInfoAll(f):
		[count] = struct.unpack("=H", f.read(2))
		return Parameter.GetInfoAll(f, count)

class PeptideprophetResult(TagHandler):
	"""
	struct PeptideprophetResult {
		float probability;
		BYTE OptionalFlags;
		String all_ntt_prob; //ONLY IF (OptionalFlags & 0x01)
		String analysis; //ONLY IF (OptionalFlags & 0x02)
		SearchScoreSummary search_score_summary; //ONLY IF (OptionalFlags & 0x04)
	}
	"""

	def __init__(self, stream, stat, attr):
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
		return results
	
class InterprophetResult(TagHandler):
	"""
	struct InterprophetResult {
		float probability;
		BYTE OptionalFlags;
		String all_ntt_prob; //ONLY IF (OptionalFlags & 0x01)
		String analysis; //ONLY IF (OptionalFlags & 0x02)
		SearchScoreSummary search_score_summary; //ONLY IF (OptionalFlags & 0x04)
	}
	"""

	def __init__(self, stream, stat, attr):
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
		return results
	
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

	def __init__(self, stream, stat, attr):
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
		return info

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
	}
	"""

	def __init__(self, stream, stat, attr):
		#TRACEPOSXML(stream, "SearchScore.__init__(): ")
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
		return results

	@staticmethod
	def GetInfo(f):
		[OptionalFlags] = struct.unpack("=H", f.read(2))
		results = {}
		if OptionalFlags & 0x01:
			[bvalue] = struct.unpack("=d", f.read(8))
			results["bvalue"] = bvalue
		if OptionalFlags & 0x02:
			[expect] = struct.unpack("=d", f.read(8))
			results["expect"] = expect
		if OptionalFlags & 0x04:
			[homologyscore] = struct.unpack("=d", f.read(8))
			results["homologyscore"] = homologyscore
		if OptionalFlags & 0x08:
			[hyperscore] = struct.unpack("=d", f.read(8))
			results["hyperscore"] = hyperscore
		if OptionalFlags & 0x10:
			[identityscore] = struct.unpack("=d", f.read(8))
			results["identityscore"] = identityscore
		if OptionalFlags & 0x20:
			[ionscore] = struct.unpack("=d", f.read(8))
			results["ionscore"] = ionscore
		if OptionalFlags & 0x40:
			[nextscore] = struct.unpack("=d", f.read(8))
			results["nextscore"] = nextscore
		if OptionalFlags & 0x80:
			[pvalue] = struct.unpack("=d", f.read(8))
			results["pvalue"] = pvalue
		if OptionalFlags & 0x100:
			[star] = struct.unpack("=d", f.read(8))
			results["star"] = star
		if OptionalFlags & 0x200:
			[yscore] = struct.unpack("=d", f.read(8))
			results["yscore"] = yscore
		return results

	@staticmethod
	def CompareHits(a, b):
		#returns:
		# >0 if b is better than a
		#  0 if b is equivelent to a
		# <0 if b is worse than a
		try:
			return a["hyperscore"] - b["hyperscore"] #interprophet
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
		WORD analysis_result__count;
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
		BYTE tot_num_ions; //ONLY IF (OptionalFlags & 0x10)
		//BYTE is_rejected;
		//WORD hit_rank;
		int num_tol_term; //ONLY IF (OptionalFlags & 0x20)
		int num_missed_cleavages; //ONLY IF (OptionalFlags & 0x40)
		String calc_pI; //ONLY IF (OptionalFlags & 0x80)
		double protein_mw; //ONLY IF (OptionalFlags & 0x100)
		SearchScore search_score;
		Modification modification_info[modification_info__count];
		Alternative alternative_protein[alternative_protein__count];
		AnalysisResult analysis_result[analysis_result__count];
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
		stream.write(struct.pack("=IHHHIdd", 0, 0, 0, 0, 0, float(attr["calc_neutral_pep_mass"]), float(attr["massdiff"])))
		stream.write(struct.pack("=HB", Flags, int(attr["num_tot_proteins"])))
		peptide = unescape(attr["peptide"])
		stat.AddPeptide(peptide, self.StartPos)
		EncodeStringToFile(stream, peptide)
		EncodeStringToFile(stream, unescape(attr["protein"]))
		if protein_descr != None:
			EncodeStringToFile(stream, unescape(protein_descr))
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
			stream.write(struct.pack("=B", int(tot_num_ions)))
		if num_tol_term != None:
			stream.write(struct.pack("=i", int(num_tol_term)))
		if num_missed_cleavages != None:
			stream.write(struct.pack("=i", int(num_missed_cleavages)))
		if calc_pI != None:
			EncodeStringToFile(stream, unescape(calc_pI))
		if protein_mw != None:
			stream.write(struct.pack("=d", protein_mw))
		DataOffset = stream.tell()
		stream.seek(self.StartPos + 4 + 2 + 2 + 2)
		stream.write(struct.pack("=I", DataOffset - self.StartPos))
		stream.seek(DataOffset)
		self.ModCount = 0
		self.AltCount = 0
		self.AnalCount = 0
		self.Scores = {}
		self.ModInfos = None
		self.AltProts = None
		self.AnalRes = None

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
		Scores = EncodeOptional(bvalue, expect, homologyscore, hyperscore, identityscore, ionscore, nextscore, pvalue, star, yscore)
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
		if self.ModInfos != None:
			self.Stream.write(self.ModInfos.getvalue())
		if self.AltProts != None:
			self.Stream.write(self.AltProts.getvalue())
		if self.AnalRes != None:
			self.Stream.write(self.AnalRes.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IHHH", EndPos - self.StartPos, self.ModCount, self.AltCount, self.AnalCount))
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
			self.AnalCount += 1
			if self.AnalRes == None:
				self.AnalRes = StringIO()
			return self.AnalRes
		raise ValueError(name)
		
	@staticmethod
	def SearchAllBestHit(f, stat, count):
		i = 0
		BestScore = None
		BestScorePos = -1
		BestScoreIndex = -1
		Hits = 0
		while i < count:
			s = stat.copy()
			StartPos = f.tell()
			TRACEPOS("SearchHit.SearchAllBestHit(", i, "): ", f.tell())
			[RecordSize, modification_info__count, alternative_protein__count, analysis_result__count, DataOffset, calc_neutral_pep_mass, massdiff, OptionalFlags, num_tot_proteins] = struct.unpack("=IHHHIddHB", f.read(4 + 2 + 2 + 2 + 4 + 8 + 8 + 2 + 1))
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
				[tot_num_ions] = struct.unpack("=B", f.read(1))
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
			if analysis_result__count > 0:
				AnalysisResult.SearchAll(f, s, analysis_result__count)
			s.SearchItemString("Peptide", PeptideFull)
			if s.IsMatched():
				Hits += 1
				if BestScore == None or SearchScore.CompareHits(BestScore, score) > 0:
					BestScore = score
					BestScorePos = StartPos
					BestScoreIndex = i
			else:
				f.seek(StartPos + RecordSize)
			i += 1
		if BestScore != None:
			EndPos = f.tell()
			f.seek(BestScorePos)
			info = SearchHit.GetInfo(f)
			f.seek(EndPos)
			return [BestScoreIndex, Hits, info]
		return None

	@staticmethod
	def GetScoresAll(f, count, hid):
		i = 0
		results = {}
		while i < count:
			TRACEPOS("SearchHit.GetScoresAll(", i, "): ", f.tell())
			if i == hid:
				StartPos = f.tell()
				[RecordSize, _1, _2, _3, DataOffset] = struct.unpack("=IHHHI", f.read(4 + 2 + 2 + 2 + 4))
				f.seek(StartPos + DataOffset)
				results = SearchScore.GetInfo(f)
				f.seek(StartPos + RecordSize)
			else:
				f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1
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
		[RecordSize, modification_info__count, alternative_protein__count, analysis_result__count, DataOffset, calc_neutral_pep_mass, massdiff] = struct.unpack("=IHHHIdd", f.read(4 + 2 + 2 + 2 + 4 + 8 + 8))
		dic = {}
		dic["calc_neutral_pep_mass"] = calc_neutral_pep_mass
		dic["massdiff"] = massdiff
		[OptionalFlags, num_tot_proteins] = struct.unpack("=HB", f.read(2 + 1))
		dic["num_tot_proteins"] = num_tot_proteins
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
			[dic["tot_num_ions"]] = struct.unpack("=B", f.read(1))
		if OptionalFlags & 0x20:
			[dic["num_tol_term"]] = struct.unpack("=i", f.read(4))
		if OptionalFlags & 0x40:
			[dic["num_missed_cleavages"]] = struct.unpack("=i", f.read(4))
		if OptionalFlags & 0x80:
			dic["calc_pI"] = DecodeStringFromFile(f)
		if OptionalFlags & 0x100:
			[dic["protein_mw"]] = struct.unpack("=d", f.read(8))
		d = SearchScore.GetInfo(f)
		for k, v in d.items():
			dic[k] = v
		dic["modification_info"] = [ModificationInfo.GetInfo(f) for i in xrange(modification_info__count)]
		dic["alternative_protein"] = [AlternativeProtein.GetInfo(f) for i in xrange(alternative_protein__count)]
		dic["analysis_result"] = [AnalysisResult.GetInfo(f) for i in xrange(analysis_result__count)]
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
		BestResultIndex = -1
		BestHitIndex = -1
		BestHitInfo = None
		BestHitMatches = 0
		BestHitTotal = 0
		while i < count:
			TRACEPOS("SearchResult.SearchAllBestHitAndCount(", i, "): ", f.tell())
			[search_hit__count] = struct.unpack("=I", f.read(4))
			r = SearchHit.SearchAllBestHit(f, stat, search_hit__count)
			if r != None:
				[idx, hits, info] = r
				if BestHitInfo == None or SearchScore.CompareHits(BestHitInfo, info) > 0:
					BestResultIndex = i
					BestHitIndex = idx
					BestHitInfo = info
					BestHitMatches = hits
					BestHitTotal = search_hit__count
			i += 1
		return [BestResultIndex, BestHitIndex, BestHitMatches, BestHitTotal, BestHitInfo]

	@staticmethod
	def GetScoresAll(f, count, rid, hid):
		i = 0
		while i < count:
			TRACEPOS("SearchResult.GetScoresAll(", i, "): ", f.tell())
			[search_hit__count] = struct.unpack("=I", f.read(4))
			if i == rid:
				return SearchHit.GetScoresAll(f, search_hit__count, hid)
			else:
				SearchHit.EatAll(f, search_hit__count)
			i += 1
		return {}

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
		BestResultIndex = -1
		BestHitInfo = None
		TotalHits = 0
		while i < count:
			TRACEPOS("SearchResult.GetBestHitInfoAll(", i, "): ", f.tell())
			[search_hit__count] = struct.unpack("=I", f.read(4))
			info = SearchHit.GetInfoFirstEatRest(f, search_hit__count)
			TotalHits += search_hit__count
			if BestHitInfo == None or SearchScore.CompareHits(BestHitInfo, info) > 0:
				BestResultIndex = i
				BestHitInfo = info
			i += 1
		return [BestResultIndex, 0, TotalHits, BestHitInfo]
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
		EncodeStringToFile(stream, unescape(attr["local_path"]))
		if URL != None:
			EncodeStringToFile(stream, unescape(URL))
		if database_name != None:
			EncodeStringToFile(stream, unescape(database_name))
		if orig_database_url != None:
			EncodeStringToFile(stream, unescape(orig_database_url))
		if database_release_date != None:
			EncodeStringToFile(stream, unescape(database_release_date))
		if database_release_identifier != None:
			EncodeStringToFile(stream, unescape(database_release_identifier))
		if size_in_db_entries != None:
			stream.write(struct.pack("=i", int(size_in_db_entries)))
		if size_of_residues != None:
			stream.write(struct.pack("=i", int(size_of_residues)))

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
		EncodeStringToFile(stream, unescape(attr["enzyme"]))
		stream.write(struct.pack("=ii", int(attr["max_num_internal_cleavages"]), int(attr["min_number_termini"])))

class SequenceSearchConstraint(TagHandler):
	"""
	struct SequenceSearchConstraint {
		String sequence;
	}
	"""

	def __init__(self, stream, stat, attr):
		EncodeStringToFile(stream, unescape(attr["sequence"]))

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
		EncodeStringToFile(stream, unescape(attr["aminoacid"]))
		EncodeStringToFile(stream, unescape(attr["massdiff"]))
		stream.write(struct.pack("=f", float(attr["mass"])))
		EncodeStringToFile(stream, unescape(attr["variable"]))
		peptide_terminus = TryGet(attr, "peptide_terminus")
		symbol = TryGet(attr, "symbol")
		binary = TryGet(attr, "binary")
		description = TryGet(attr, "description")
		stream.write(struct.pack("=B", EncodeOptional(peptide_terminus, symbol, binary, description)))
		if peptide_terminus != None:
			EncodeStringToFile(stream, unescape(peptide_terminus))
		if symbol != None:
			EncodeStringToFile(stream, unescape(symbol))
		if binary != None:
			EncodeStringToFile(stream, unescape(binary))
		if description != None:
			EncodeStringToFile(stream, unescape(description))

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
		EncodeStringToFile(stream, unescape(attr["name"]))
		EncodeStringToFile(stream, unescape(attr["value"]))
		if t != None:
			EncodeStringToFile(stream, unescape(t))"""
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
		EncodeStringToFile(self.Stream, unescape(attr["base_name"]))
		EncodeStringToFile(self.Stream, unescape(attr["search_engine"]))
		if self.out_data_type != None:
			EncodeStringToFile(self.Stream, unescape(self.out_data_type))
		if self.out_data != None:
			EncodeStringToFile(self.Stream, unescape(self.out_data))
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
		EncodeStringToFile(stream, unescape(attr["database"]))
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
		String spectrum;
		unsigned int start_scan;
		unsigned int end_scan;
		float precursor_neutral_mass;
		int assumed_charge;
		unsigned int index;
		float retention_time_sec; //ONLY IF (OptionalFlags & 0x01)
		String search_specification; //ONLY IF (OptionalFlags & 0x02)
		SearchResult search_result[search_result__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SpectrumQuery.__init__(): ")
		self.StartPos = stream.tell()
		retention_time_sec = TryGet(attr, "retention_time_sec")
		search_specification = TryGet(attr, "search_specification")
		stream.write(struct.pack("=IIHB", 0, 0, 0, EncodeOptional(retention_time_sec, search_specification)))
		EncodeStringToFile(stream, unescape(attr["spectrum"]))
		stream.write(struct.pack("=IIfiI", int(attr["start_scan"]), int(attr["end_scan"]), float(attr["precursor_neutral_mass"]), int(attr["assumed_charge"]), int(attr["index"])))
		if retention_time_sec != None:
			stream.write(struct.pack("=f", float(retention_time_sec)))
		if search_specification != None:
			EncodeStringToFile(stream, unescape(search_specification))
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
			[RecordSize, _, search_result__count, OptionalFlags] = struct.unpack("=IIHB", f.read(4 + 4 + 2 + 1))
			spectrum = DecodeStringFromFile(f)
			[_1, _2, precursor_neutral_mass, _3, _4] = struct.unpack("=IIfiI", f.read(4 + 4 + 4 + 4 + 4))
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
				[result.ResultIndex, result.HitIndex, result.TotalHits, result.HitInfo] = SearchResult.GetBestHitInfoAll(f, search_result__count)
				result.HitMatches = result.TotalHits
			else:
				[rid, hid, matches, total, info] = SearchResult.SearchAllBestHitAndCount(f, s, search_result__count)
				if info != None:
					result = Result(ResultType.SearchHit)
					result.ResultIndex = rid
					result.HitIndex = hid
					result.HitMatches = matches
					result.TotalHits = total
					result.HitInfo = info
			if result != None:
				result.precursor_neutral_mass = precursor_neutral_mass
				result.retention_time_sec = retention_time_sec
				result.search_specification = search_specification
				result.QueryIndex = i
				stat.Results.append(result)
			i += 1

	@staticmethod
	def GetScoresAll(f, count, qid, rid, hid):
		i = 0
		while i < count:
			TRACEPOS("SpectrumQuery.GetScoresAll(", i, "): ", f.tell())
			if i == qid:
				StartPos = f.tell()
				[RecordSize, search_result__offset, search_result__count, OptionalFlags] = struct.unpack("=IIHB", f.read(4 + 4 + 2 + 1))
				spectrum = DecodeStringFromFile(f)
				f.seek(StartPos + search_result__offset)
				results = SearchResult.GetScoresAll(f, search_result__count, rid, hid)
				f.seek(StartPos + RecordSize)
				return [spectrum, results]
			else:
				f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1
		return {}


class MsmsRunSummary(TagHandler):
	"""
	struct MsmsRunSummary {
		DWORD RecordSize; //Size in bytes of this record, not including this 4 byte value
		DWORD spectrum_query__count;
		DWORD spectrum_query__offset;
		DWORD OtherDataOffset;
		String base_name;
		String raw_data_type;
		String raw_data;
		BYTE OptionalFlags;
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
		stream.write(struct.pack("=IIII", 0, 0, 0, 0))
		EncodeStringToFile(stream, unescape(attr["base_name"]))
		EncodeStringToFile(stream, unescape(attr["raw_data_type"]))
		EncodeStringToFile(stream, unescape(attr["raw_data"]))
		msManufacturer = TryGet(attr, "msManufacturer")
		msModel = TryGet(attr, "msModel")
		msIonization = TryGet(attr, "msIonization")
		msMassAnalyzer = TryGet(attr, "msMassAnalyzer")
		msDetector = TryGet(attr, "msDetector")
		stream.write(struct.pack("=B", EncodeOptional(msManufacturer, msModel, msIonization, msMassAnalyzer, msDetector)))
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

	@staticmethod
	def GetScoresAll(f, count, sid, qid, rid, hid):
		i = 0
		while i < count:
			TRACEPOS("MsmsRunSummary.GetScoresAll(", i, "): ", f.tell())
			if i == sid:
				StartPos = f.tell()
				[_, spectrum_query__count, spectrum_query__offset] = struct.unpack("=III", f.read(4 + 4 + 4))
				f.seek(StartPos + spectrum_query__offset)
				return SpectrumQuery.GetScoresAll(f, spectrum_query__count, qid, rid, hid)
			else:
				f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1
		return {}

class DatasetDerivation(TagHandler):
	def __init__(self, stream, stat, attr):
		raise NotImplementedError("DatasetDerivation")
		
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

class Mixturemodel(TagHandler):
	def __init__(self, stream, stat, attr):
		#we don't care about this
		return

	def BeginChild(self, name):
		#We don't care about what is in this
		return None
		
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
		return None

class AnalysisSummary(TagHandler):
	def __init__(self, stream, stat, attr):
		stream.write(struct.pack("=B", GetEngineCode(attr["analysis"])))

	def BeginChild(self, name):
		#FIXME: Do we care about this?
		return None
		
	@staticmethod
	def SearchAll(f, dic, count):
		"""i = 0
		while i < count:
			print("NYI: AnalysisSummary.Search") #FIXME: Implement
			i += 1
		return"""
		TRACEPOS("AnalysisSymmary.SearchAll(", i, "): ", f.tell())
		f.read(count) #each entry is 1 byte, and we dont care what it is

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
		EncodeStringToFile(stream, unescape(attr["summary_xml"]))
		EncodeStringToFile(stream, unescape(attr["date"]))
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
		if dataset_derivation__count > 0:
			DatasetDerivation.SearchAll(f, stat, dataset_derivation__countt)
		if analysis_summary__count > 0:
			AnalysisSummary.SearchAll(f, stat, analysis_summary__count)
		return scores

	@staticmethod
	def GetScores(f, sid, qid, rid, hid):
		TRACEPOS("MsmsPipelineAnalysis.GetScores(): ", f.tell())
		[scores, msms_run_summary__count, dataset_derivation__count, analysis_summary__count] = struct.unpack("=HHHH", f.read(2 + 2 + 2 + 2))
		EatStringFromFile(f) #don't bother searching the summary filename
		EatStringFromFile(f) #don't bother searching the date
		return MsmsRunSummary.GetScoresAll(f, msms_run_summary__count, sid, qid, rid, hid)
		#don't bother with the rest of the data in the file

	@staticmethod
	def GetAvaliableScores(f):
		return struct.unpack("=H", f.read(2))[0]
		

#externally usable functions

def ConvertFilename(FileName):
	return os.path.splitext(FileName)[0] + ".pepBIN"

def IsConverted(FileName):
	return os.path.isfile(ConvertFilename(FileName))

def PepXml2Bin(FileName, Dest = None):
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
	stat = EncodingStatus()
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
		for offset in offsets:
			Dest.write(struct.pack("=I", offset))
	Dest.close()

def PepBinSearchBasic(FileName, terms):
	f = open(FileName, "r")
	f.seek(4) #skip the peptide index offset
	stat = SearchStatus({ None: SplitPhrase(terms.upper()) })
	scores = MsmsPipelineAnalysis.Search(f, stat)
	f.close()
	#PrintResults(stat.Results)
	return [scores, stat.TotalQueries, sorted(stat.Results, key = SearchScore.KeyExpect)]

def PepBinSearchAdvanced(FileName, terms_dict):
	f = open(FileName, "r")
	terms = {}
	for k, v in terms_dict.items():
		terms[k] = SplitPhrase(v.upper())
	stat = SearchStatus(terms)
	scores = MsmsPipelineAnalysis.Search(f, stat)
	f.close()
	#PrintResults(stat.Results)
	return [scores, stat.TotalQueries, sorted(stat.Results, key = SearchScore.Key)]

def PepBinSearchPeptide(FileName, peptide):
	f = open(FileName, "r")
	f.seek(struct.unpack("=I", f.read(4))[0])
	[peptides] = struct.unpack("=I", f.read(4))
	peptide = peptide.upper()
	while peptides > 0:
		pep = DecodeStringFromFile(f)
		[occurrances] = struct.unpack("=H", f.read(2))
		if pep == peptide:
			offsets = struct.unpack("".join(["I" for i in xrange(occurrances)]), f.read(occurrances * 4))
			info = [SearchHit.GetInfoSeek(f, offset) for offset in offsets]
			f.close()
			return info
		else:
			f.seek(occurrances * 4, 1)
		peptides -= 1
	f.close()
	return None

def PepBinGetScores(FileName, sid, qid, rid, hid):
	f = open(FileName, "r")
	results = MsmsPipelineAnalysis.GetScores(f, sid, qid, rid, hid)
	f.close()
	return results

def GetAvaliableScores(FileName):
	f = open(FileName, "r")
	scores = MsmsPipelineAnalysis.GetAvaliableScores(f)
	f.close()
	return scores

def SearchEngineName(scores):
	if scores & 0x08:
		return "Interprophet Hyperscore"
	elif scores & 0x20:
		return "Mascot Ionscore"
	elif scores & 0x02:
		return "Omssa Expect"
	return "unknown"

def DefaultSortColumn(scores):
	if scores & 0x08:
		return "hyperscore"
	elif scores & 0x20:
		return "ionscore"
	return "expect"

#FIXME: DEBUG
def PrintResults(results):
	print("Results:")
	for r in results:
		print(r)
