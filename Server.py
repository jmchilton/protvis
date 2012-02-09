#!/usr/bin/python
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.renderers import render, render_to_response
import binascii;
from xml.sax.saxutils import escape
import os
from threading import Thread, Lock
from pyramid.httpexceptions import *
import tempfile
import urllib
import re
from HttpUtil import *
import Reference
import struct
from Common import EncodeStringToFile, DecodeStringFromFile, TryGet, EncodeTermsBasic, EncodeTermsAdvanced
import ProtXML, PepXML, MGF
import time
import subprocess
import parameters

templates = os.path.realpath(os.path.dirname(__file__))+ "/templates/"
converted = os.path.realpath(os.path.dirname(__file__))+ "/ConvertedFiles/"
decoy_regex = re.compile(parameters.DECOY_REGEX)
spectrum_regex = re.compile(parameters.SPECTRUM_REGEX)

MzMl = None #FIXME: delete when there is an MzMl module

Parsers = { "mzml": MzMl, "mgf": MGF, "pep": PepXML, "prot": ProtXML }
Referencers = { "protxml": Reference.LoadChainProt, "pepxml": Reference.LoadChainPep, "mgf": Reference.LoadChainMgf, "mzml": Reference.LoadChainMzml }

class Literal(object):
    def __init__(self, s):
        self.s = s

    def __html__(self):
        return self.s

def test(cond, t, f):
	if cond == True:
		return t
	return f

class JobManager:
	def __init__(self):
		self.Jobs = {}
		self.NextJobID = 0
		self.ThreadsLock = Lock()

	def Add(self, threads, f, files, data):
		self.ThreadsLock.acquire()
		jobid = self.NextJobID
		self.NextJobID += 1
		self.Jobs[jobid] = { "index": data, "file": f, "files": [[threads[i], files[i]] for i in xrange(len(threads))] }
		self.ThreadsLock.release()
		return jobid

	def QueryStatus(self, f, jobid):
		self.ThreadsLock.acquire()
		try:
			job = self.Jobs[jobid]
		except:
			self.ThreadsLock.release()
			raise
		if job["file"] != f:
			raise ValueError()
		alive = 0
		for t, _ in job["files"]:
			if t != None:
				t.join(5.0 / len(job["files"]))
				if t.isAlive():
					alive += 1
		if alive == 0:
			data = job["index"]
			data.write(struct.pack("=I", len(job["files"])))
			for t, f in job["files"]:
				if t != None and t.Type > f.Type:
					print f, t.Type, f.Type
					f.Type = t.Type
				else:
					print f, None
				data.write(struct.pack("=BH", f.Type, len(f.Depends)))
				for d in f.Depends:
					data.write(struct.pack("=H", test(d < 0, 0xFFFF, d)))
				EncodeStringToFile(data, f.Name)
			data.close()
			del self.Jobs[jobid]
		self.ThreadsLock.release()
		return alive

Jobs = JobManager()

def GetTypeParser(datatype):
	modules = {
		Reference.FileType.MZML: MzMl,
		Reference.FileType.MGF: MGF,
		Reference.FileType.PEPXML: PepXML, Reference.FileType.PEPXML_MASCOT: PepXML, Reference.FileType.PEPXML_OMSSA: PepXML, Reference.FileType.PEPXML_XTANDEM: PepXML, Reference.FileType.PEPXML_COMPARE: PepXML, Reference.FileType.PEPXML_PEPTIDEPROPHET: PepXML, Reference.FileType.PEPXML_INTERPROPHET: PepXML,
		Reference.FileType.PROTXML: ProtXML, Reference.FileType.PROTXML_PROTEINPROPHET: ProtXML
	}
	try:
		return modules[datatype]
	except:
		return None

