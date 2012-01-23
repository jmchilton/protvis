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
import parameters

templates = os.path.realpath(os.path.dirname(__file__))+ "/templates/"
converted = os.path.realpath(os.path.dirname(__file__))+ "/ConvertedFiles/"
decoy_regex = re.compile(parameters.DECOY_REGEX)
spectrum_regex = re.compile(parameters.SPECTRUM_REGEX)

MzMl = None #FIXME: delete when there is an MzMl module

Parsers = { "mzml": MzMl, "mgf": MGF, "pep": PepXML, "prot": ProtXML }

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

	def Add(self, threads, files, data):
		self.ThreadsLock.acquire()
		jobid = self.NextJobID
		self.NextJobID += 1
		self.Jobs[jobid] = { "index": data, "files": [[threads[i], files[i]] for i in xrange(len(threads))] }
		self.ThreadsLock.release()
		return jobid

	def QueryStatus(self, jobid):
		self.ThreadsLock.acquire()
		try:
			job = self.Jobs[jobid]
		except:
			self.ThreadsLock.release()
			raise
		alive = 0
		for t, _ in job["files"]:
			t.join(5.0 / len(job["files"]))
			if t.isAlive():
				alive += 1
		if alive == 0:
			data = job["index"]
			data.write(struct.pack("=I", len(job["files"])))
			for t, f in job["files"]:
				if t.Type > f.Type:
					f.Type = t.Type
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
	modules = { Reference.FileType.MZML: MzMl,
		Reference.FileType.MGF: MGF,
		Reference.FileType.PEPXML: PepXML, Reference.FileType.PEPXML_MASCOT: PepXML, Reference.FileType.PEPXML_OMSSA: PepXML, Reference.FileType.PEPXML_XTANDEM: PepXML, Reference.FileType.PEPXML_COMPARE: PepXML, Reference.FileType.PEPXML_PEPTIDEPROPHET: PepXML, Reference.FileType.PEPXML_INTERPROPHET: PepXML,
		Reference.FileType.PROTXML: ProtXML, Reference.FileType.PROTXML_PROTEINPROPHET: ProtXML
	}
	return modules[datatype]

class FileLinks:
	class Link:
		def __init__(self, f):
			[self.Type, deps] = struct.unpack("=BH", f.read(1 + 2))
			self.Depends = [struct.unpack("=H", f.read(2))[0] for i in xrange(deps)]
			self.Name = DecodeStringFromFile(f)

	def __init__(self, IndexFile):
		f = open(GetFileName(IndexFile), "r")
		[files] = struct.unpack("=I", f.read(4))
		self.Index = IndexFile
		self.Links = [FileLinks.Link(f) for i in xrange(files)]

	def __getitem__(self, i):
		if i == 0xFFFF:
			return None
		return self.Links[i]

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
		

	return { "test": test, "render_peptide": render_peptide, "try_get": TryGet }

class ConverterThread(Thread):
	def __init__(self, mod, src, dst, links):
		Thread.__init__(self)
		self.Source = src
		self.Dest = dst
		self.Module = mod
		self.Links = links
		self.Type = Reference.FileType.UNKNOWN

	def run(self):
		self.Type = self.Module.ToBinary(self.Source, open(self.Dest, "w"), self.Links)


def DecodeQuery(query):
	params = query.split("&")
	dic = {}
	for p in params:
		try:
			[k, v] = p.split("=")
			dic[k] = v
		except:
			dic[p] = None
	return dic

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

