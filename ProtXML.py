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

	def GetLink(self, name):
		try:
			return self.Links[name]
		except:
			return 0xFFFF


#Search results
class ResultType:
	Undefined = 0
	Protein = 1
	Peptide = 2
	Modification = 3
	
class Result:
	def __init__(self, Type = ResultType.Undefined):
		self.Type = Type
		self.ProteinOffset = None
		self.PeptideOffset = None
		self.PeptideMatches = None
		self.HitInfo = None

	def __str__(self):
		fields = ["   Type: ", str(self.Type), "\n",
			"   ProteinOffset: ", str(self.ProteinOffset), "\n",
			"   PeptideOffset: ", str(self.PeptideOffset), "\n",
			"   PeptideMatches: ", str(self.PeptideMatches), "\n",
			"   HitInfo: ", str(self.HitInfo), "\n"]
		return "".join(fields)


#XML helpers
class SaxHandler(SaxHandlerBase):
	def __init__(self, stream, stat):
		SaxHandlerBase.__init__(self, stream, stat)
		self.Handlers = {
			"peptide": Peptide,
			"annotation": Annotation,
			"protein": Protein,
			"parameter": Parameter,
			"protein_group": ProteinGroup,
			"peptide_parent_protein": PeptideParentProtein,
			"mod_aminoacid_mass": ModAminoacidMass,
			"modification_info": ModificationInfo,
			"indistinguishable_protein": IndistinguishableProtein,
			"indistinguishable_peptide": IndistinguishablePeptide,
			"protein_summary_data_filter": ProteinSummaryDataFilter,
			"nsp_distribution": NspDistribution,
			"ni_distribution": NiDistribution,
			"nsp_information": NspInformation,
			"ni_information": NiInformation,
			"protein_summary_header": ProteinSummaryHeader,
			"analysis_summary": AnalysisSummary,
			"protein_summary": ProteinSummary,
			"proteinprophet_details": ProteinprophetDetails,
			"program_details": ProgramDetails,
			"dataset_derivation": DatasetDerivation,
			"analysis_result": AnalysisResult,
			"data_filter": DataFilter }