class FileLinks:
	class Link:
		def __init__(self, f):
			[self.Type, deps] = struct.unpack("=BH", f.read(1 + 2))
			self.Depends = [struct.unpack("=H", f.read(2))[0] for i in xrange(deps)]
			self.Name = DecodeStringFromFile(f)

	def __init__(self, IndexFile):
		f = open(IndexFile, "r")
		[files] = struct.unpack("=I", f.read(4))
		self.Index = IndexFile
		self.Links = [FileLinks.Link(f) for i in xrange(files)]

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
		i = len(self.Links) - 1
		l = self.Links[i]
		return { "name": l.Name, "type": l.Type, "index": i }

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
			if l.Type >= Reference.FileType.PROTXML:
				flags |= 8
			elif l.Type >= Reference.FileType.PEPXML:
				flags |= 4
			elif l.Type == Reference.FileType.MGF:
				flags |= 2
			elif l.Type == Reference.FileType.MZML:
				flags |= 1
		return flags

def RendererGlobals(system):
	def render_peptide(peptide):
		try:
			mods = peptide["modification_info"]
			if len(mods) == 0:
				mods = None
		except:
			mods = None
		pep = peptide["peptide"]
		if mods != None:
			mod = [m["mod_aminoacid_mass"] for m in mods]
			mods = []
			for m in mod:
				mods += m
			mods = sorted(mods, key = lambda mam: mam[0], reverse = True)
			for m in mods:
				(pos, mass) = m
				pep = pep[:pos] + '<span class="modification">[' + str(int(mass)) + ']</span>' + pep[pos:]
		return Literal(pep)

	def unique_dataset():
		return abs(hash(time.gmtime()))

	return { "test": test, "render_peptide": render_peptide, "try_get": TryGet, "urlencode": urllib.quote, "unique_dataset": unique_dataset }

class ConverterThread(Thread):
	def __init__(self, mod, src, dst, links):
		Thread.__init__(self)
		self.Source = src
		self.Dest = dst
		self.Module = mod
		self.Links = links
		self.Type = Reference.FileType.UNKNOWN

	def run(self):
		opened = False
		if isinstance(self.Source, file):
			s = self.Source
			s.seek(0)
		else:
			s = open(self.Source, "r")
			opened = True
		d = open(self.Dest, "w")
		self.Type = self.Module.ToBinary(s, d, self.Links)
		if opened:
			s.close()
		d.close()


def GetFileName(fname):
	if fname.find("/") >= 0:
		raise HTTPUnauthorized()
	return converted + fname

def GetQueryFileName(query):
	try:
		fname = query["file"]
	except:
		raise HTTPBadRequest()
	return GetFileName(fname)

def DecodeDecoy(protein):
	if decoy_regex.match(protein.lower()) != None:
		return "decoy"
	return "row"

def DisplayList(req):
	fname = GetQueryFileName(req.GET)
	try:
		t = req.matchdict["type"]
		return render_to_response(templates + "list_" + t + ".pt", Parsers[t].DisplayList(req, req.GET, fname), request = req)
	except:
		return HTTPNotFound()

def SortPeptides(results, sortcol, score, reverse = False):
	if sortcol == "score":
		def Comparator(a, b):
			try:
				_a = a[score]
				try:
					_b = b[score]
					if _a < _b:
						return -1
					elif _a == _b:
						_a = a["pvalue"]
						_b = b["pvalue"]
						if _a < _b:
							return -1
						elif _a == _b:
							return 0
						return 1
					return 1
				except:
					return 1
			except:
				if score in b:
					return -1
				_a = a["pvalue"]
				_b = b["pvalue"]
				if _a < _b:
					return -1
				elif _a == _b:
					return 0
				return 1
		return sorted(results, cmp = Comparator, reverse=reverse)
	else:
		return sorted(results, key = lambda key: key[sortcol], reverse=reverse)

def Index(req):
	#for when this is used as a standalone tool
	return render_to_response(templates + "index.pt", { }, request=req)

