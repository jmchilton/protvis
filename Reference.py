import binascii
import os
import xml.sax
import xml.parsers.expat
import parameters
import struct
from Common import *
import ProtXML, PepXML, MGF, MzML
import subprocess

def EnsureWhitelistFile(fname):
	fname = os.path.abspath(fname)
	for d in parameters.PATH_WHITELIST:
		if fname.startswith(d):
			return True
	return False

class IncludedFile:
	class FileInfo:
		def __init__(self, t, index, level, stream):
			self.Type = t
			self.Index = index
			self.Level = level
			self.Stream = stream
			self.Depends = []

		def Reference(self, index, level):
			if (level > self.Level):
				self.Level = level
				self.Index = index
				return True
			return False

	def __init__(self, fname = None, ftype = None, stream = None):
		if fname != None and ftype != None:
			self.Files = { unicode(fname): IncludedFile.FileInfo(ftype, 0, 0, stream) }
		else:
			self.Files = {}
		self.Counter = 1
		self.Level = 0

	def Add(self, fname, ftype, stream = None):
		self.Files[unicode(fname)] = IncludedFile.FileInfo(ftype, self.Counter, self.Level, stream)
		self.Counter += 1

	def Get(self, fname):
		f = self.Files[unicode(fname)]
		if (f.Reference(self.Counter, self.Level)):
			self.Counter += 1
		return f

	def GetSilent(self, fname):
		return self.Files[unicode(fname)]

	def Set(self, fname, ftype):
		self.Files[unicode(fname)].Type = ftype

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
				elif (i[1].Type & ~FileType.MISSING) != FileType.DATABASE:
					n += 1
			return -1

		class IncludedFile:
			def __init__(self, f, t, deps, stream):
				self.Name = f
				self.Type = t
				self.Depends = deps
				self.Stream = stream

		#files = [[f, fi] for f, fi in self.Files.items()]
		files = []
		dbs = []
		for f, fi in self.Files.items():
			if (fi.Type & ~FileType.MISSING) == FileType.DATABASE:
				dbs.append([f, fi])
			else:
				files.append([f, fi]);
		files = sorted(files, key=lambda flist: flist[1].Index, reverse=True) + dbs
		return [IncludedFile(f, fi.Type, list(set([IndexOf(files, unicode(d)) for d in fi.Depends])), fi.Stream) for f, fi in files]

	def SetDepends(self, fname, depends):
		self.Files[unicode(fname)].Depends = depends

	def TouchDeps(self, fname):
		f = self.Files[unicode(fname)]
		if (f.Reference(self.Counter, self.Level)):
			self.Counter += 1
		for d in f.Depends:
			self.TouchDeps(d)

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
	def DummyClose(f):
		return
	parser = xml.sax.make_parser()
	parser.setFeature("http://xml.org/sax/features/external-general-entities", False)
	parser.setContentHandler(SaxHandler(elems, handler))
	try:
		f = fname.Stream
		f.seek(0)
		close = DummyClose
	except:
		f = open(fname, "r")
		close = file.close
	try:
		parser.parse(f)
		close(f)
	except StopIteration:
		close(f)
	except:
		close(f)
		raise

class FileType:
	#higher numbers are more specific than lower numbers. e.g. PEPXML_INTERPROPHET > PEPXML_COMPARE > PEPXML > UNKNOWN
	MISSING = 0x80 #any types with 0x80 set are missing
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
	DATABASE = 0x7F

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
			FileType.PROTXML_PROTEINPROPHET: "protpro",
			FileType.DATABASE: "db"
		}
		try:
			return switch[t & ~FileType.MISSING]
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
			FileType.PROTXML_PROTEINPROPHET: "prot",
			FileType.DATABASE: "db"
		}
		try:
			return switch[t & ~FileType.MISSING]
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
		if "mgf" in exts:
			return FileType.MGF
		if "fasta" in exts:
			return FileType.DATABASE
		return FileType.UNKNOWN

