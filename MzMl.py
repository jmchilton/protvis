import zlib
import base64

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
			"msms_pipeline_analysis": MsmsPipelineAnalysis,
			"sequence_search_constraint": SequenceSearchConstraint,
			"terminal_modification": TerminalModification,
			"xpressratio_timestamp": XpressratioTimestamp,
			"dataset_derivation": DatasetDerivation }


#XML element classes
class CVParamType(TagHandler):
	""" //Written to a collection, not a stream
	class CVParamType {
		String cvRef;
		DWORD accession;
		String value; //Optional
		String unitCvRef; //Optional
		DWORD unitAccession; //Optional
	}
	"""

	def __init__(self, stream, statprotein_summary_header, attr):
		TRACEPOSXML(stream, "CVParam.__init__(): ")
		self.cvRef = attr["cvRef"]
		self.accession = attr["accession"]
		self.value = TryGet(attr, "value")
		self.unitCvRef = TryGet(attr, "unitCvRef")
		self.unitAccession = TryGet(attr, "unitAccession")
		if self.accession[:len(self.cvRef) + 1] != self.cvRef + ":":
			raise ValueError(self.accession)
		self.accession = int(self.accession[len(self.cvRef) + 1:]
		if self.unitAccession[:len(self.unitCvRef) + 1] != self.unitCvRef + ":":
			raise ValueError(self.unitAccession)
		self.unitAccession = int(self.unitAccession[len(self.unitCvRef) + 1:]
		stream.append(self)

class UserParamType(TagHandler):
	""" //Written to a collection, not a stream
	class UserParamType {
		String name;
		String type; //Optional
		String value; //Optional
		String unitCvRef; //Optional
		DWORD unitAccession; //Optional
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "UserParamType.__init__(): ")
		self.name = attr["name"]
		self.type = attr["type"]
		self.value = TryGet(attr, "value")
		self.unitCvRef = TryGet(attr, "unitCvRef")
		self.unitAccession = TryGet(attr, "unitAccession")
		if self.unitAccession[:len(self.unitCvRef) + 1] != self.unitCvRef + ":":
			raise ValueError(self.unitAccession)
		self.unitAccession = int(self.unitAccession[len(self.unitCvRef) + 1:]
		stream.append(self)

class ReferenceableParamGroupType(TagHandler):
	""" //Sorted as a collection
	class ReferenceableParamGroupType {
		ID id;
		CVParamType cvParam[];
		UserParamType userParam[];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ReferenceableParamGroupType.__init__(): ")
		self.id = attr["id"]
		self.cvParam = []
		self.userParam = []
		stream.append(self)

	def BeginChild(self, name):
		if name == "cvParam":
			return self.cvParam
		if name == "userParam":
			return self.userParam
		raise ValueError(name)

class ReferenceableParamGroupRefType(TagHandler):
	""" //Sorted as a collection
	class ReferenceableParamGroupRefType {
		IDREF ref;
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ReferenceableParamGroupRefType.__init__(): ")
		self.ref = attr["ref"]
		stream.append(self)

class ParamGroupType(TagHandler):
	""" //Sorted as a collection
	class ParamGroupType {
		ReferenceableParamGroupRefType referenceableParamGroupRef[];
		CVParamType cvParam[];
		UserParamType userParam[];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ParamGroupType.__init__(): ")
		self.referenceableParamGroupRef = []
		self.cvParam = []
		self.userParam = []

	def BeginChild(self, name):
		if name == "referenceableParamGroupRef":
			return self.referenceableParamGroupRef
		if name == "cvParam":
			return self.cvParam
		if name == "userParam":
			return self.userParam
		raise ValueError(name)


class BinaryType(TagHandler):
class BinaryDataArrayType(TagHandler):
class BinaryDataArrayListType(TagHandler):
class ScanType(TagHandler):
	"""
	struct ScanType {
		BYTE OptionalFlags;
		String spectrumRef; //ONLY IF (OptionalFlags & 0x01)
		IDREF sourceFileRef; //ONLY IF (OptionalFlags & 0x02)
		String externalSpectrumID; //ONLY IF (OptionalFlags & 0x04)
		IDREF instrumentConfigurationRef; //ONLY IF (OptionalFlags & 0x08)
		ScanWindowListType scanWindowList; //ONLY IF (OptionalFlags & 0x10)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ScanType.__init__(): ")
		self.StartPos = stream.tell()
		spectrumRef = TryGet(attr, "spectrumRef");
		sourceFileRef = TryGet(attr, "sourceFileRef");
		externalSpectrumID = TryGet(attr, "externalSpectrumID");
		instrumentConfigurationRef = TryGet(attr, "instrumentConfigurationRef");
		self.OptionalFlags = EncodeOptional(spectrumRef, sourceFileRef, externalSpectrumID, instrumentConfigurationRef)
		stream.write(struct.pack("=B", 0))
		if spectrumRef != None:
			EncodeStringToFile(stream, spectrumRef)
		if sourceFileRef != None:
			EncodeStringToFile(stream, sourceFileRef)
		if externalSpectrumID != None:
			EncodeStringToFile(stream, externalSpectrumID)
		if instrumentConfigurationRef != None:
			EncodeStringToFile(stream, instrumentConfigurationRef)

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=B", self.OptionalFlags))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "scanWindowList":
			self.OptionalFlags |= 0x10
			return self.Stream
		raise ValueError(name)
		
class ScanListType(TagHandler):
	"""
	struct ScanListType {
		DWORD RecordSize;
		WORD scan__count;
		ScanType scan[scan__count];
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "ScanListType.__init__(): ")
		self.StartPos = stream.tell()
		stream.write(struct.pack("=IH", 0, 0))
		self.Scans = 0

	def End(self):
		EndPos = self.Stream.tell()
		self.Stream.seek(self.StartPos)
		self.Stream.write(struct.pack("=IH", EndPos - self.StartPos, self.Scans))
		self.Stream.seek(EndPos)

	def BeginChild(self, name):
		if name == "scan":
			return self.Stream
		raise ValueError(name)
		
class SpectrumType(TagHandler):
class SpectrumListType(TagHandler):
	"""
	struct SpectrumListType {
		DWORD spectrum__count;
		IDREF defaultDataProcessingRef;
		SpectrumType spectrum;
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "SpectrumListType.__init__(): ")

	def BeginChild(self, name):
		if name == "spectrum":
			return self.Stream
		raise ValueError(name)

class RunType(TagHandler):
	"""
	struct RunType {
		ID id;
		IDREF defaultInstrumentConfigurationRef;
		BYTE OptionalFlags;
		IDREF defaultSourceFileRef; //ONLY IF (OptionalFlags & 0x01)
		IDREF sampleRef; //ONLY IF (OptionalFlags & 0x02)
		DateTime startTimeStamp; //ONLY IF (OptionalFlags & 0x04)
		SpectrumListType spectrumList; //ONLY IF (OptionalFlags & 0x08)
		ChromatogramListType chromatogramList; //ONLY IF (OptionalFlags & 0x10)
	}
	"""

	def __init__(self, stream, stat, attr):
		TRACEPOSXML(stream, "RunType.__init__(): ")