def Upload(req):
	#uploading from a remote server
	#try:
		fs = req.POST.getall("uploadedfiles[]")
		for f in fs:
			f.file.seek(0)
		files = Reference.LoadChainGroup([[f.filename, f.file] for f in fs])
		#Build the index file
		if not os.path.exists("ConvertedFiles"):
			os.makedirs("ConvertedFiles")
		data = tempfile.NamedTemporaryFile(dir = ".", prefix = "ConvertedFiles/", delete = False)
		threads = range(len(files))
		links = {}
		for i in threads:
			links[files[i].Name] = i
		#Now generate all the data files
		for i in threads:
			f = files[i]
			if f.Type & Reference.FileType.MISSING or f.Type == Reference.FileType.UNKNOWN:
				threads[i] = None
			else:
				t = ConverterThread(GetTypeParser(f.Type), f.Stream, data.name + "_" + str(i), links)
				t.start()
				threads[i] = t
		f = data.name[len(converted):]
		jobid = Jobs.Add(threads, f, files, data)
		return Response('{"file":"' + f + '","jobid":' + str(jobid) + '}\r\n')
	#except:
	#	return Response('{"error":"Internal server error"}\r\n')

def Convert(req):
	#for when this is running on the same server as galaxy
	#just use the local files directly
	#try:
		files = Referencers[req.GET["type"]](binascii.unhexlify(req.GET["file"]))
		#Build the index file
		if not os.path.exists("ConvertedFiles"):
			os.makedirs("ConvertedFiles")
		data = tempfile.NamedTemporaryFile(dir = ".", prefix = "ConvertedFiles/", delete = False)
		threads = range(len(files))
		links = {}
		for i in threads:
			links[files[i].Name] = i
		#Now generate all the data files
		for i in threads:
			f = files[i]
			if f.Type & Reference.FileType.MISSING:
				threads[i] = None
			else:
				p = GetTypeParser(f.Type)
				if p == None:
					threads[i] = None
				else:
					t = ConverterThread(p, f.Name, data.name + "_" + str(i), links)
					t.start()
					threads[i] = t
		f = data.name[len(converted):]
		jobid = Jobs.Add(threads, f, files, data)
		return render_to_response(templates + "upload.pt", { "file": f, "jobid": str(jobid) }, request=req)
	#except:
	#	return HTTPBadRequest()

def QueryInitStatus(req):
	try:
		alive = Jobs.QueryStatus(req.GET["file"], int(req.GET["id"]))
		return Response(str(alive) + "\r\n", request=req)
	except HTTPException:
		raise
	except:
		return Response("-\r\n", request=req)

def AddFile(req):
	#try:
		links = FileLinks(GetQueryFileName(req.GET))
		n = req.GET["n"]
		l = links[int(n)]
		try:
			s = req.POST["datas[]"]
		except:
			try:
				s = req.POST["data0"]
			except:
				try:
					s = req.POST["data"]
				except:
					return HTTPBadRequest()
		s = s.file
		s.seek(0)
		d = open(GetQueryFileName(req.GET) + "_" + n, "w")
		t = l.Type & 0x7F
		if t == Reference.FileType.UNKNOWN:
			t = TryGet(req.POST, "type")
			if t != None and int(t) != 0:
				t = int(t)
			else:
				t = Reference.GuessType(s)
				if t == Reference.FileType.UNKNOWN:
					return HTTPUnsupportedMediaType("File type could not be determined")
				s.seek(0)
		s.seek(0)
		t2 = GetTypeParser(t).ToBinary(s, d, links)
		if t2 > t:
			t = t2
		d.close()
		l.Type = t
		same = TryGet(req.POST, "similar")
		if same != None:
			same = same.split(",")
			#FIXME: merge
		links.Write(req.GET["file"])
		return Response("test\r\n", request=req)
	#except:
	#	return HTTPBadRequest()

def View(req):
	try:
		try:
			links = FileLinks(GetQueryFileName(req.GET))
		except:
			return HTTPNotFound()
		try:
			int(req.GET["n"]) #ensure it is an integer
			index = req.GET["n"]
			typename = Reference.FileType.NameBasic(links.Links[index].Type)
		except:
			index = links.GetTopInfo()
			typename = Reference.FileType.NameBasic(index["type"])
			index = index["index"]
		files = ",".join(["{" + ",".join(["name:'" + os.path.split(l.Name)[1] + "'", "type:" + str(l.Type), "deps:[" + ",".join([test(d < 65535, str(d), "-1") for d in l.Depends]) + "]"]) + "}" for l in links])
		return render_to_response(templates + "dataview.pt", { "file": req.GET["file"], "index": index, "type": typename, "files": files, "nfiles": len(links) }, request=req)
	except:
		return HTTPBadRequest()

