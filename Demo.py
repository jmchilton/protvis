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
import PepXML
import ProtXML
import tempfile
import urllib
import re
from HttpUtil import *;

templates = os.path.realpath(os.path.dirname(__file__))+ "/templates/"
converted = os.path.realpath(os.path.dirname(__file__))+ "/ConvertedFiles/"
decoy_regex = re.compile(r"^decoy_.*")
spectrum_regex = re.compile(r"(.+?)(\.mzML)?\.[0-9]+\.[0-9]+\.[0-9]+")

Renderers = {
	"pepBIN": PepXML,
	"protBIN": ProtXML,
}

class ConverterThread(Thread):
	def __init__(self, func, src, dst=None):
		Thread.__init__(self)
		self.Source = src
		self.Dest = dst
		self.Function = func

	def run(self):
		self.Function(self.Source, self.Dest)

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

def GetFileName(request, query):
	try:
		fname = query["file"]
	except:
		raise HTTPBadRequestError()
	if fname.find("/") >= 0:
		raise HTTPUnauthorized()
	return converted + fname + "." + request.matchdict["type"]

def DecodeDecoy(protein):
	if decoy_regex.match(protein.lower()) != None:
		return "/" + protein
	return protein

def DumpPeptideResult(r, score):
	if "hyperscore" in r:
		engine = "X-Tandem"
		engine_score = str(r["hyperscore"])
	elif "ionscore" in r:
		engine = "Mascot"
		engine_score = str(r["ionscore"])
	elif "expect" in r:
		engine = "Omssa"
		engine_score = str(r["expect"])
	else:
		engine = ""
		engine_score = ""
	return " ".join([r["spectrum"], str(r["massdiff"]), str(r[score]), engine, engine_score])

def DumpQueryResult(res, score):
	h = res.HitInfo
	ret = " ".join([str(res.QueryIndex), str(res.ResultIndex), str(res.HitIndex), str(res.HitMatches), str(res.TotalMatches), h["peptide_prev_aa"], h["peptide"], h["peptide_next_aa"], DecodeDecoy(h["protein"]), str(h["massdiff"]), str(h[score])])
	try:
		ret += " " + h["protein_descr"]
	except:
		ret += " "
	return ret

def PepXml(request):
	#f=open(binascii.unhexlify(request.matchdict["file"]), "r") #FIXME: SECURITY
	return Response("<pre>" + escape(f.read(512 * 1024)) + "</pre>")
	#return Response(request.matchdict.keys())

def Xml(request):
	#f=open(binascii.unhexlify(request.matchdict["file"]), "r") #FIXME: SECURITY
	return Response(f.read(), content_type="application/xml")

def DisplayList(request):
	query = DecodeQuery(request.query_string)
	fname = GetFileName(request, query)
	try:
		t = request.matchdict["type"]
		return render_to_response(templates + "list_" + t + ".pt", Renderers[t].DisplayList(request, query, fname), request = request)
	except:
		return HTTPNotFound()

def ListPeptide(request):
	class Spec:
		def __init__(self, spectrum, count):
			self.Spectrum = spectrum
			self.Count = count

		def __str__(self):
			return str(self.Count) + "/" + self.Spectrum

	query = DecodeQuery(request.query_string)
	fname = GetFileName(request, query)
	try:
		[scores, results] = PepXML.PepBinSearchPeptide(fname, query["peptide"])
		total = len(results)
		score = PepXML.DefaultSortColumn(scores)
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
		if sortcol in ["hyperscore", "pp_prob", "ip_prob"]:
			reverse = not reverse
		SearchEngines = { "X-Tandem": 0, "Mascot": 0, "Omssa": 0 }
		spectrums = {}
		for r in results:
			if "hyperscore" in r:
				SearchEngines["X-Tandem"] += 1
			elif "ionscore" in r:
				SearchEngines["Mascot"] += 1
			elif "expect" in r:
				SearchEngines["Omssa"] += 1
			spec = spectrum_regex.sub(r"\1", r["spectrum"])
			try:
				spectrums[spec] += 1
			except:
				spectrums[spec] = 1
		sort = sorted([Spec(k, v) for k, v in spectrums.items()], reverse = True, key = lambda spec: spec.Count)
		spectrums = " ".join([str(s) for s in sort])
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
				results = results[start:start + limit]
			else:
				results = restults[start:]
		elif limit > 0:
			results = results[:limit]
		return Response(" ".join([str(start), str(total), query["peptide"], str(SearchEngines["X-Tandem"]), str(SearchEngines["Mascot"]), str(SearchEngines["Omssa"])]) + "\n" + spectrums + "\n" + "\n".join([DumpPeptideResult(r, score) for r in results]))
	except:
		return HTTPBadRequest()

def SearchQuery(request):
	query = DecodeQuery(request.query_string)
	fname = GetFileName(request, query)
	if request.matchdict["level"] == "basic":
		[scores, TotalQueries, results] = PepXML.PepBinSearchBasic(fname, urllib.unquote(query["q"]))
	else:
		[scores, TotalQueries, results] = PepXML.PepBinSearchAdvanced(fname, urllib.unquote(query["q"]))
	total = len(results)
	score = PepXML.DefaultSortColumn(scores)
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
	if sortcol in ["hyperscore", "pp_prob", "ip_prob"]:
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
			results = restults[start:]
	elif limit > 0:
		results = results[:limit]
	resp = " ".join([str(start), str(total), str(TotalQueries)])
	if len(results) > 0:
		resp += "\n" + "\n".join([DumpQueryResult(r, score) for r in results])
	return Response(resp)