#XML element classes
class Parameter(TagHandler):
	"""
	struct Parameter {
		String name;
		String value;
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "Parameter.__init__(): ")
		EncodeStringToFile(stream, attr["name"])
		EncodeStringToFile(stream, attr["value"])
		
	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("Parameter.SearchAll(", i, "): ", f.tell())
			stat.SearchItemString(DecodeStringFromFile(f), DecodeStringFromFile(f))
			i += 1

	@staticmethod
	def EatAll(f, count):
		i = 0
		while i < count:
			TRACEPOS("Parameter.EatAll(", i, "): ", f.tell())
			EatStringFromFile(f)
			EatStringFromFile(f)
			i += 1

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
	def GetInfoAll(f, count):
		i = 0
		info = range(count)
		while i < count:
			[mod_aminoacid_mass__count, OptionalFlags] = struct.unpack("=HB", f.read(2 + 1))
			dic = {}
			if OptionalFlags & 0x01:
				dic["mod_nterm_mass"] = struct.unpack("=d", f.read(8))
			if OptionalFlags & 0x02:
				dic["mod_cterm_mass"] = struct.unpack("=d", f.read(8))
			dic["mod_aminoacid_mass"] = ModAminoacidMass.GetInfoAll(f, mod_aminoacid_mass__count)
			info[i] = dic
			i += 1
		return info

class Annotation(TagHandler):
	"""
	struct Annotation {
		BYTE OptionalFlags;
		String protein_description;
		String ipi_name; //ONLY IF (OptionalFlags & 0x01)
		String refseq_name; //ONLY IF (OptionalFlags & 0x02)
		String swissprot_name; //ONLY IF (OptionalFlags & 0x04)
		String ensembl_name; //ONLY IF (OptionalFlags & 0x08)
		String trembl_name; //ONLY IF (OptionalFlags & 0x10)
		String locus_link_name; //ONLY IF (OptionalFlags & 0x20)
		String flybase; //ONLY IF (OptionalFlags & 0x40)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "Annotation.__init__(): ")
		ipi_name = TryGet(attr, "ipi_name")
		refseq_name = TryGet(attr, "refseq_name")
		swissprot_name = TryGet(attr, "swissprot_name")
		ensembl_name = TryGet(attr, "ensembl_name")
		trembl_name = TryGet(attr, "trembl_name")
		locus_link_name = TryGet(attr, "locus_link_name")
		flybase = TryGet(attr, "flybase")
		stream.write(struct.pack("=B", EncodeOptional(ipi_name, refseq_name, swissprot_name, ensembl_name, trembl_name, locus_link_name, flybase)))
		EncodeStringToFile(stream, attr["protein_description"])
		if ipi_name != None:
			EncodeStringToFile(stream, ipi_name)
		if refseq_name != None:
			EncodeStringToFile(stream, refseq_name)
		if swissprot_name != None:
			EncodeStringToFile(stream, swissprot_name)
		if ensembl_name != None:
			EncodeStringToFile(stream, ensembl_name)
		if trembl_name != None:
			EncodeStringToFile(stream, trembl_name)
		if locus_link_name != None:
			EncodeStringToFile(stream, locus_link_name)
		if flybase != None:
			EncodeStringToFile(stream, flybase)
		
	@staticmethod
	def Search(f, stat):
		TRACEPOS("Annotation.Search(): ", f.tell())
		[OptionalFlags] = struct.unpack("=B", f.read(1))
		EatStringFromFile(f)
		if OptionalFlags & 0x01:
			EatStringFromFile(f)
		if OptionalFlags & 0x02:
			EatStringFromFile(f)
		if OptionalFlags & 0x04:
			EatStringFromFile(f)
		if OptionalFlags & 0x08:
			EatStringFromFile(f)
		if OptionalFlags & 0x10:
			EatStringFromFile(f)
		if OptionalFlags & 0x20:
			EatStringFromFile(f)
		if OptionalFlags & 0x40:
			EatStringFromFile(f)
		
	@staticmethod
	def Eat(f):
		TRACEPOS("Annotation.Eat(): ", f.tell())
		[OptionalFlags] = struct.unpack("=B", f.read(1))
		EatStringFromFile(f)
		if OptionalFlags & 0x01:
			EatStringFromFile(f)
		if OptionalFlags & 0x02:
			EatStringFromFile(f)
		if OptionalFlags & 0x04:
			EatStringFromFile(f)
		if OptionalFlags & 0x08:
			EatStringFromFile(f)
		if OptionalFlags & 0x10:
			EatStringFromFile(f)
		if OptionalFlags & 0x20:
			EatStringFromFile(f)
		if OptionalFlags & 0x40:
			EatStringFromFile(f)

class AnalysisResult(TagHandler):
	"""
	struct AnalysisResult {
		DWORD RecordSize;
		WORD info__count;
		DWORD id;
		String analysis;
		Object info[info__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "AnalysisResult.__init__(): ")
		_id = TryGet(attr, "id")
		if _id == None:
			_id = 1
		else:
			_id = int(_id)
		self.StartPos = stream.tell()
		stream.write(struct.pack("=IHI", 0, 0, _id))
		EncodeStringToFile(stream, attr["analysis"])
		self.Infos = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IH", EndPos - self.StartPos, self.Infos))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		self.Infos += 1
		return self.Stream
	
	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("AnalysisResult.SearchAll(", i, "): ", f.tell())
			i += 1
	
	@staticmethod
	def EatAll(f, count):
		i = 0
		while i < count:
			TRACEPOS("AnalysisResult.EatAll(", i, "): ", f.tell())
			f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1

class PeptideParentProtein(TagHandler):
	"""
	struct PeptideParentProtein {
		String protein_name;
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "PeptideParentProtein.__init__(): ")
		EncodeStringToFile(stream, attr["protein_name"])

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("PeptideParentProtein.SearchAll(", i, "): ", f.tell())
			stat.SearchItemString("peptide_parent_protein", DecodeStringFromFile(f))
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		i = 0
		info = range(count)
		while i < count:
			TRACEPOS("PeptideParentProtein.SearchAll(", i, "): ", f.tell())
			info[i] = DecodeStringFromFile(f)
			i += 1
		return info

class IndistinguishableProtein(TagHandler):
	"""
	struct IndistinguishableProtein {
		WORD parameter__count; MSB set when Annotation included
		String protein_name;
		Annotation annotation; //ONLY IF (parameter__count & 0x8000)
		Parameter parameter[parameter__count & 0x7FFF];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "IndistinguishableProtein.__init__(): ")
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))
		EncodeStringToFile(stream, attr["protein_name"])
		self.Parameters = 0
		self.Parameter = None

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Parameters))
		self.Stream.seek(EndPos)
		if self.Parameter != None:
			self.Stream.write(self.Parameter.getvalue())

	def BeginChild(self, name):
		if name == "annotation":
			if self.Parameters & 0x8000:
				raise IndexError()
			else:
				self.Parameters |= 0x8000
			return self.Stream
		if name == "parameter":
			if self.Parameter == None:
				self.Parameter = StringIO()
			self.Parameters += 1
			return self.Parameter
		raise ValueError(name)

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		protein = None
		indistinguishable = []
		matched = False
		while i < count:
			TRACEPOS("IndistinguishableProtein.SearchAll(", i, "): ", f.tell())
			[parameter__count] = struct.unpack("=H", f.read(2))
			prot = DecodeStringFromFile(f)
			stat.SearchItemString("protein", prot)
			if parameter__count & 0x8000:
				Annotation.Search(f, stat)
			Parameter.SearchAll(f, stat, parameter__count & 0x7FFF)
			if not matched and stat.IsMatched():
				matched = True
				protein = prot
			else:
				indistinguishable.append(prot)
			i += 1
		return [protein, indistinguishable]

	@staticmethod
	def GetInfoAll(f, count):
		i = 0
		info = range(count)
		while i < count:
			TRACEPOS("IndistinguishableProtein.GetInfoAll(", i, "): ", f.tell())
			[parameter__count] = struct.unpack("=H", f.read(2))
			info[i] = DecodeStringFromFile(f)
			if parameter__count & 0x8000:
				Annotation.Eat(f)
			Parameter.EatAll(f, parameter__count & 0x7FFF)
			i += 1
		return info

class IndistinguishablePeptide(TagHandler):
	"""
	struct IndistinguishablePeptide {
		String peptide_sequence;
		WORD modification_info__count;
		ModificationInfo modification_info[modification_info__count];
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "IndistinguishablePeptide.__init__(): ")
		EncodeStringToFile(stream, attr["peptide_sequence"])
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))
		self.Modifications = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Modifications))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "modification_info":
			self.Modifications += 1
			return self.Stream
		raise ValueError(name)
		
	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("IndistinguishablePeptide.SearchAll(", i, "): ", f.tell())
			stat.SearchItemString("peptide", DecodeStringFromFile(f))
			[modification_info__count] = struct.unpack("=H", f.read(2))
			ModificationInfo.SearchAll(f, stat, modification_info__count)
			i += 1

	@staticmethod
	def GetInfoAll(f, count):
		i = 0
		info = range(count)
		while i < count:
			TRACEPOS("IndistinguishablePeptide.GetInfoAll(", i, "): ", f.tell())
			dic = {}
			dic["peptide"] = DecodeStringFromFile(f)
			[modification_info__count] = struct.unpack("=H", f.read(2))
			dic["modification_info"] = ModificationInfo.GetInfoAll(f, modification_info__count)
			info[i] = dic
			i += 1
		return info