def ListResults(req):
	fname = GetQueryFileName(req.GET)
	try:
		links = FileLinks(fname)
	except:
		return HTTPNotFound()
	#try:
	n = req.GET["n"]
	if links.Links[int(n)].Type & Reference.FileType.MISSING:
		exts = ["mzml", "mzxml", "mgf", "pepxml", "pep", "protxml", "prot", "xml"]
		mypath = os.path.split(links.Links[int(n)].Name)
		myname = mypath[1].split(".")
		j = len(myname) - 1
		while j >= 0:
			if myname[j].lower() in exts:
				del myname[j]
			else:
				break
			j -= 1
		myname = ".".join(myname)
		n = int(n)
		similar = []
		i = 0
		for l in links.Links:
			if l.Type == Reference.FileType.MISSING and i != n:
				name = os.path.split(l.Name)
				if name[0] == mypath[0]:
					name = name[1].split(".")
					j = len(name) - 1
					while j >= 0:
						if name[j].lower() in exts:
							del name[j]
						else:
							break
						j -= 1
					name = ".".join(name)	
					if name == myname:
						similar.append({"index":i, "name":os.path.basename(l.Name)})
			i += 1
		return render_to_response(templates + "missing_results.pt", { "links": links, "query": req.GET, "similar": similar }, request = req)
	else:
		t = req.GET["type"]
		parser = Parsers[t]
		if TryGet(req.GET, "level") == "adv":
			[scores, total, results] = parser.Search(fname + "_" + req.GET["n"], EncodeTermsAdvanced(urllib.unquote(req.GET["q"])))
		else:
			[scores, total, results] = parser.Search(fname + "_" + req.GET["n"], EncodeTermsBasic(urllib.unquote(req.GET["q"])))
		matches = len(results)
		[score, reverses] = parser.DefaultSortColumn(scores)
		try:
			sortcol = req.GET["sort"]
		except:
			sortcol = score
		try:
			if req.GET["order"] == "asc":
				reverse = False
			else:
				reverse = True
		except:
			reverse = False
		results = sorted(results, key = lambda key: key.HitInfo[sortcol], reverse = test(test(sortcol == "score", score, sortcol) in reverses, not reverse, reverse))
		try:
			start = int(req.GET["start"])
		except:
			start = 0
		try:
			limit = int(req.GET["max"])
		except:
			limit = -1
		if start > 0:
			if limit > 0:
				results = results[start:start + limit]
			else:
				results = results[start:]
		elif limit > 0:
			results = results[:limit]
		for r in results:
			h = r.HitInfo
			try:
				r.style = DecodeDecoy(h["protein"])
			except:
				r.style = "row"
		info = { "total": total, "matches": matches, "start": start + 1, "end": start + len(results), "type": t, "score": score, "file": req.GET["file"], "datafile": n, "query": req.GET["q"], "datas": links.Types() }
		return render_to_response(templates + t + "_results.pt", { "sortcol": sortcol, "sortdsc": reverse, "info": info, "results": results, "url": Literal(req.path_qs) }, request = req)
	#except:
	#	return HTTPBadRequest()