def SearchHit(request):
	query = DecodeQuery(request.query_string)
	return Response("search hit")

def SearchScore(request):
	query = DecodeQuery(request.query_string)
	fname = GetFileName(request, query)
	try:
		sid = int(query["sid"])
		qid = int(query["qid"])
		rid = int(query["rid"])
		hid = int(query["hid"])
	except:
		return HTTPBadRequest()
	[spectrum, results] = PepXML.PepBinGetScores(fname, sid, qid, rid, hid)
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
	return Response(rows)

def Tooltip(request):
	query = DecodeQuery(request.query_string)
	fname = GetFileName(request, query)
	try:
		[scores, results] = PepXML.PepBinSearchPeptide(fname, query["peptide"])
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
		i = 0
		styles = ["norm", "alt"]
		rows = "";
		for r in results:
			if "hyperscore" in r:
				engine = "X-Tandem"
				engine_score = str(r["hyperscore"])
			elif "ionscore" in r:
				engine = "Mascot"
				engine_score = str(r["ionscore"])
			elif "expect" in r:
				engine = "Omssa"
				engine_score = str(r["expect"])
			else:
				engine = ""
				engine_score = ""
			rows += "".join(["<tr class=\"", styles[i], "\" style=\"text-align: center;\"><td style=\"text-align: left;\">" + r["spectrum"] + "</td><td>", str(r[score]), "</td><td>", engine, "</td><td>", engine_score, "</td></tr>"])
			i = (i + 1) % 2
		if count > shown:
			disp = "Displaying best " + str(shown) + " of " + str(count) + " results"
		elif count == 1:
			disp = "Displaying the only result"
		else:
			disp = "Displaying all " + str(shown) + " results"
		hits = ""
		for k, v in SearchEngines.items():
			if v > 0:
				if len(hits) > 0:
					hits += ", "
				hits += str(v) + " from " + k
		return Response(disp + "<br/>" + hits + "<br/><table id=\"results\" style=\"width: 100%;\"><tr><th>Spectrum</th><th>" + PepXML.SearchEngineName(scores) + "</th><th>Search Engine</th></th><th>Raw Score</th></tr>" + rows + "</table>")
	except:
		return HTTPBadRequest()

def Convert(request):
	#for when this is running on the same server as galaxy
	#just use the local files directly
	try:
		query = DecodeQuery(request.query_string)
		data = tempfile.NamedTemporaryFile(dir = ".", prefix = "ConvertedFiles/", delete = False)
		files = query["files"].split(";")
		data.write(struct.pack("=I", len(files)))
		data.seek(len(files) * 4, 1)
		offsets = range(len(files))
		threads = range(len(files))
		for i in threads:
			f = files[i].split(":")
			offsets[i] = data.tell()
			data.write(binascii.unhexlify(f[1]))
			files[i] = [f[0], binascii.unhexlify(f[1])]
			t = ConverterThread(f[0], binascii.unhexlify(query["file"]), data.name) #FIXME: Security
			t.start()
			threads[i] = t
		data.seek(4)
		data.write("".join([struct.pack("=I", o) for o in offsets]))
		data.close()
		ThreadsLock.acquire()
		jobid = JobsTotal
		JobsTotal += 1
		threads[jobid] = threads
		ThreadsLock.release()
		return render_to_response(templates + "upload.pt", { "type": ext, "file": data.name[len(converted):], "jobid": jobid }, request=request)
	except:
		return HTTPBadRequest()

def Upload(request):
	#uploading from a remote server
	return HTTPBadRequest()

def QueryInitStatus(request):
	try:
		query = DecodeQuery(request.query_string)
		_id = int(query["id"])
		threads = Threads[_id]
		alive = 0
		for t in threads:
			if t.isAlive():
				alive += 1
		if alive == 0:
			del threads[_id]
		return Response(str(alive), content_type="application/text")
	except HTTPException:
		raise
	except:
		return Response("-", content_type="application/text")

def GetResource(request, res):
	MimeTypes = {
		"png": "image/png",
		"gif": "image/gif",
		"js": "text/javascript",
		"css": "text/css" }
	try:
		f = open("resource/" + res + "/" + request.matchdict["file"], "r")
		res = Response(f.read(), content_type=MimeTypes[os.path.splitext(request.matchdict["file"])[1][1:]])
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
	config.add_route("list_peptide", "/list/{type}/peptide")
	config.add_route("search_query", "/search/{type}/query/{level}")
	config.add_route("search_hit", "/search/{type}/hit/")
	config.add_route("search_score", "/search/{type}/score/")
	config.add_route("tooltip", "/tooltip/{type}/{field}")
	
	config.add_route("upload", "/init")
	config.add_route("convert", "/init_local")
	config.add_route("query_init", "/query_init")
	config.add_route("view", "/view/{file:.+}")
	config.add_route("res", "/res/{file:.+}")
	config.add_view(DisplayList, route_name="list")
	config.add_view(ListPeptide, route_name="list_peptide")
	config.add_view(SearchQuery, route_name="search_query")
	config.add_view(SearchHit, route_name="search_hit")
	config.add_view(SearchScore, route_name="search_score")
	config.add_view(Tooltip, route_name="tooltip")
	config.add_view(Convert, route_name="convert")
	config.add_view(QueryInitStatus, route_name="query_init")
	config.add_view(Upload, route_name="upload")
	config.add_view(GetResource, route_name="res")
	app = config.make_wsgi_app()
	serve(app, host="127.0.0.1", port=8000)