def DisplayList(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(request, query)
	try:
		t = request.matchdict["type"]
		return render_to_response(templates + "list_" + t + ".pt", Parsers[t].DisplayList(request, query, fname), request = request)
	except:
		return HTTPNotFound()

def SearchScores(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	try:
		qoff = int(query["qoff"])
		hoff = int(query["hoff"])
		[spectrum, results] = PepXML.GetScores(fname, qoff, hoff)
	except:
		return HTTPBadRequest()
	items = sorted(results.items())
	rows = spectrum;
	names = {
		"bvalue": "bvalue",
		"expect": "expect",
		"homologyscore": "homologyscore",
		"hyperscore": "hyperscore",
		"identityscore": "identityscore",
		"ionscore": "ionscore",
		"nextscore": "nextscore",
		"pvalue": "pvalue",
		"star": "star",
		"yscore": "yscore",
		"pp_prob": "peptideprophet",
		"ip_prob": "interpropht",
		"ap_prob": "asapratio",
		"ep_prob": "xpressratio"}
	for name, val in items:
		rows += "\n" + str(val) + " " + names[name];
	return Response(rows, request=request)

def Upload(request):
	#uploading from a remote server
	return HTTPBadRequest()

def Convert(request):
	#for when this is running on the same server as galaxy
	#just use the local files directly
	#try:
		query = DecodeQuery(request.query_string)
		referencers = { "protxml": Reference.LoadChainProt, "pepxml": Reference.LoadChainPep, "mgf": Reference.LoadChainMgf, "mzml": Reference.LoadChainMzml }
		files = referencers[query["type"]](binascii.unhexlify(query["file"]))
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
			t = ConverterThread(GetTypeParser(f.Type), f.Name, data.name + "_" + str(i), links) #FIXME: Security
			t.start()
			threads[i] = t
		jobid = Jobs.Add(threads, files, data)
		return render_to_response(templates + "upload.pt", { "file": data.name[len(converted):], "jobid": jobid }, request=request)
	#except:
	#	return HTTPBadRequest()

def QueryInitStatus(request):
	try:
		query = DecodeQuery(request.query_string)
		alive = Jobs.QueryStatus(int(query["id"]))
		return Response(str(alive) + "\r\n", request=request)
	except HTTPException:
		raise
	except:
		return Response("-", request=request)

def View(request):
	try:
		query = DecodeQuery(request.query_string)
		try:
			links = FileLinks(query["file"])
		except:
			return HTTPNotFound()
		try:
			int(query["n"]) #ensure it is an integer
			index = query["n"]
			typename = Reference.FileType.NameBasic(links.Get(index).Type)
		except:
			index = links.GetTopInfo()
			typename = Reference.FileType.NameBasic(index["type"])
			index = index["index"]
		files = ",".join(["{" + ",".join(["name:'" + os.path.split(l.Name)[1] + "'", "type:" + test(l.Type == Reference.FileType.MISSING, "null", str(l.Type)), "deps:[" + ",".join([test(d < 65535, str(d), "-1") for d in l.Depends]) + "]"]) + "}" for l in links])
		return render_to_response(templates + "dataview.pt", { "file": query["file"], "index": index, "type": typename, "files": files }, request=request)
	except:
		return HTTPBadRequest()

def ListResults(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	try:
		links = FileLinks(query["file"])
	except:
		return HTTPNotFound()
	#try:
	t = query["type"]
	int(query["n"]) #ensure it is an integer
	parser = Parsers[t]
	if TryGet(query, "level") == "adv":
		[scores, total, results] = parser.Search(fname + "_" + query["n"], EncodeTermsAdvanced(urllib.unquote(query["q"])))
	else:
		[scores, total, results] = parser.Search(fname + "_" + query["n"], EncodeTermsBasic(urllib.unquote(query["q"])))
	matches = len(results)
	[score, reverses] = parser.DefaultSortColumn(scores)
	try:
		sortcol = query["sort"]
	except:
		sortcol = score
	try:
		if query["order"] == "asc":
			reverse = False
		else:
			reverse = True
	except:
		reverse = False
	results = sorted(results, key = lambda key: key.HitInfo[sortcol], reverse = test(test(sortcol == "score", score, sortcol) in reverses, not reverse, reverse))
	try:
		start = int(query["start"])
	except:
		start = 0
	try:
		limit = int(query["max"])
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
	info = {"total": total, "matches": matches, "start": start + 1, "end": start + len(results), "type": t, "score": score, "file": query["file"], "datafile": query["n"], "query": query["q"], "hash": abs(hash(time.gmtime())), "datas": links.Types()}
	return render_to_response(templates + t + "_results.pt", { "sortcol": sortcol, "sortdsc": reverse, "info": info, "results": results, "url": Literal(request.path_qs) }, request = request)
	#except:
	#	return HTTPBadRequest()

def ListPeptide(request):
	class Spec:
		def __init__(self, spectrum, count):
			self.Spectrum = spectrum
			self.Count = count

		def __str__(self):
			return str(self.Count) + "/" + self.Spectrum

	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)

	def ViewSpectrum(row):
		return "ShowSpectrumFromPeptide(" + query["n"] + ", '" + row["spectrum"] + "', " + str(row["query__offset"]) + ", " + str(row["hit__offset"]) + ");"

	#try:
	int(query["n"])
	[scores, results] = PepXML.SearchPeptide(fname + "_" + query["n"], query["peptide"])
	total = len(results)
	[score, reverses] = PepXML.DefaultSortColumn(scores)
	try:
		sortcol = query["sort"]
	except:
		sortcol = "score"
	try:
		if query["order"] == "asc":
			reverse = False
		else:
			reverse = True
	except:
		reverse = False
	SearchEngines = { "X-Tandem": 0, "Mascot": 0, "Omssa": 0 }
	spectrums = {}
	for r in results:
		r["score"] = r[score]
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
	results = sorted(results, key = lambda key: key[sortcol], reverse = test(test(sortcol == "score", score, sortcol) in reverses, not reverse, reverse))
	try:
		start = int(query["start"])
	except:
		start = 0
	try:
		limit = int(query["max"])
	except:
		limit = -1
	if start > 0:
		if limit > 0:
			results = results[start:start+limit]
		else:
			results = results[start:]
	elif limit > 0:
		results = results[:limit]
	info = { "total": total, "start": start + 1, "end": start + len(results), "peptide": query["peptide"] }
	columns = [{"name": "spectrum", "title": "Spectrum", "click": ViewSpectrum}, {"name": "massdiff", "title": "Mass Diff"}, {"name": "score", "title": "Score"}, {"name": "engine", "title": "Search Engine"}, {"name": "engine_score", "title": "Engine Score"}]
	specs = render(templates + "pepxml_peptide_spectrums.pt", { "count": len(spectrums), "spectrums": spectrums}, request=request)
	instances = render(templates + "pepxml_peptide.pt", { "info": info, "peptides": results, "columns": columns, "sortcol": sortcol, "sortdsc": reverse }, request=request)
	return Response(specs + '<div id="peptide_results_list">' + instances + "</div>", request=request)
	#except:
	#	return HTTPBadRequest()

def SelectInfo(request):
	query = DecodeQuery(request.query_string)
	for c in query["type"]:
		if (c < 'a' or c > 'z') and c != '_':
			raise HTTPUnauthorized()
	#try:
	parser = FileLinks(query["file"]).GetParser(int(query["n"]))
	select = eval("parser.select_" + query["type"])
	results = select(GetQueryFileName(query), query)
	return render_to_response(templates + "select_" + query["type"] + ".pt", { "query": query, "results": results }, request=request)
	#except:
	#	return HTTPBadRequest()

def Spectrum(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	#try:
	spectrum = query["spectrum"]
	datafile = TryGet(query, "n")
	filetype = TryGet(query, "type")
	offset = TryGet(query, "off")
	pep_datafile = TryGet(query, "pn")
	pep_query_offset = TryGet(query, "pqoff")
	pep_hit_offset = TryGet(query, "phoff")
	if datafile == None:
		links = FileLinks(query["file"])
		possible = []
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
		print possible
		for t in [Reference.FileType.MGF, Reference.FileType.MZML]:
			for f in possible:
				if links.Links[f].Type == t:
					offset = MGF.GetOffsetFromSpectrum(fname + "_" + str(f), spectrum)
					if offset >= 0:
						datafile = f
						filetype = Reference.FileType.NameBasic(t)
						break
	elif filetype == None:
		filetype = FileLinks(query["file"]).Links[datafile].Type
	if offset == None:
		parser = Parsers[filetype]
		parser.GetOffsetFromSpectrum(spectrum)
	return render_to_response(templates + "spectrum.pt", { "file": query["file"], "type": filetype, "spectrum": spectrum, "datafile": datafile, "offset": offset, "pep_datafile": pep_datafile, "pep_query_offset": pep_query_offset, "pep_hit_offset": pep_hit_offset }, request=request)
	#except:
	#	return HTTPBadRequest()

def Lorikeet(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	#try:
	parser = Parsers[query["type"]]
	spec = query["spectrum"].split(".")
	pep_datafile = TryGet(query, "pn")
	pep_query_offset = TryGet(query, "pqoff")
	pep_hit_offset = TryGet(query, "phoff")
	if pep_datafile != None and pep_query_offset != None and pep_hit_offset != None:
		pep = PepXML.GetHitInfo(fname + "_" + pep_datafile, int(pep_query_offset), int(pep_hit_offset))
		peptide = { "peptide": pep["peptide"], "precursor_neutral_mass": pep["precursor_neutral_mass"], "modification_info": pep["modification_info"] }
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
	else:
		peptide = None
	spectrum = { "file": ".".join(spec[:-3]), "scan": spec[-3], "charge": spec[-1], "ions": parser.GetSpectrumFromOffset(fname + "_" + query["n"], int(query["off"])) }
	return render_to_response(templates + "lorikeet_frame.pt", { "query": query, "spectrum": spectrum, "peptide": peptide }, request=request)
	#except:
	#	return HTTPBadRequest()

def Tooltip(request):
	t = request.matchdict["type"]
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	if t == "peptide":
		#try:
			int(query["n"]) #ensure it is an integer
			[scores, results] = PepXML.SearchPeptide(fname + "_" + query["n"], query["peptide"])
			score = PepXML.DefaultSortColumn(scores)
			if score == "expect":
				reverse = False
			else:
				reverse = True
			results = sorted(results, key = lambda key: key[score[0]], reverse = reverse)
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
				r["score"] = r[score[0]]
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
			return render_to_response(templates + "pepxml_peptide_tooltip.pt", { "info": info, "peptides": results, "counts": SearchEngines.items() }, request=request)
		#except:
		#	return HTTPBadRequest()
	return HTTPNotFound()

if __name__ == "__main__":
	#check to make sure everything is set up properly
	
	Threads = {}
	JobsTotal = 0
	ThreadsLock = Lock()
	config = Configurator(renderer_globals_factory=RendererGlobals)
	config.add_route("list", "/list/{type}/")
	config.add_route("search_score", "/search/{type}/score/")
	
	config.add_route("upload", "/init")
	config.add_route("convert", "/init_local")
	config.add_route("query_init", "/query_init")
	config.add_route("view", "/view")
	config.add_route("results", "/results")
	config.add_route("peptide", "/peptide")
	config.add_route("select", "/select")
	config.add_route("spectrum", "/spectrum")
	config.add_route("lorikeet", "/lorikeet")
	config.add_route("tooltip", "/tooltip/{type}")
	config.add_view(DisplayList, route_name="list")
	#config.add_view(SearchHit, route_name="search_hit")
	config.add_view(SearchScores, route_name="search_score")
	config.add_view(Upload, route_name="upload")
	config.add_view(Convert, route_name="convert")
	config.add_view(QueryInitStatus, route_name="query_init")
	config.add_view(View, route_name="view")
	config.add_view(ListResults, route_name="results")
	config.add_view(ListPeptide, route_name="peptide")
	config.add_view(SelectInfo, route_name="select")
	config.add_view(Spectrum, route_name="spectrum")
	config.add_view(Lorikeet, route_name="lorikeet")
	config.add_view(Tooltip, route_name="tooltip")
	config.add_static_view("res", "res", cache_max_age=3600*24*7)
	config.add_static_view("test", "test", cache_max_age=0)
	app = config.make_wsgi_app()
	server = make_server(parameters.HOST, parameters.PORT, app)
	server.serve_forever()