class FileLinks:
	"""
	struct Link {
		BYTE type;
		WORD links__count;
		WORD links[links__count];
		String name;
	}
	struct FileLinks {
		DWORD files__count;
		DWORD databases__count;
		Link files[files__count];
		String databases[databases__count];
	}
	"""
	class Link:
		def __init__(self, f):
			[self.Type, deps] = struct.unpack("=BH", f.read(1 + 2))
			self.Depends = [struct.unpack("=H", f.read(2))[0] for i in xrange(deps)]
			self.Name = DecodeStringFromFile(f)

	def __init__(self, IndexFile):
		try:
			f = open(IndexFile, "r")
		except:
			raise HTTPNotFound_Data(os.path.split(IndexFile)[1])
		[files, dbs] = struct.unpack("=II", f.read(4 + 4))
		self.Index = IndexFile
		self.Links = [FileLinks.Link(f) for i in xrange(files)]
		self.Databases = [DecodeStringFromFile(f) for i in xrange(dbs)]

	def __getitem__(self, i):
		if i == 0xFFFF:
			return None
		return self.Links[i]

	def __len__(self):
		return len(self.Links)

	def GetTopFile(self):
		return self.Index + "_" + str(len(self.Links) - 1)

	def GetTopIndex(self):
		return len(self.Links) - 1

	def GetTopType(self):
		return self.Links[len(self.Links) - 1].Type

	def GetTopName(self):
		return self.Links[len(self.Links) - 1].Name

	def GetTopInfo(self):
		def ExpandDepends(nodes, node):
			deps = nodes[node]
			isdep = False
			for n in nodes:
				if n != node and node in nodes[n]:
					nodes[n] = nodes[n].union(deps)
					isdep = True
			return isdep

		nodes = {i: set(self.Links[i].Depends) for i in xrange(len(self.Links))}
		deps = []
		for i in nodes:
			if ExpandDepends(nodes, i):
				deps.append(i)
		for i in deps:
			del nodes[i]
		maxval = -1
		maxi = 0
		for i in nodes:
			if len(nodes[i]) > maxval:
				maxval = len(nodes[i])
				maxi = i
		l = self.Links[maxi]
		return { "name": l.Name, "type": l.Type, "index": maxi }

	def GetInfo(self, index):
		l = self.Links[index]
		return { "name": l.Name, "type": l.Type, "index": index }

	def Get(self, index):
		return self.Links[index]

	def GetParser(self, index):
		return GetTypeParser(self.Links[index].Type)

	def Types(self):
		flags = 0
		for l in self.Links:
			if l.Type >= FileType.PROTXML:
				flags |= 8
			elif l.Type >= FileType.PEPXML:
				flags |= 4
			elif l.Type == FileType.MGF:
				flags |= 2
			elif l.Type == FileType.MZML:
				flags |= 1
		return flags
		

def GetTypeParser(datatype):
	modules = {
		FileType.MZML: MzML,
		FileType.MGF: MGF,
		FileType.PEPXML: PepXML, FileType.PEPXML_MASCOT: PepXML, FileType.PEPXML_OMSSA: PepXML, FileType.PEPXML_XTANDEM: PepXML, FileType.PEPXML_COMPARE: PepXML, FileType.PEPXML_PEPTIDEPROPHET: PepXML, FileType.PEPXML_INTERPROPHET: PepXML,
		FileType.PROTXML: ProtXML, FileType.PROTXML_PROTEINPROPHET: ProtXML
	}
	try:
		return modules[datatype]
	except:
		return None

class ValidFile:
	def __init__(self, Name, Type, Exists):
		self.Name = Name
		self.Type = Type
		self.Exists = Exists

def ValidateFilename(IncludedFiles, fname, exts = None):
	if not EnsureWhitelistFile(fname):
		raise ValueError(fname)
	ext = []
	while True:
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