def ListPeptide(req):
	class Spec:
		def __init__(self, spectrum, count):
			self.Spectrum = spectrum
			self.Count = count

		def __str__(self):
			return str(self.Count) + "/" + self.Spectrum

	def ViewSpectrum(row):
		return "ShowSpectrumFromPeptide(" + req.GET["n"] + ", '" + row["spectrum"] + "', " + str(row["query__offset"]) + ", " + str(row["hit__offset"]) + ");"

	fname = GetQueryFileName(req.GET)
	#try:
	int(req.GET["n"])
	[scores, results] = PepXML.SearchPeptide(fname + "_" + req.GET["n"], req.GET["peptide"])
	total = len(results)
	[score, reverses] = PepXML.DefaultSortColumn(scores)
	try:
		sortcol = req.GET["sort"]
	except:
		sortcol = "score"
	try:
		if req.GET["order"] == "asc":
			reverse = False
		else:
			reverse = True
	except:
		reverse = False
	SearchEngines = { "X-Tandem": 0, "Mascot": 0, "Omssa": 0 }
	spectrums = {}
	for r in results:
		r["score"] = TryGet(r, score)
		if "hyperscore" in r:
			r["engine"] = "X-Tandem"
			r["engine_score"] = str(r["hyperscore"])
			SearchEngines["X-Tandem"] += 1
		elif "ionscore" in r:
			r["engine"] = "Mascot"
			r["engine_score"] = str(r["ionscore"])
			SearchEngines["Mascot"] += 1
		elif "expect" in r:
			r["engine"] = "Omssa"
			r["engine_score"] = str(r["expect"])
			SearchEngines["Omssa"] += 1
		else:
			r["engine"] = ""
			r["engine_score"] = ""
		spec = spectrum_regex.sub(r"\1", r["spectrum"])
		try:
			spectrums[spec] += 1
		except:
			spectrums[spec] = 1
	spectrums = sorted([Spec(k, v) for k, v in spectrums.items()], reverse = True, key = lambda spec: spec.Count)
	results = SortPeptides(results, sortcol, score, test(test(sortcol == "score", score, sortcol) in reverses, not reverse, reverse))
	try:
		start = int(req.GET["start"])
	except:
		start = 0
	try:
		limit = int(req.GET["max"])
	except:
		limit = -1
	if start > 0:
		if limit > 0:
			results = results[start:start+limit]
		else:
			results = results[start:]
	elif limit > 0:
		results = results[:limit]
	info = { "total": total, "start": start + 1, "end": start + len(results), "peptide": req.GET["peptide"] }
	columns = [{"name": "spectrum", "title": "Spectrum", "click": ViewSpectrum}, {"name": "massdiff", "title": "Mass Diff"}, {"name": "score", "title": "Score"}, {"name": "engine", "title": "Search Engine"}, {"name": "engine_score", "title": "Engine Score"}]
	specs = render(templates + "pepxml_peptide_spectrums.pt", { "count": len(spectrums), "spectrums": spectrums}, request=req)
	instances = render(templates + "pepxml_peptide.pt", { "info": info, "peptides": results, "columns": columns, "sortcol": sortcol, "sortdsc": reverse }, request=req)
	return Response(specs + '<div id="peptide_results_list">' + instances + "</div>", request=req)
	#except:
	#	return HTTPBadRequest()

def SelectInfo(req):
	for c in req.GET["type"]:
		if (c < 'a' or c > 'z') and c != '_':
			raise HTTPUnauthorized()
	#try:
	parser = FileLinks(GetQueryFileName(req.GET)).GetParser(int(req.GET["n"]))
	select = eval("parser.select_" + req.GET["type"])
	results = select(GetQueryFileName(req.GET), req.GET)
	return render_to_response(templates + "select_" + req.GET["type"] + ".pt", { "query": req.GET, "results": results }, request=req)
	#except:
	#	return HTTPBadRequest()