class Peptide(TagHandler):
	"""
	struct Peptide {
		DWORD RecordSize;
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "Peptide.__init__(): ")
		nsp_adjusted_probability = TryGet(attr, "nsp_adjusted_probability")
		ni_adjusted_probability = TryGet(attr, "ni_adjusted_probability")
		exp_sibling_ion_instances = TryGet(attr, "exp_sibling_ion_instances")
		exp_sibling_ion_bin = TryGet(attr, "exp_sibling_ion_bin")
		exp_tot_instances = TryGet(attr, "exp_tot_instances")
		n_enzymatic_termini = TryGet(attr, "n_enzymatic_termini")
		calc_neutral_pep_mass = TryGet(attr, "calc_neutral_pep_mass")
		peptide_group_designator = TryGet(attr, "peptide_group_designator")
		weight = TryGet(attr, "weight")
		if weight == None:
			weight = 1.0
		else:
			weight = float(weight)
		n_sibling_peptides_bin = TryGet(attr, "n_sibling_peptides_bin")
		if n_sibling_peptides_bin == None:
			n_sibling_peptides_bin = 0
		else:
			n_sibling_peptides_bin = int(n_sibling_peptides_bin)
		self.StartPos = stream.tell()
		Flags = YNBit(attr["is_nondegenerate_evidence"], 0x8000) | YNBit(attr["is_contributing_evidence"], 0x4000) | EncodeOptional(nsp_adjusted_probability, ni_adjusted_probability, exp_sibling_ion_instances, exp_sibling_ion_bin, exp_tot_instances, n_enzymatic_termini, calc_neutral_pep_mass, peptide_group_designator)
		stream.write(struct.pack("=IHHHHIIddiiH", 0, 0, 0, 0, 0, int(attr["charge"]), int(attr["n_enzymatic_termini"]), float(attr["initial_probability"]), weight, n_sibling_peptides_bin, int(attr["n_instances"]), Flags))
		EncodeStringToFile(stream, attr["peptide_sequence"])
		if nsp_adjusted_probability != None:
			stream.write(struct.pack("=d", float(nsp_adjusted_probability)))
		if ni_adjusted_probability != None:
			stream.write(struct.pack("=d", float(ni_adjusted_probability)))
		if exp_sibling_ion_instances != None:
			stream.write(struct.pack("=d", float(exp_sibling_ion_instances)))
		if exp_sibling_ion_bin != None:
			stream.write(struct.pack("=d", float(exp_sibling_ion_bin)))
		if exp_tot_instances != None:
			stream.write(struct.pack("=d", float(exp_tot_instances)))
		if n_enzymatic_termini != None:
			stream.write(struct.pack("=d", float(n_enzymatic_termini)))
		if calc_neutral_pep_mass != None:
			stream.write(struct.pack("=d", float(calc_neutral_pep_mass)))
		if peptide_group_designator != None:
			EncodeStringToFile(stream, peptide_group_designator)
		self.Modifications = 0
		self.Parameters = 0
		self.Parents = 0
		self.Indistinguishables = 0
		self.Parameter = None
		self.Parent = None
		self.Indistinguishable = None

	def End(self):
		if self.Parameter != None:
			self.Stream.write(self.Parameter.getvalue())
		if self.Parent != None:
			self.Stream.write(self.Parent.getvalue())
		if self.Indistinguishable != None:
			self.Stream.write(self.Indistinguishable.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IHHHH", EndPos - self.StartPos, self.Modifications, self.Parameters, self.Parents, self.Indistinguishables))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "modification_info":
			self.Modifications += 1
			return self.Stream
		if name == "parameter":
			if self.Parameter == None:
				self.Parameter = StringIO()
			self.Parameters += 1
			return self.Parameter
		if name == "peptide_parent_protein":
			if self.Parent == None:
				self.Parent = StringIO()
			self.Parents += 1
			return self.Parent
		if name == "indistinguishable_peptide":
			if self.Indistinguishable == None:
				self.Indistinguishable = StringIO()
			self.Indistinguishables += 1
			return self.Indistinguishable
		raise ValueError(name)

	@staticmethod
	def SearchAllBestAndCount(f, stat, count):
		TRACEPOS("Peptide.SearchAll(): ", f.tell())
		i = 0
		BestOffset = -1
		matches = 0
		while i < count:
			TRACEPOS("Peptide.SearchAllBestAndCount(", i, "): ", f.tell())
			StartPos = f.tell()
			s = stat.copy()
			[RecordSize, modification_info__count, parameter__count, peptide_parent_protein__count, indistinguishable_peptide__count, charge, n_enzymatic_termini, initial_probability, weight, n_sibling_peptides_bin, n_instances, OptionalFlags] = struct.unpack("=IHHHHIIddiiH", f.read(4 + 2 + 2 + 2 + 2 + 4 + 4 + 8 + 8 + 4 + 4 + 2))
			#stat.SearchItemString("peptide", DecodeStringFromFile(f))
			peptide_sequence = DecodeStringFromFile(f)
			s.SearchItemString("peptide", peptide_sequence)
			if OptionalFlags & 0x01:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x02:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x04:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x08:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x10:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x20:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x40:
				#struct.unpack("=d", f.read(8)) #FIXME: Search this?
				f.read(8)
			if OptionalFlags & 0x80:
				#DecodeStringFromFile(f) #FIXME: Search this?
				EatStringFromFile(f)
			ModificationInfo.SearchAll(f, s, modification_info__count)
			Parameter.SearchAll(f, s, parameter__count)
			PeptideParentProtein.SearchAll(f, s, peptide_parent_protein__count)
			IndistinguishablePeptide.SearchAll(f, s, indistinguishable_peptide__count)
			if s.IsMatched():
				matches += 1
				if BestOffset == -1:
					BestOffset = StartPos
			i += 1
		if BestOffset != -1:
			EndPos = f.tell()
			f.seek(BestOffset)
			BestInfo = Peptide.GetInfo(f)
			f.seek(BestOffset)
			return [BestOffset, BestInfo, matches]
		return [0, None, 0]

	@staticmethod
	def GetInfo(f):
		TRACEPOS("Peptide.GetInfo(): ", f.tell())
		dic = {}
		[RecordSize, modification_info__count, parameter__count, peptide_parent_protein__count, indistinguishable_peptide__count, charge, n_enzymatic_termini, initial_probability, weight, n_sibling_peptides_bin, n_instances, OptionalFlags] = struct.unpack("=IHHHHIIddiiH", f.read(4 + 2 + 2 + 2 + 2 + 4 + 4 + 8 + 8 + 4 + 4 + 2))
		dic["initial_probability"] = initial_probability
		dic["weight"] = weight
		dic["charge"] = charge
		dic["peptide"] = DecodeStringFromFile(f)
		if OptionalFlags & 0x01:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x02:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x04:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x08:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x10:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x20:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x40:
			#struct.unpack("=d", f.read(8)) #FIXME: Search this?
			f.read(8)
		if OptionalFlags & 0x80:
			#DecodeStringFromFile(f) #FIXME: Search this?
			EatStringFromFile(f)
		dic["modification_info"] = ModificationInfo.GetInfoAll(f, modification_info__count)
		Parameter.EatAll(f, parameter__count)
		dic["peptide_parent_protein"] = PeptideParentProtein.GetInfoAll(f, peptide_parent_protein__count)
		dic["indistinguishable_peptide"] = IndistinguishablePeptide.GetInfoAll(f, indistinguishable_peptide__count)
		return dic

	@staticmethod
	def GetBestInfoAll(f, count):
		off = f.tell()
		if count == 0:
			return [off, None]
		info = Peptide.GetInfo(f)
		i = 1
		while i < count:
			TRACEPOS("Peptide.GetBestInfoAll(", i, "): ", f.tell())
			f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1
		return [off, info]

	@staticmethod
	def EatAll(f, count):
		i = 0
		while i < count:
			f.seek(struct.unpack("=I", f.read(4))[0] - 4, 1)
			i += 1

class Protein(TagHandler):
	"""
	struct Protein {
		DWORD RecordSize;
		BYTE OptionalFlags;
		WORD peptide__count;
		WORD analysis_result__count;
		WORD indistinguishable_protein__count;
		WORD parameter__count;
		double probability;
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "Protein.__init__(): ")
		self.StartPos = stream.tell()
		stream.write(struct.pack("=I", 0))
		percent_coverage = TryGet(attr, "percent_coverage")
		total_number_peptides = TryGet(attr, "total_number_peptides")
		#unique_stripped_peptides = TryGet(attr, "unique_stripped_peptides")
		subsuming_protein_entry = TryGet(attr, "subsuming_protein_entry")
		pct_spectrum_ids = TryGet(attr, "pct_spectrum_ids")
		self.Flags = EncodeOptional(percent_coverage, total_number_peptides, subsuming_protein_entry, pct_spectrum_ids)#, unique_stripped_peptides)
		stream.write(struct.pack("=BHHHHd", 0, 0, 0, 0, 0, float(attr["probability"])))
		EncodeStringToFile(stream, attr["protein_name"])
		EncodeStringToFile(stream, attr["group_sibling_id"])
		if percent_coverage != None:
			stream.write(struct.pack("=d", float(percent_coverage)))
		if total_number_peptides != None:
			stream.write(struct.pack("=i", int(total_number_peptides)))
		if subsuming_protein_entry != None:
			EncodeStringToFile(stream, subsuming_protein_entry)
		if pct_spectrum_ids != None:
			EncodeStringToFile(stream, pct_spectrum_ids)
		#if unique_stripped_peptides != None:
		#	EncodeStringToFile(stream, unique_stripped_peptides)
		self.Results = 0
		self.Proteins = 0
		self.Peptides = 0
		self.Parameters = 0
		self.Annotation = None
		self.Result = None
		self.Protein = None
		self.Parameter = None

	def End(self):
		if self.Annotation != None:
			self.Flags |= 0x20
			self.Stream.write(self.Annotation.getvalue())
		if self.Parameter != None:
			self.Stream.write(self.Parameter.getvalue())
		if self.Result != None:
			self.Stream.write(self.Result.getvalue())
		if self.Protein != None:
			self.Stream.write(self.Protein.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IBHHHH", EndPos - self.StartPos, self.Flags, self.Peptides, self.Results, self.Proteins, self.Parameters))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "peptide":
			self.Peptides += 1
			return self.Stream
		if name == "annotation":
			if self.Annotation == None:
				self.Annotation = StringIO()
			else:
				raise IndexError()
			return self.Annotation
		if name == "analysis_result":
			if self.Result == None:
				self.Result = StringIO()
			self.Results += 1
			return self.Result
		if name == "indistinguishable_protein":
			if self.Protein == None:
				self.Protein = StringIO()
			self.Proteins += 1
			return self.Protein
		if name == "parameter":
			if self.Parameter == None:
				self.Parameter = StringIO()
			self.Parameters += 1
			return self.Parameter
		raise ValueError(name)
		
	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		stat.Total += count
		while i < count:
			TRACEPOS("Protein.SearchAll(", i, "): ", f.tell())
			s = stat.copy()
			StartPos = f.tell()
			[RecordSize, OptionalFlags, peptide__count, analysis_result__count, indistinguishable_protein__count, parameter__count, probability] = struct.unpack("=IBHHHHd", f.read(4 + 1 + 2 + 2 + 2 + 2 + 8))
			s.SearchItemFloat("probability", probability)
			protein_name = DecodeStringFromFile(f)
			s.SearchItemString("protein_name", protein_name)
			EatStringFromFile(f) #don't care about group_sibling_id
			if OptionalFlags & 0x01:
				#struct.unpack("=d", f.read(8))
				f.read(8) #ignore this
			if OptionalFlags & 0x02:
				#struct.unpack("=i", f.read(4))
				f.read(4) #ignore this
			if OptionalFlags & 0x04:
				EatStringFromFile(f)
			if OptionalFlags & 0x08:
				EatStringFromFile(f)
			if OptionalFlags & 0x10:
				EatStringFromFile(f)
			result = None
			protein = None
			indistinguishable = None
			PeptidePos = -1
			if not s.IsMatched():
				PeptidePos = f.tell()
				[off, info, matches] = Peptide.SearchAllBestAndCount(f, s, peptide__count)
				if info != None:
					result = Result(ResultType.Peptide)
					result.PeptideOffset = off
					result.PeptideMatches = matches
					result.HitInfo = info
					if OptionalFlags & 0x20:
						Annotation.Eat(f)
					Parameter.EatAll(f, parameter__count)
					AnalysisResult.EatAll(f, analysis_result__count)
					indistinguishable = IndistinguishableProtein.GetInfoAll(f, indistinguishable_protein__count)
					f.seek(StartPos + RecordSize)
				else:
					if OptionalFlags & 0x20:
						Annotation.Search(f, s)
					Parameter.SearchAll(f, s, parameter__count)
					AnalysisResult.SearchAll(f, s, analysis_result__count)
					[protein, indistinguishable] = IndistinguishableProtein.SearchAll(f, s, indistinguishable_protein__count)
			if result == None and s.IsMatched():
				if PeptidePos >= 0:
					f.seek(PeptidePos)
				result = Result(ResultType.Protein)
				[result.PeptideOffset, result.HitInfo] = Peptide.GetBestInfoAll(f, peptide__count)
				result.PeptideMatches = peptide__count
				if indistinguishable == None:
					if OptionalFlags & 0x20:
						Annotation.Eat(f)
					Parameter.EatAll(f, parameter__count)
					AnalysisResult.EatAll(f, analysis_result__count)
					indistinguishable = IndistinguishableProtein.GetInfoAll(f, indistinguishable_protein__count)
				f.seek(StartPos + RecordSize)
			if result != None:
				result.HitInfo["indistinguishable_protein"] = indistinguishable
				if TryGet(result.HitInfo, "protein") == None:
					if protein == None:
						result.HitInfo["protein"] = protein_name
					else:
						result.HitInfo["protein"] = protein
				else:
					result.HitInfo["indistinguishable_protein"].append(protein_name)
				result.HitInfo["probability"] = probability
				result.ProteinOffset = StartPos
				stat.Results.append(result)
			i += 1

	@staticmethod
	def GetPeptides(f, off):
		f.seek(off)
		[_1, OptionalFlags, peptide__count, _2, _3, _4, _5] = struct.unpack("=IBHHHHd", f.read(4 + 1 + 2 + 2 + 2 + 2 + 8))
		EatStringFromFile(f)
		EatStringFromFile(f)
		if OptionalFlags & 0x01:
			f.read(8)
		if OptionalFlags & 0x02:
			f.read(4)
		if OptionalFlags & 0x04:
			EatStringFromFile(f)
		if OptionalFlags & 0x08:
			EatStringFromFile(f)
		if OptionalFlags & 0x10:
			EatStringFromFile(f)
		i = 0
		peptides = []
		while i < peptide__count:
			peptides.append(Peptide.GetInfo(f))
			i += 1
		return peptides

	@staticmethod
	def GetIndistinguishable(f, off):
		f.seek(off)
		[_1, OptionalFlags, peptide__count, analysis_result__count, indistinguishable_protein__count, parameter__count, _5] = struct.unpack("=IBHHHHd", f.read(4 + 1 + 2 + 2 + 2 + 2 + 8))
		protein = DecodeStringFromFile(f)
		EatStringFromFile(f)
		if OptionalFlags & 0x01:
			f.read(8)
		if OptionalFlags & 0x02:
			f.read(4)
		if OptionalFlags & 0x04:
			EatStringFromFile(f)
		if OptionalFlags & 0x08:
			EatStringFromFile(f)
		if OptionalFlags & 0x10:
			EatStringFromFile(f)
		Peptide.EatAll(f, peptide__count)
		if OptionalFlags & 0x20:
			Annotation.Eat(f)
		Parameter.EatAll(f, parameter__count)
		AnalysisResult.EatAll(f, analysis_result__count)
		same = IndistinguishableProtein.GetInfoAll(f, indistinguishable_protein__count)
		same.insert(0, protein)
		return same

class ProteinGroup(TagHandler):
	"""
	struct ProteinGroup {
		double probability;
		WORD protein__count;
		BYTE OptionalFlags;
		String group_number;
		String pseudo_name; //ONLY IF (OptionalFlags & 0x01)
		Protein protein[protein__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ProteinGroup.__init__(): ")
		self.StartPos = stream.tell() + 8
		pseudo_name = TryGet(attr, "pseudo_name")
		stream.write(struct.pack("=dHB", float(attr["probability"]), 0, EncodeOptional(pseudo_name)))
		EncodeStringToFile(stream, attr["group_number"])
		if pseudo_name != None:
			EncodeStringToFile(stream, pseudo_name)
		self.Proteins = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Proteins))
		self.Stream.seek(EndPos)
	
	def BeginChild(self, name):
		if name == "protein":
			self.Proteins += 1
			return self.Stream
		raise ValueError(name)

	@staticmethod
	def SearchAll(f, stat, count):
		i = 0
		while i < count:
			TRACEPOS("ProteinGroup.SearchAll(", i, "): ", f.tell())
			[probability, protein__count, OptionalFlags] = struct.unpack("=dHB", f.read(8 + 2 + 1))
			EatStringFromFile(f)
			if OptionalFlags & 0x01:
				EatStringFromFile(f)
			Protein.SearchAll(f, stat, protein__count)
			i += 1

class NspDistribution(TagHandler):
	"""
	struct NspDistribution {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "NspDistribution.__init__(): ")
		nsp_lower_bound_incl = TryGet(attr, "nsp_lower_bound_incl")
		nsp_upper_bound_excl = TryGet(attr, "nsp_upper_bound_excl")
		nsp_lower_bound_excl = TryGet(attr, "nsp_lower_bound_excl")
		nsp_upper_bound_incl = TryGet(attr, "nsp_upper_bound_incl")
		alt_pos_to_neg_ratio = TryGet(attr, "alt_pos_to_neg_ratio")
		stream.write(struct.pack("=idddB", int(attr["bin_no"]), float(attr["pos_freq"]), float(attr["neg_freq"]), float(attr["pos_to_neg_ratio"]), EncodeOptional(nsp_lower_bound_incl, nsp_upper_bound_excl, nsp_lower_bound_excl, nsp_upper_bound_incl, alt_pos_to_neg_ratio)))
		if nsp_lower_bound_incl != None:
			stream.write(struct.pack("=d", float(nsp_lower_bound_incl)))
		if nsp_upper_bound_excl != None:
			EncodeStringToFile(stream, nsp_upper_bound_excl)
		if nsp_lower_bound_excl != None:
			stream.write(struct.pack("=d", float(nsp_lower_bound_excl)))
		if nsp_upper_bound_incl != None:
			EncodeStringToFile(stream, nsp_upper_bound_incl)
		if alt_pos_to_neg_ratio != None:
			stream.write(struct.pack("=d", float(alt_pos_to_neg_ratio)))

class NiDistribution(TagHandler):
	"""
	struct NiDistribution {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "NiDistribution.__init__(): ")
		ni_lower_bound_incl = TryGet(attr, "ni_lower_bound_incl")
		ni_upper_bound_excl = TryGet(attr, "ni_upper_bound_excl")
		ni_lower_bound_excl = TryGet(attr, "ni_lower_bound_excl")
		ni_upper_bound_incl = TryGet(attr, "ni_upper_bound_incl")
		alt_pos_to_neg_ratio = TryGet(attr, "alt_pos_to_neg_ratio")
		stream.write(struct.pack("=idddB", int(attr["bin_no"]), float(attr["pos_freq"]), float(attr["neg_freq"]), float(attr["pos_to_neg_ratio"]), EncodeOptional(ni_lower_bound_incl, ni_upper_bound_excl, ni_lower_bound_excl, ni_upper_bound_incl, alt_pos_to_neg_ratio)))
		if ni_lower_bound_incl != None:
			stream.write(struct.pack("=d", float(ni_lower_bound_incl)))
		if ni_upper_bound_excl != None:
			EncodeStringToFile(stream, ni_upper_bound_excl)
		if ni_lower_bound_excl != None:
			stream.write(struct.pack("=d", float(ni_lower_bound_excl)))
		if ni_upper_bound_incl != None:
			EncodeStringToFile(stream, ni_upper_bound_incl)
		if alt_pos_to_neg_ratio != None:
			stream.write(struct.pack("=d", float(alt_pos_to_neg_ratio)))

class NspInformation(TagHandler):
	"""
	struct NspInformation {
		String neighboring_bin_smoothing;
		WORD nsp_distribution;
		NspDistribution nsp_distribution[nsp_distribution__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "NspInformation.__init__(): ")
		EncodeStringToFile(stream, attr["neighboring_bin_smoothing"])
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))
		self.Distributions = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Distributions))
		self.Stream.seek(EndPos)
	
	def BeginChild(self, name):
		if name == "nsp_distribution":
			self.Distributions += 1
			return self.Stream
		raise ValueError(name)