def DbReferences(fname, IncludedFiles, Validator):
	def TestIndex(db):
		p = subprocess.Popen(["bin/blastdbcmd", "-db", fname, "-info"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		(out, err) = p.communicate()
		p.stderr.close()
		p.stdout.close()
		return p.wait() == 0

	fname = os.path.abspath(fname)
	if not EnsureWhitelistFile(fname):
		raise ValueError(fname)
	IncludedFiles.StepIn()
	if not TestIndex(fname):
		link = os.path.split(fname)
		link = abs(hash(link[0])) + "_" + link[1]
		IncludedFiles.GetSilent(fname).Stream = link
		if not TestIndex(link):
			os.symlink(fname, link)
			subprocess.call(["bin/makeblastdb", "-in", link, "-parse_seqids"])
	IncludedFiles.StepOut()

def MzmlReferences(fname, IncludedFiles, Validator):
	IncludedFiles.StepIn()
	IncludedFiles.StepOut()

def MgfReferences(fname, IncludedFiles, Validator):
	IncludedFiles.StepIn()
	"""print fname
	try:
		f = fname.Stream
		f.seek(0)
		close = False
	except:
		f = open(fname, "r")
		close = True
	deps = []
	while True:
		s = f.readline()
		if len(s) == 0:
			break
		if s[:6] == "TITLE=":
			s = ".".join(s[6:].split(".")[:-3])
			try:
				info = Validator(IncludedFiles, s, ["dat", "mzml"])
				deps.append(info.Name)
				IncludedFiles.Set(info.Name, FileType.MZML)
				if info.Exists:
					IncludedFiles.TouchDeps(info.Name)
				else:
					_MzmlReferences(info.Name, IncludedFiles, Validator)
			except:
				deps.append(s)
				try:
					IncludedFiles.GetSilent(s)
				except:
					IncludedFiles.Add(s, FileType.MZML | FileType.MISSING)
					print("Can't open referenced file: " + s)
	if close:
		f.close()
	IncludedFiles.SetDepends(fname, deps)"""
	IncludedFiles.StepOut()

def PepReferences(fname, IncludedFiles, Validator):
	IncludedFiles.StepIn()
	files = []
	def _HandlePepFind(name, attr):
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
		elif name == "search_database":
			files.append([attr["local_path"], FileType.DATABASE])
	SearchXml(fname, ["msms_run_summary", "inputfile", "search_database"], _HandlePepFind)
	deps = range(len(files))
	for i in deps:
		f = files[i]
		valid = ["fasta", "mzml", "mgf", "pepxml", "pep", "xml"]
		try:
			info = Validator(IncludedFiles, f[0], valid)
			deps[i] = info.Name
			if info.Type == FileType.PEPXML:
				IncludedFiles.Set(fname, FileType.PEPXML_COMPARE)
			t = info.Type
			if f[1] != FileType.UNKNOWN:
				t = f[1]
				IncludedFiles.Set(info.Name, f[1])
			if t == FileType.UNKNOWN:
				fh = open(fname)
				t = GuessType(fh)
				fh.close()
				if t != FileType.UNKNOWN:
					IncludedFiles.Set(info.Name, t)
			if info.Exists:
				IncludedFiles.TouchDeps(info.Name)
			else:
				_References(t, info.Name, IncludedFiles, Validator)
		except:
			deps[i] = f[0]
			try:
				IncludedFiles.GetSilent(f[0])
			except:
				exts = f[0].split(".")
				ext = []
				j = len(exts) - 1
				while j >= 0:
					if exts[j] in valid:
						ext.append(exts[j])
						j -= 1
					else:
						break
				t = f[1]
				if t == FileType.UNKNOWN:
					t = FileType.FromExtensions(ext)
				IncludedFiles.Add(f[0], t | FileType.MISSING)
				print("Can't open referenced file: " + f[0])
	IncludedFiles.SetDepends(fname, deps)
	IncludedFiles.StepOut()

def ProtReferences(fname, IncludedFiles, Validator):
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
		valid = ["pepxml", "pep", "xml"]
		try:
			info = Validator(IncludedFiles, f, valid)
			deps[i] = info.Name
			#IncludedFiles.Add(info.Name, FileType.PEPXML)
			if info.Exists:
				IncludedFiles.TouchDeps(info.Name)
			else:
				PepReferences(info.Name, IncludedFiles, Validator)
		except:
			deps[i] = f
			try:
				IncludedFiles.GetSilent(f[0])
			except:
				exts = f.split(".")
				ext = []
				j = len(exts) - 1
				while j >= 0:
					if exts[j] in valid:
						ext.append(exts[j])
						j -= 1
					else:
						break
				IncludedFiles.Add(f, FileType.FromExtensions(ext) | FileType.MISSING)
				print("Can't open referenced file: " + f)
	IncludedFiles.SetDepends(fname, deps)
	IncludedFiles.StepOut()
		

def _References(t, fname, IncludedFiles, Validator):
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
		FileType.PROTXML_PROTEINPROPHET: ProtReferences,
		FileType.DATABASE: DbReferences
	}
	try:
		func = switch[t]
	except:
		return
	return func(fname, IncludedFiles, Validator)

def LoadChainProt(fname):
	if not EnsureWhitelistFile(fname):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.PROTXML)
	ProtReferences(fname, IncludedFiles, ValidateFilename)
	return IncludedFiles.Items()