def Spectrum(req):
	def PeptideInfo(pep):
		peptide = { "peptide": pep["peptide"], "modification_info": pep["modification_info"], "protein": pep["protein"], "score": TryGet(pep, sortcol) }
		if pep["modification_info"] != None and len(pep["modification_info"]) > 0:
			nterm_mod = 0
			cterm_mod = 0
			mods = []
			for mi in pep["modification_info"]:
				if nterm_mod != None:
					nterm = TryGet(mi, "mod_nterm_mass")
					if nterm != None:
						nterm_mod = nterm
				if cterm_mod != None:
					cterm = TryGet(mi, "mod_nterm_mass")
					if cterm != None:
						cterm_mod = cterm
				mods += [{"index": m[0], "mass": m[1], "aa": pep["peptide"][m[0]]} for m in mi["mod_aminoacid_mass"]]
			peptide["mods"] = mods
			peptide["nterm"] = nterm_mod
			peptide["cterm"] = cterm_mod
		else:
			peptide["mods"] = None
		return peptide

	def render_peptide_lorikeet(peptide):
		pep = peptide["peptide"]
		mods = peptide["mods"]
		if mods != None and len(mods) > 0:
			mods = sorted(mods, key = lambda mam: mam["index"], reverse = True)
			for m in mods:
				pep = pep[:m["index"]] + '<span class="modification">[' + str(int(m["mass"])) + ']</span>' + pep[m["index"]:]
		return Literal(pep)

	fname = GetQueryFileName(req.GET)
	#try:
	spectrum = req.GET["spectrum"]
	datafile = TryGet(req.GET, "n")
	filetype = TryGet(req.GET, "type")
	offset = TryGet(req.GET, "off")
	params = ""
	pep_datafile = None
	init_pep = 0
	peptide = None
	score = None
	if datafile == None:
		links = FileLinks(fname)
		possible = []
		pep_datafile = TryGet(req.GET, "pn")
		if pep_datafile == None:
			for i in xrange(len(links.Links)):
				l = links.Links[i]
				if l.Type == Reference.FileType.MZML or l.Type == Reference.FileType.MGF:
					possible.append(i)
		else:
			deps = links.Links[int(pep_datafile)].Depends
			i = 0
			while i < len(deps):
				deps += links.Links[deps[i]].Depends
				i += 1
			for d in deps:
				l = links.Links[d]
				if l.Type == Reference.FileType.MZML or l.Type == Reference.FileType.MGF:
					possible.append(d)
		possible = list(set(possible))
		for t in [Reference.FileType.MGF, Reference.FileType.MZML]:
			for f in possible:
				if links.Links[f].Type == t:
					offset = Parsers[Reference.FileType.NameBasic(t)].GetOffsetFromSpectrum(fname + "_" + str(f), spectrum)
					if offset >= 0:
						datafile = str(f)
						filetype = Reference.FileType.NameBasic(t)
						break
		pep_query_offset = TryGet(req.GET, "pqoff")
		if pep_query_offset != None:
			pep_hit_offset = TryGet(req.GET, "phoff")
			if pep_hit_offset == None:
				[peptide, scores] = PepXML.GetQueryHitInfos(fname + "_" + pep_datafile, int(pep_query_offset))
				scores = scores & 0xFF #get rid of inter/pepdite prophet scores. Only the top hit has 1 of these scores, which isnt much use
				score = PepXML.SearchEngineName(scores)
				[sortcol, reverses] = PepXML.DefaultSortColumn(scores)
				peptide["peptides"] = sorted([PeptideInfo(p) for p in peptide["peptides"]], key = lambda key: key["score"], reverse = test(sortcol in reverses, True, False))
				pep = TryGet(req.GET, "pep")
				if pep != None:
					i = 0
					for p in peptide["peptides"]:
						if p["peptide"] == pep:
							init_pep = i
							break
						i += 1
			else:
				sortcol = None
				pep = PepXML.GetHitInfo(fname + "_" + pep_datafile, int(pep_query_offset), int(pep_hit_offset))
				peptide = { "peptides":[PeptideInfo(pep)], "precursor_neutral_mass":pep["precursor_neutral_mass"] }
	elif filetype == None:
		filetype = FileLinks(fname).Links[datafile].Type
	parser = Parsers[filetype]
	if offset == None and datafile != None:
		offset = parser.GetOffsetFromSpectrum(fname + "_" + datafile, spectrum)
	if offset == None or offset < -1 or datafile == None:
		raise HTTPBadRequest()
	spec = spectrum.split(".")
	spectrum = { "file": Literal(".".join(spec[:-3]).replace("\\", "\\\\").replace("\"", "\\\"")), "scan": spec[-3], "charge": spec[-1], "ions": parser.GetSpectrumFromOffset(fname + "_" + datafile, int(offset)) }
	return render_to_response(templates + "specview.pt", { "query": req.GET, "datafile": datafile, "spectrum": spectrum, "peptide": peptide, "init_pep": init_pep, "score": score, "render_peptide_lorikeet": render_peptide_lorikeet }, request=req)
	#except:
	#	return HTTPBadRequest()

