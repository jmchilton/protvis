import binascii
import os
import xml.sax
import xml.parsers.expat

GalaxyPath = "/".join(os.path.abspath(__file__).split("/")[:-3]) + "/"
IncludedFiles = {}

def Echo(x):
	return x
binascii.hexlify = Echo

class SaxHandler(xml.sax.ContentHandler):
	def __init__(self, elems, handler):
		self.Elems = elems
		self.Handler = handler
		
	def startElement(self, name, attrs):
		try:
			if name in self.Elems:
				self.Handler(name, attrs)
		except:
			return

	def endElement(self, name):
		return

def SearchXml(fname, elems, handler):
	parser = xml.sax.make_parser()
	parser.setFeature("http://xml.org/sax/features/external-general-entities", False)
	parser.setContentHandler(SaxHandler(elems, handler))
	f = open(fname, "r")
	try:
		parser.parse(f)
		f.close()
	except StopIteration:
		f.close()
	except:
		f.close()
		raise

class FileType:
	#higher numbers are more specific than lower numbers. e.g. PEPXML_INTERPROPHET > PEPXML_COMPARE > PEPXML > UNKNOWN
	UNKNOWN = 0
	MZML = 1
	MGF = 2
	PEPXML = 3
	PEPXML_MASCOT = 4
	PEPXML_OMSSA = 5
	PEPXML_XTANDEM = 6
	PEPXML_COMPARE = 7
	PEPXML_PEPTIDEPROPHET = 8
	PEPXML_INTERPROPHET = 9
	PROTXML = 10
	PROTXML_PROTEINPROPHET = 11

	@staticmethod
	def Name(t):
		switch = {
			FileType.MZML: "mzml",
			FileType.MGF: "mgf",
			FileType.PEPXML: "pepxml",
			FileType.PEPXML_MASCOT: "pepmas",
			FileType.PEPXML_OMSSA: "pepoms",
			FileType.PEPXML_XTANDEM: "pepxta",
			FileType.PEPXML_COMPARE: "pepcmp",
			FileType.PEPXML_PEPTIDEPROPHET: "peppep",
			FileType.PEPXML_INTERPROPHET: "pepint",
			FileType.PROTXML: "protxml",
			FileType.PROTXML_PROTEINPROPHET: "protpro"
		}
		try:
			return switch[t]
		except:
			return "aux"

	@staticmethod
	def FromExtensions(exts):
		if "protxml" in exts or "prot" in exts:
			return FileType.PROTXML
		if "pepxml" in exts or "pep" in exts:
			return FileType.PEPXML
		if "mzml" in exts or "mzxml" in exts:
			return FileType.MZML
		elif "mgf" in exts:
			return FileType.MGF
		return FileType.UNKNOWN

def ValidateFilename(fname, exts = None):
	class ValidFile:
		def __init__(self, Name, Type, Exists):
			self.Name = Name
			self.Type = Type
			self.Exists = Exists

	fname = os.path.abspath(fname)
	if not fname.startswith(GalaxyPath):
		raise ValueError(fname)
	f = None
	ext = []
	while f == None:
		try:
			t = IncludedFiles[fname]
			_t = FileType.FromExtensions(ext)
			if _t > t:
				t = _t
				IncludedFiles[fname] = _t
			return ValidFile(fname, t, True)
		except:
			if os.path.exists(fname):
				t = FileType.FromExtensions(ext)
				IncludedFiles[fname] = t
				return ValidFile(fname, t, False)
			else:
				if exts == None:
					raise IOError(fname)
				split = os.path.splitext(fname)
				if len(split[1]) > 0:
					e = split[1][1:].lower()
					if e in exts:
						ext.append(e)
						fname = split[0]
					else:
						raise IOError(fname)
				else:
					raise IOError(fname)

def MzmlReferences(fname):
	return

def MgfReferences(fname):
	return

def PepReferences(fname):
	files = []
	def _HandleProtFind(name, attr):
		if name == "msms_run_summary":
			t = attr["raw_data_type"]
			if t[0] == ".":
				t = t[1:]
			ext = t
			t = t.lower()
			if t == "mgf":
				t = FileType.MGF
			elif t in ["mzml", "mzxml"]:
				t = FileType.MZML
			else:
				t = attr["raw_data"]
				if t[0] == ".":
					t = t[1:]
				ext = t
				t = t.lower()
				if t == "mgf":
					t = FileType.MGF
				elif t in ["mzml", "mzxml"]:
					t = FileType.MZML
				else:
					print "Unknown file type: ", attr["base_name"]
					t = FileType.UNKNOWN
			files.append([attr["base_name"] + "." + ext, t])
			raise StopIteration()
		elif name == "inputfile":
			files.append([attr["name"], FileType.UNKNOWN])
	SearchXml(fname, ["msms_run_summary", "inputfile"], _HandleProtFind)
	for f in files:
		info = ValidateFilename(f[0], ["mzml", "mzxml", "mgf", "pepxml", "pep", "xml"])
		if info.Type == FileType.PEPXML:
			IncludedFiles[fname] = FileType.PEPXML_COMPARE
		t = info.Type
		if f[1] != FileType.UNKNOWN:
			t = f[1]
		if not info.Exists:
			_References(t, info.Name)

def ProtReferences(fname):
	files = []
	def _HandleProtFind(name, attr):
		files.append(attr["source_files"]) #FIXME: this is a plural, how are the names seperated?
		files.append(attr["source_files_alt"]) #FIXME: this is a plural, how are the names seperated?
		raise StopIteration()
	SearchXml(fname, ["protein_summary_header"], _HandleProtFind)
	for f in files:
		info = ValidateFilename(f, ["pepxml", "pep", "xml"])
		if not info.Exists:
			PepReferences(info.Name)

def _References(t, fname):
	switch = {
		FileType.MZML: MzmlReferences,
		FileType.MGF: MgfReferences,
		FileType.PEPXML: PepReferences,
		FileType.PEPXML_MASCOT: PepReferences,
		FileType.PEPXML_OMSSA: PepReferences,
		FileType.PEPXML_XTANDEM: PepReferences,
		FileType.PEPXML_PEPTIDEPROPHET: PepReferences,
		FileType.PEPXML_INTERPROPHET: PepReferences,
		FileType.PROTXML: ProtReferences,
		FileType.PROTXML_PROTEINPROPHET: ProtReferences
	}
	try:
		func = switch[t]
	except:
		return "aux=" + binascii.hexlify(fname)
	return func(fname)

def Build():
	return "files=" + ";".join([FileType.Name(t) + ":" + binascii.hexlify(f) for f, t in IncludedFiles.items()])

def LoadChainProt(fname):
	IncludedFiles[fname] = FileType.PROTXML
	ProtReferences(fname)
	return Build()

def LoadChainPep(fname):
	IncludedFiles[fname] = FileType.PEPXML
	PepReferences(fname)
	return Build()

def LoadChainMgf(fname):
	IncludedFiles[fname] = FileType.MGF
	MgfReferences(fname)
	return Build()

def LoadChainMzml(fname):
	IncludedFiles[fname] = FileType.MZML
	MzmlReferences(fname)
	return Build()