class NiInformation(TagHandler):
	"""
	struct NiInformation {
		//String neighboring_bin_smoothing;
		WORD ni_distribution;
		NiDistribution ni_distribution[ni_distribution__count];
	}
	"""
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "NiInformation.__init__(): ")
		#EncodeStringToFile(stream, attr["neighboring_bin_smoothing"])
		self.StartPos = stream.tell()
		stream.write(struct.pack("=H", 0))
		self.Distributions = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Distributions))
		self.Stream.seek(EndPos)
	
	def BeginChild(self, name):
		if name == "ni_distribution":
			self.Distributions += 1
			return self.Stream
		raise ValueError(name)

class ProteinSummaryDataFilter(TagHandler):
	"""
	struct ProteinSummaryDataFilter {
		double min_probability;
		double sensitivity;
		double false_positive_error_rate;
		BYTE OptionalFlags;
		double predicted_num_correct; //ONLY IF (OptionalFlags & 0x01)
		double predicted_num_incorrect; //ONLY IF (OptionalFlags & 0x02)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ProteinSummaryDataFilter.__init__(): ")
		predicted_num_correct = TryGet(attr, "predicted_num_correct")
		predicted_num_incorrect = TryGet(attr, "predicted_num_incorrect")
		stream.write(struct.pack("=dddB", float(attr["min_probability"]), float(attr["sensitivity"]), float(attr["false_positive_error_rate"]), EncodeOptional(predicted_num_correct, predicted_num_incorrect)))
		if predicted_num_correct != None:
			stream.write(struct.pack("=d", float(predicted_num_correct)))
		if predicted_num_incorrect != None:
			stream.write(struct.pack("=d", float(predicted_num_incorrect)))

class ProteinprophetDetails(TagHandler):
	"""
	struct ProteinprophetDetails {
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
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ProteinprophetDetails.__init__(): ")
		self.StartPos = stream.tell()
		run_options = TryGet(attr, "run_options")
		stream.write(struct.pack("=IH", 0, 0))
		stream.write(struct.pack("=B", YNBit(attr["occam_flag"], 0x80) | YNBit(attr["groups_flag"], 0x40) | YNBit(attr["degen_flag"], 0x20) | YNBit(attr["nsp_flag"], 0x10) | EncodeOptional(run_options)))
		EncodeStringToFile(stream, attr["initial_peptide_wt_iters"])
		EncodeStringToFile(stream, attr["final_peptide_wt_iters"])
		EncodeStringToFile(stream, attr["nsp_distribution_iters"])
		if run_options != None:
			EncodeStringToFile(stream, attr["run_options"])
		self.Filters = 0
		self.NI = None
		self.Filter = None
		self.State = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IH", EndPos - self.StartPos, self.Filters))
		self.Stream.seek(EndPos)
		if self.State < 2:
			raise IndexError()
		if self.NI != None:
			self.Stream.write(self.NI.getvalue())
		if self.Filter != None:
			self.Stream.write(self.Filter.getvalue())
	
	def BeginChild(self, name):
		if name == "nsp_information":
			self.State = 1
			return self.Stream
		if name == "ni_information":
			if self.State == 1:
				self.State = 2
				return self.Stream
			else:
				self.NI = StringIO()
				return self.NI
		if name == "protein_summary_data_filter":
			self.Filters += 1
			if self.State == 2:
				return self.Stream
			elif self.State == 1:
				if self.NI != None:
					self.Stream.write(self.NI.getvalue())
					self.NI = None
					if self.Filter != None:
						self.Stream.write(self.Filter.getvalue())
						self.Filter = None
					return self.Stream
			if self.Filter == None:
				self.Filter = StringIO()
			return self.Filter
		raise ValueError(name)

class ProgramDetails(TagHandler):
	"""
	struct Details {
		BYTE Type;
		Object detail;
	}
	struct ProgramDetails {
		String analysis;
		String time;
		//String version; //ONLY IF (OptionalFlags & 0x01)
		WORD details__count;
		Details details[details__count];
	}
	"""
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ProgramDetails.__init__(): ")
		EncodeStringToFile(stream, attr["analysis"])
		EncodeStringToFile(stream, attr["time"])
		#EncodeStringToFile(stream, attr["version"])
		stream.write(struct.pack("=H", 0))
		self.StartPos = stream.tell()
		self.Details = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Details))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		Details = { "proteinprophet_details": 0 }
		Type = 0xFF
		try:
			Type = Details[name]
		except:
			print "Unknown details type ", name
			return NullStream()
		self.Stream.write(struct.pack("=B", Type))
		self.Details += 1
		return self.Stream
		