def Tooltip(req):
	t = req.matchdict["type"]
	fname = GetQueryFileName(req.GET)
	if t == "peptide":
		#try:
			int(req.GET["n"]) #ensure it is an integer
			[scores, results] = PepXML.SearchPeptide(fname + "_" + req.GET["n"], req.GET["peptide"])
			[score, reverses] = PepXML.DefaultSortColumn(scores)
			results = SortPeptides(results, "score", score, score in reverses)
			count = len(results)
			shown = count
			SearchEngines = { "X-Tandem": 0, "Mascot": 0, "Omssa": 0 }
			for r in results:
				if "hyperscore" in r:
					SearchEngines["X-Tandem"] += 1
				elif "ionscore" in r:
					SearchEngines["Mascot"] += 1
				elif "expect" in r:
					SearchEngines["Omssa"] += 1
			if count > 5:
				results = results[:5]
				shown = 5
			for r in results:
				r["score"] = TryGet(r, score)
				if "hyperscore" in r:
					r["engine"] = "X-Tandem"
					r["engine_score"] = str(r["hyperscore"])
				elif "ionscore" in r:
					r["engine"] = "Mascot"
					r["engine_score"] = str(r["ionscore"])
				elif "expect" in r:
					r["engine"] = "Omssa"
					r["engine_score"] = str(r["expect"])
				else:
					r["engine"] = ""
					r["engine_score"] = ""
			if SearchEngines["X-Tandem"] == 0:
				del SearchEngines["X-Tandem"]
			if SearchEngines["Mascot"] == 0:
				del SearchEngines["Mascot"]
			if SearchEngines["Omssa"] == 0:
				del SearchEngines["Omssa"]
			info = { "shown": shown, "total": count, "engine": PepXML.SearchEngineName(scores) }
			return render_to_response(templates + "pepxml_peptide_tooltip.pt", { "info": info, "peptides": results, "counts": SearchEngines.items() }, request=req)
		#except:
		#	return HTTPBadRequest()
	return HTTPNotFound()

if __name__ == "__main__":
	#check to make sure everything is set up properly
	if len(parameters.PROTEIN_DATABASES) > 0:
		print " + Indexing protein databases"
		for f in parameters.PROTEIN_DATABASES:
			p = subprocess.Popen(["bin/blastdbcmd", "-db", f, "-info"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
			(out, err) = p.communicate()
			p.stderr.close()
			p.stdout.close()
			if len(err) > 0:
				subprocess.call(["bin/makeblastdb", "-in", f, "-parse_seqids"])
	
	Threads = {}
	JobsTotal = 0
	ThreadsLock = Lock()
	config = Configurator(renderer_globals_factory=RendererGlobals)
	config.add_route("list", "/list/{type}/") #deprecated
	
	config.add_route("index", "/")
	config.add_route("upload", "/init")
	config.add_route("convert", "/init_local")
	config.add_route("query_init", "/query_init")
	config.add_route("add", "/add")
	config.add_route("view", "/view")
	config.add_route("results", "/results")
	config.add_route("peptide", "/peptide")
	config.add_route("select", "/select")
	config.add_route("spectrum", "/spectrum")
	config.add_route("tooltip", "/tooltip/{type}")
	config.add_view(DisplayList, route_name="list")
	#config.add_view(SearchHit, route_name="search_hit")
	config.add_view(Index, route_name="index")
	config.add_view(Upload, route_name="upload")
	config.add_view(Convert, route_name="convert")
	config.add_view(QueryInitStatus, route_name="query_init")
	config.add_view(AddFile, route_name="add")
	config.add_view(View, route_name="view")
	config.add_view(ListResults, route_name="results")
	config.add_view(ListPeptide, route_name="peptide")
	config.add_view(SelectInfo, route_name="select")
	config.add_view(Spectrum, route_name="spectrum")
	config.add_view(Tooltip, route_name="tooltip")
	config.add_static_view("res", "res", cache_max_age=3600*24*7)
	config.add_static_view("test", "test", cache_max_age=0)
	app = config.make_wsgi_app()
	server = make_server(parameters.HOST, parameters.PORT, app)
	print "Server is going up now"
	server.serve_forever()
