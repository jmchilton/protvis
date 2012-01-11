#!/usr/bin/python
import sys
sys.path.insert(1, "env/lib/python2.7")
import getsite

from paste.httpserver import serve
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
import conf
import struct
from CommonXML import EncodeStringToFile, DecodeStringFromFile, TryGet
import ProtXML, PepXML
import time

templates = os.path.realpath(os.path.dirname(__file__))+ "/templates/"
converted = os.path.realpath(os.path.dirname(__file__))+ "/ConvertedFiles/"
decoy_regex = re.compile(conf.DECOY_REGEX)
spectrum_regex = re.compile(conf.SPECTRUM_REGEX)
Parsers = { "pepxml": PepXML, "protxml": ProtXML }


def test(cond, t, f):
	if cond == True:
		return t
	return f

class JobManager:
	def __init__(self):
		self.Jobs = {}
		self.NextJobID = 0
		self.ThreadsLock = Lock()

	def Add(self, threads):
		self.ThreadsLock.acquire()
		jobid = self.NextJobID
		self.NextJobID += 1
		self.Jobs[jobid] = threads
		self.ThreadsLock.release()
		return jobid

	def QueryStatus(self, jobid):
		self.ThreadsLock.acquire()
		try:
			threads = self.Jobs[jobid]
		except:
			self.ThreadsLock.release()
			raise
		alive = 0
		for t in threads:
			t.join(5.0 / len(threads))
			if t.isAlive():
				alive += 1
		if alive == 0:
			del self.Jobs[jobid]
		self.ThreadsLock.release()
		return alive

Jobs = JobManager()

