import binascii
import os
import xml.sax
import xml.parsers.expat
import conf;

GalaxyPath = conf.GALAXY_ROOT + "/database/files/"

class IncludedFile:
	class FileInfo:
		def __init__(self, t, index, level):
			self.Type = t
			self.Index = index
			self.Level = level
			self.Depends = []

		def Refernece(self, index, level):
			if (level > self.Level):
				self.Level = level
				self.Index = index
				return True
			return False

	def __init__(self, fname, ftype):
		self.Files = { fname: IncludedFile.FileInfo(ftype, 0, 0) }
		self.Counter = 1
		self.Level = 0

	def Add(self, fname, ftype):
		self.Files[fname] = IncludedFile.FileInfo(ftype, self.Counter, self.Level)
		self.Counter += 1

	def Get(self, fname):
		f = self.Files[fname]
		if (f.Reference(self.Counter, self.Level)):
			self.Counter += 1
		return f

	def Set(self, fname, ftype):
		self.Files[fname].Type = ftype

	def StepIn(self):
		self.Level += 1

	def StepOut(self):
		self.Level -= 1

	def Items(self):
		def IndexOf(items, item):
			n = 0
			for i in items:
				if i[0] == item:
					return n
				n += 1
			return -1

		class IncludedFile:
			def __init__(self, f, t, deps):
				self.Name = f
				self.Type = t
				self.Depends = deps

		files = [[f, fi] for f, fi in self.Files.items()]
		files = sorted(files, key=lambda flist: flist[1].Index, reverse=True)
		return [IncludedFile(f, fi.Type, list(set([IndexOf(files, d) for d in fi.Depends]))) for f, fi in files]

	def SetDepends(self, fname, depends):
		self.Files[fname].Depends = depends

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
	MISSING = -1
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
	def NameBasic(t):
		switch = {
			FileType.MZML: "mzml",
			FileType.MGF: "mgf",
			FileType.PEPXML: "pep",
			FileType.PEPXML_MASCOT: "pep",
			FileType.PEPXML_OMSSA: "pep",
			FileType.PEPXML_XTANDEM: "pep",
			FileType.PEPXML_COMPARE: "pep",
			FileType.PEPXML_PEPTIDEPROPHET: "pep",
			FileType.PEPXML_INTERPROPHET: "pep",
			FileType.PROTXML: "prot",
			FileType.PROTXML_PROTEINPROPHET: "prot"
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

def ValidateFilename(IncludedFiles, fname, exts = None):
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
			t = IncludedFiles.Get(fname)
			_t = FileType.FromExtensions(ext)
			if _t > t:
				t = _t
				IncludedFiles.Set(fname, _t)
			return ValidFile(fname, t, True)
		except:
			if os.path.exists(fname):
				t = FileType.FromExtensions(ext)
				IncludedFiles.Add(fname, t)
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

def MzmlReferences(fname, IncludedFiles):
	IncludedFiles.StepIn()
	IncludedFiles.StepOut()

def MgfReferences(fname, IncludedFiles):
	IncludedFiles.StepIn()
	IncludedFiles.StepOut()

def PepReferences(fname, IncludedFiles):
	IncludedFiles.StepIn()
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
	deps = range(len(files))
	for i in deps:
		f = files[i]
		try:
			info = ValidateFilename(IncludedFiles, f[0], ["mzml", "mzxml", "mgf", "pepxml", "pep", "xml"])
			deps[i] = info.Name
			if info.Type == FileType.PEPXML:
				IncludedFiles.Set(fname, FileType.PEPXML_COMPARE)
			t = info.Type
			if f[1] != FileType.UNKNOWN:
				t = f[1]
				IncludedFiles.Set(info.Name, f[1])
			if not info.Exists:
				_References(t, info.Name, IncludedFiles)
		except:
			deps[i] = None
			print("Can't open referenced file: " + f[0])
	IncludedFiles.SetDepends(fname, deps)
	IncludedFiles.StepOut()

def ProtReferences(fname, IncludedFiles):
	IncludedFiles.StepIn()
	files = []
	def _HandleProtFind(name, attr):
		files.append(attr["source_files"]) #FIXME: this is a plural, how are the names seperated?
		files.append(attr["source_files_alt"]) #FIXME: this is a plural, how are the names seperated?
		raise StopIteration()
	SearchXml(fname, ["protein_summary_header"], _HandleProtFind)
	deps = range(len(files))
	for i in deps:
		f = files[i]
		try:
			info = ValidateFilename(IncludedFiles, f, ["pepxml", "pep", "xml"])
			deps[i] = info.Name
			#IncludedFiles.Add(info.Name, FileType.PEPXML)
			if not info.Exists:
				PepReferences(info.Name, IncludedFiles)
		except:
			deps[i] = None
			print("Can't open referenced file: " + f)
	IncludedFiles.SetDepends(fname, deps)
	IncludedFiles.StepOut()

def _References(t, fname, IncludedFiles):
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
		return
	return func(fname, IncludedFiles)

def LoadChainProt(fname):
	if not os.path.abspath(fname).startswith(GalaxyPath):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.PROTXML)
	ProtReferences(fname, IncludedFiles)
	return IncludedFiles.Items()

def LoadChainPep(fname):
	if not os.path.abspath(fname).startswith(GalaxyPath):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.PEPXML)
	PepReferences(fname, IncludedFiles)
	return IncludedFiles.Items()

def LoadChainMgf(fname):
	if not os.path.abspath(fname).startswith(GalaxyPath):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.MGF)
	MgfReferences(fname, IncludedFiles)
	return IncludedFiles.Items()

def LoadChainMzml(fname):
	if not os.path.abspath(fname).startswith(GalaxyPath):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.MZML)
	MzmlReferences(fname, IncludedFiles)
	return IncludedFiles.Items()