def LoadChainPep(fname):
	if not EnsureWhitelistFile(fname):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.PEPXML)
	PepReferences(fname, IncludedFiles, ValidateFilename)
	return IncludedFiles.Items()

def LoadChainMgf(fname):
	if not EnsureWhitelistFile(fname):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.MGF)
	MgfReferences(fname, IncludedFiles, ValidateFilename)
	return IncludedFiles.Items()

def LoadChainMzml(fname):
	if not EnsureWhitelistFile(fname):
		raise ValueError(fname)
	IncludedFiles = IncludedFile(fname, FileType.MZML)
	MzmlReferences(fname, IncludedFiles, ValidateFilename)
	return IncludedFiles.Items()

def LoadChainGroup(files):
	class OpenFile:
		def __init__(self, f, s):
			self.Name = f
			self.Stream = s

		def __str__(self):
			return self.Name

		def __unicode__(self):
			return self.Name

	class AvaliableFile(OpenFile):
		def __init__(self, f):
			OpenFile.__init__(self, f[0], f[1])
			self.NeedsProcessing = True

		def __eq__(self, o):
			return (isinstance(o, AvaliableFile)  and o.Name == self.Name) or o == self.Name

	files = [AvaliableFile(f) for f in files]

	def NameValidator(IncludedFiles, fname, exts = None):
		fname = os.path.split(fname)[1]
		ext = []
		while True:
			f = None
			for _f in files:
				if _f.Name == fname:
					f = _f
			try:
				t = IncludedFiles.Get(fname)
				_t = FileType.FromExtensions(ext)
				if t.Type > _t:
					_t = t.Type
					IncludedFiles.Set(fname, _t)
				return ValidFile(OpenFile(fname, f.Stream), _t, True)
			except:
				if f != None:
					t = FileType.FromExtensions(ext)
					IncludedFiles.Add(fname, t, f.Stream)
					f.NeedsProcessing = 0
					return ValidFile(OpenFile(fname, f.Stream), t, False)
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
	IncludedFiles = IncludedFile()
	for f in files:
		if f.NeedsProcessing:
			f.Stream.seek(0)
			t = GuessType(f.Stream)
			IncludedFiles.Add(f.Name, t, f.Stream)
			if t != FileType.UNKNOWN:
				_References(t, f, IncludedFiles, NameValidator)
	return IncludedFiles.Items()

def GuessType(f):
	head = f.read(2048)
	if "<mzML" in head:
		return FileType.MZML
	elif "BEGIN IONS" in head.upper():
		return FileType.MGF
	elif "<msms_pipeline_analysis" in head:
		return FileType.PEPXML
	elif "<protein_summary" in head:
		return FileType.PROTXML
	return FileType.UNKNOWN