def GetTypeParser(datatype):
	MzMl = None #FIXME: delete when there is an MzMl module
	Mgf = None #FIXME: delete when there is an Mgf module
	modules = { Reference.FileType.MZML: MzMl,
		Reference.FileType.MGF: Mgf,
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

def TemplateFunctions():
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

	def run(self):
		self.Module.ToBinary(self.Source, open(self.Dest, "w"), self.Links)


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
		data = tempfile.NamedTemporaryFile(dir = ".", prefix = "ConvertedFiles/", delete = False)
		referencers = { "protxml": Reference.LoadChainProt, "pepxml": Reference.LoadChainPep, "mgf": Reference.LoadChainMgf, "mzml": Reference.LoadChainMzml }
		files = referencers[query["type"]](binascii.unhexlify(query["file"]))
		fs = len(files)
		#Build the index file
		data.write(struct.pack("=I", fs))
		threads = range(fs)
		links = {}
		for i in threads:
			f = files[i]
			data.write(struct.pack("=BH", f.Type, len(f.Depends)))
			for d in f.Depends:
				data.write(struct.pack("=H", test(d < 0, 0xFFFF, d)))
			EncodeStringToFile(data, f.Name)
			links[f.Name] = i
		data.close()
		#Now generate all the data files
		for i in threads:
			f = files[i]
			t = ConverterThread(GetTypeParser(f.Type), f.Name, data.name + "_" + str(i), links) #FIXME: Security
			t.start()
			threads[i] = t
		jobid = Jobs.Add(threads)
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
	#try:
		query = DecodeQuery(request.query_string)
		try:
			links = FileLinks(query["file"])
		except:
			return HTTPNotFound()
		try:
			index = query["n"]
			typename = Reference.FileType.Name(links.Get(index).Type)
		except:
			index = links.GetTopInfo()
			typename = Reference.FileType.Name(index["type"])
			index = index["index"]
		files = "[" + ",".join(["{" + ",".join(["name:'" + os.path.split(l.Name)[1] + "'", "type:" + str(l.Type), "deps:[" + ",".join([str(d) for d in l.Depends]) + "]"]) + "}" for l in links]) + "]"
		return render_to_response(templates + "dataview.pt", { "file": query["file"], "index": index, "type": typename, "files": files }, request=request)
	#except:
	#	return HTTPBadRequest()

def ListResults(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	#try:
	t = query["type"]
	parser = Parsers[t]
	if TryGet(query, "level") == "adv":
		[scores, total, results] = parser.SearchAdvanced(fname + "_" + query["n"], urllib.unquote(query["q"]))
	else:
		[scores, total, results] = parser.SearchBasic(fname + "_" + query["n"], urllib.unquote(query["q"]))
	matches = len(results)
	score = parser.DefaultSortColumn(scores)
	try:
		sortcol = query["sort"]
	except:
		sortcol = score
	try:
		sortby = query["order"]
		if sortby == "asc":
			reverse = False
		else:
			reverse = True
	except:
		reverse = True
	sc = sortcol
	if sortcol == "score":
		sc = score
	if sc in ["hyperscore", "pp_prob", "ip_prob"]:
		reverse = not reverse
	results = sorted(results, key = lambda key: key.HitInfo[sortcol], reverse = reverse)
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
		r.style = DecodeDecoy(h["protein"])
	info = {"total": total, "matches": matches, "start": start + 1, "end": start + len(results), "type": t, "score": score, "file": query["file"], "datafile": query["n"], "hash": abs(hash(time.gmtime()))}
	return render_to_response(templates + t + "_results.pt", { "sortcol": sortcol, "sortdsc": reverse, "info": info, "results": results, "url": Literal(request.path_qs), "funcs": TemplateFunctions() }, request = request)
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
	try:
		[scores, results] = PepXML.SearchPeptide(fname, query["peptide"])
		total = len(results)
		score = PepXML.DefaultSortColumn(scores)
		try:
			sortcol = query["sort"]
		except:
			sortcol = "score"
		try:
			sortby = query["order"]
			if sortby == "asc":
				reverse = False
			else:
				reverse = True
		except:
			reverse = True
		sc = sortcol
		if sortcol == "score":
			sc = score
		if sc in ["hyperscore", "pp_prob", "ip_prob"]:
			reverse = not reverse
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
		results = sorted(results, key = lambda key: key[sortcol], reverse = reverse)
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
		columns = [{"name": "spectrum", "title": "Spectrum"}, {"name": "massdiff", "title": "Mass Diff"}, {"name": "score", "title": "Score"}, {"name": "engine", "title": "Search Engine"}, {"name": "engine_score", "title": "Engine Score"}]
		specs = render(templates + "pepxml_peptide_spectrums.pt", { "count": len(spectrums), "spectrums": spectrums}, request=request)
		instances = render(templates + "pepxml_peptide.pt", { "info": info, "peptides": results, "columns": columns, "sortcol": sortcol, "sortdsc": reverse, "funcs": TemplateFunctions() }, request=request)
		return Response(specs + '<div id="peptide_results_list">' + instances + "</div>", request=request)
	except:
		return HTTPBadRequest()

def SelectInfo(request):
	query = DecodeQuery(request.query_string)
	for c in query["type"]:
		if (c < 'a' or c > 'z') and c != '_':
			raise HTTPUnauthorized()
	#try:
	parser = FileLinks(query["file"]).GetParser(int(query["n"]))
	select = eval("parser.select_" + query["type"])
	results = select(GetQueryFileName(query), query)
	return render_to_response(templates + "select_" + query["type"] + ".pt", { "query": query, "results": results, "funcs": TemplateFunctions() }, request=request)
	#except:
	#	return HTTPBadRequest()

def ListPeptideTooltip(request):
	query = DecodeQuery(request.query_string)
	fname = GetQueryFileName(query)
	try:
		[scores, results] = PepXML.SearchPeptide(fname, query["peptide"])
		score = PepXML.DefaultSortColumn(scores)
		if score == "expect":
			reverse = False
		else:
			reverse = True
		results = sorted(results, key = lambda key: key[score], reverse = reverse)
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
			r["score"] = r[score]
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
		return render_to_response(templates + "pepxml_peptide_tooltip.pt", { "info": info, "peptides": results, "counts": SearchEngines.items(), "funcs": TemplateFunctions() }, request=request)
	except:
		return HTTPBadRequest()

def GetResource(request):
	MimeTypes = {
		"png": "image/png",
		"gif": "image/gif",
		"js": "text/javascript",
		"css": "text/css" }
	try:
		f = open("res/" + request.matchdict["file"], "r")
		res = Response(f.read(), content_type=MimeTypes[os.path.splitext(request.matchdict["file"])[1][1:]])
		res.expires = time.gmtime(time.time() + 3600 * 24 * 7)
		f.close()
	except:
		res = HTTPNotFound()
	return res

if __name__ == "__main__":
	Threads = {}
	JobsTotal = 0
	ThreadsLock = Lock()
	config = Configurator()
	config.add_route("list", "/list/{type}/")
	config.add_route("search_score", "/search/{type}/score/")
	
	config.add_route("upload", "/init")
	config.add_route("convert", "/init_local")
	config.add_route("query_init", "/query_init")
	config.add_route("view", "/view")
	config.add_route("results", "/results")
	config.add_route("peptide", "/peptide")
	config.add_route("select", "/select")
	config.add_route("tooltip_peptide", "/tooltip/peptide")
	config.add_route("res", "/res/{file:.+}")
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
	config.add_view(ListPeptideTooltip, route_name="tooltip_peptide")
	config.add_view(GetResource, route_name="res")
	app = config.make_wsgi_app()
	serve(app, host=conf.HOST, port=conf.PORT)