class DataFilter(TagHandler):
	"""
	struct DataFilter {
		String number;
		String parent_file;
		String description;
		//String windows_parent; //ONLY IF (OptionalFlags & 0x01)
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "DataFilter.__init__(): ")
		EncodeStringToFile(stream, attr["number"])
		EncodeStringToFile(stream, attr["parent_file"])
		EncodeStringToFile(stream, attr["description"])

class DatasetDerivation(TagHandler):
	"""
	struct DatasetDerivation {
		String generation_no;
		WORD data_filter__count;
		DataFilter data_filter[data_filter__count];
	}
	"""
	
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "DatasetDerivation.__init__(): ")
		EncodeStringToFile(stream, attr["generation_no"])
		stream.write(struct.pack("=H", 0))
		self.StartPos = stream.tell()
		self.Filters = 0

	def BeginChild(self, name):
		if name == "data_filter":
			self.Filters += 1
			return self.Stream
		raise ValueError(name)

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=H", self.Filters))
		self.Stream.seek(EndPos)

class AnalysisSummary(TagHandler):
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "AnalysisSummary.__init__(): ")
		#stream.write(struct.pack("=B", GetEngineCode(attr["analysis"])))
		return #FIXME: Do we care about this?

	def BeginChild(self, name):
		#FIXME: Do we care about this?
		return None

class ProteinSummaryHeader(TagHandler):
	"""
	struct ProteinSummaryHeader {
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
	}
	"""
	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ProteinSummaryHeader.__init__(): ")
		win_cyg_reference_database = TryGet(attr, "win_cyg_reference_database")
		residue_substitution_list = TryGet(attr, "residue_substitution_list")
		organism = TryGet(attr, "organism")
		win_cyg_source_files = TryGet(attr, "win_cyg_source_files")
		source_file_xtn = TryGet(attr, "source_file_xtn")
		total_no_spectrum_ids = TryGet(attr, "total_no_spectrum_ids")
		stream.write(struct.pack("=ddddiiiiiB", float(attr["min_peptide_probability"]), float(attr["min_peptide_probability"]), float(attr["num_predicted_correct_prots"]), float(attr["initial_min_peptide_prob"]), int(attr["num_input_1_spectra"]), int(attr["num_input_2_spectra"]), int(attr["num_input_3_spectra"]), int(attr["num_input_4_spectra"]), int(attr["num_input_5_spectra"]), EncodeOptional(win_cyg_reference_database, residue_substitution_list, organism, win_cyg_source_files, source_file_xtn, total_no_spectrum_ids)))
		EncodeStringToFile(stream, attr["reference_database"])
		EncodeStringToFile(stream, attr["source_files"])
		EncodeStringToFile(stream, attr["source_files_alt"])
		EncodeStringToFile(stream, attr["sample_enzyme"])
		if win_cyg_reference_database != None:
			EncodeStringToFile(stream, win_cyg_reference_database)
		if residue_substitution_list != None:
			EncodeStringToFile(stream, residue_substitution_list)
		if organism != None:
			EncodeStringToFile(stream, organism)
		if win_cyg_source_files != None:
			EncodeStringToFile(stream, win_cyg_source_files)
		if source_file_xtn != None:
			EncodeStringToFile(stream, source_file_xtn)
		if total_no_spectrum_ids != None:
			EncodeStringToFile(stream, total_no_spectrum_ids)

	def BeginChild(self, name):
		if name == "program_details":
			return self.Stream
		raise ValueError(name)

class ProteinSummary(TagHandler):
	"""
	struct ProteinSummary {
		WORD protein_group__count;
		WORD dataset_derivation__count;
		WORD analysis_summary__count;
		String summary_xml;
		ProteinGroup protein_group[protein_group__count];
		ProteinSummaryHeader protein_summary_header;
		DatasetDerivation dataset_derivation[dataset_derivation__count];
		AnalysisSummary analysis_summary[analysis_summary__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ProteinSummary.__init__(): ")
		self.Stat = stat
		self.StartPos = stream.tell()
		stream.write(struct.pack("=HHH", 0, 0, 0))
		EncodeStringToFile(stream, attr["summary_xml"])
		self.Groups = 0
		self.Datasets = 0
		self.Summaries = 0
		self.ProteinSummaryHeader = StringIO()
		self.DatasetDerivation = None
		self.AnalysisSummary = None

	def End(self):
		self.Stream.write(self.ProteinSummaryHeader.getvalue())
		if self.DatasetDerivation != None:
			self.Stream.write(self.DatasetDerivation.getvalue())
		if self.AnalysisSummary != None:
			self.Stream.write(self.AnalysisSummary.getvalue())
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=HHH", self.Groups, self.Datasets, self.Summaries))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "protein_group":
			self.Groups += 1
			return self.Stream
		elif name == "protein_summary_header":
			return self.ProteinSummaryHeader
		elif name == "dataset_derivation":
			if self.DatasetDerivation == None:
				self.DatasetDerivation = StringIO()
			self.Datasets += 1
			return self.DatasetDerivation
		elif name == "analysis_summary":
			if self.AnalysisSummary == None:
				self.AnalysisSummary = StringIO()
			self.Summaries += 1
			return self.AnalysisSummary
		raise ValueError(name)

	@staticmethod
	def Search(f, stat):
		"""
		To search everything relevent, make dic { None: "search terms" }
		"""
		TRACEPOS("ProteinSummary.Search(): ", f.tell())
		[protein_group__count, dataset_derivation__count, analysis_summary__count] = struct.unpack("=HHH", f.read(2 + 2 + 2))
		EatStringFromFile(f) #don't bother searching the summary filename
		if protein_group__count > 0:
			ProteinGroup.SearchAll(f, stat, protein_group__count)
		

#externally usable functions

def ConvertFilename(FileName):
	return os.path.splitext(FileName)[0] + ".protBIN"

def IsConverted(FileName):
	return os.path.isfile(ConvertFilename(FileName))

def ToBinary(FileName, Dest = None, Links = None):
	if Dest == None:
		Dest = open(ConvertFilename(FileName), "w")
	#Dest.write(struct.pack("=I", 0))
	stat = EncodingStatus(Links)
	parser = xml.sax.make_parser()
	parser.setFeature("http://xml.org/sax/features/external-general-entities", False)
	parser.setContentHandler(SaxHandler(Dest, stat))
	parser.parse(open(FileName, "r"))
	Dest.close()

def SearchBasic(FileName, terms):
	f = open(FileName, "r")
	#f.seek(4) #skip the peptide index offset
	stat = SearchStatus({ None: SplitPhrase(terms.upper()) })
	ProteinSummary.Search(f, stat)
	f.close()
	#PrintResults(stat.Results)
	return [0, stat.Total, stat.Results]

def SearchAdvanced(FileName, terms_dict):
	f = open(FileName, "r")
	#f.seek(4) #skip the peptide index offset
	terms = {}
	for k, v in terms_dict.items():
		terms[k] = SplitPhrase(v.upper())
	stat = SearchStatus(terms)
	ProteinSummary.Search(f, stat)
	f.close()
	#PrintResults(stat.Results)
	return [0, stat.Total, stat.Results]

def select_protein(BaseFile, query):
	f = open(BaseFile + "_" + query["n"], "r")
	peptides = Protein.GetPeptides(f, int(query["off"]))
	f.close()
	return peptides

def select_indistinguishable_protein(BaseFile, query):
	f = open(BaseFile + "_" + query["n"], "r")
	proteins = Protein.GetIndistinguishable(f, int(query["off"]))
	f.close()
	return proteins

def select_indistinguishable_peptide(BaseFile, query):
	f = open(BaseFile + "_" + query["n"], "r")
	peptides = Peptide.GetIndistinguishable(f, int(query["off"]))
	f.close()
	return peptides

def DefaultSortColumn(scores):
	return "probability"

#FIXME: DEBUG
def PrintResults(results):
	print("Results:")
	for r in results:
		print(r)
