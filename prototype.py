#!/usr/bin/python
import sys
sys.path.insert(1, "env/lib/python2.7")
import getsite

from paste.httpserver import serve
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.renderers import render
import binascii;
from xml.sax.saxutils import escape
import os
from threading import Thread
from pyramid.httpexceptions import *
import PepXML
import tempfile
import urllib
import re

templates = os.path.realpath(os.path.dirname(__file__))+ "/templates/"
converted = os.path.realpath(os.path.dirname(__file__))+ "/ConvertedFiles/"
decoy_regex = re.compile("^decoy_.*")
threads = {}

class ConverterThread(Thread):
	def __init__(self, src, dst=None):
		Thread.__init__(self)
		self.Source = src
		self.Dest = dst

	def run(self):
		PepXML.PepXml2Bin(self.Source, Dest = self.Dest)

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

def DecodeDecoy(protein):
	if decoy_regex.match(protein.lower()) != None:
		return "/" + protein
	return protein

def DumpPeptideResult(r, score):
	print(r)
	ret = " ".join([r["peptide_prev_aa"], r["peptide"], r["peptide_next_aa"], DecodeDecoy(r["protein"]), str(r["massdiff"]), str(r[score])])
	try:
		ret += " " + r["protein_descr"]
	except:
		ret += " "
	return ret

def DumpQueryResult(res, score):
	h = res.HitInfo
	ret = " ".join([str(res.QueryIndex), str(res.ResultIndex), str(res.HitIndex), str(res.HitMatches), str(res.TotalMatches), h["peptide_prev_aa"], h["peptide"], h["peptide_next_aa"], DecodeDecoy(h["protein"]), str(h["massdiff"]), str(h[score])])
	try:
		ret += " " + h["protein_descr"]
	except:
		ret += " "
	return ret

class Literal(object):
    def __init__(self, s):
        self.s =s

    def __html__(self):
        return self.s

def PepXml(request):
	#f=open(binascii.unhexlify(request.matchdict["file"]), "r") #FIXME: SECURITY
	return Response("<pre>" + escape(f.read(512 * 1024)) + "</pre>")
	#return Response(request.matchdict.keys())

def Xml(request):
	#f=open(binascii.unhexlify(request.matchdict["file"]), "r") #FIXME: SECURITY
	return Response(f.read(), content_type="application/xml")

def GetFile(request):
	try:
		extensions = {
			"pepxml": "pepBIN"
		}
		query = DecodeQuery(request.query_string)
		ext = extensions[request.matchdict["type"].lower()]
		f = tempfile.NamedTemporaryFile(dir = ".", prefix = "ConvertedFiles/", suffix = "." + ext, delete = False)
		converter = ConverterThread(binascii.unhexlify(query["file"]), f) #FIXME: Security
		converter.start()
		threads[converter.ident] = converter
		res = render(templates + "converting.pt", {"type": ext, "file": f.name[len(converted) : len(f.name) - 7], "tid": converter.ident}, request=request)
		return Response(res)
	except:
		return HTTPBadRequest()

def QueryGetFileStatus(request):
	try:
		query = DecodeQuery(request.query_string)
		t = threads[int(query["id"])]
		if t.isAlive():
			return Response("1", content_type="application/text")
		else:
			del threads[int(query["id"])]
			return Response("2", content_type="application/text")
	except:
		return Response("9", content_type="application/text")

def DisplayList(request):
	query = DecodeQuery(request.query_string)
	fname = query["file"]
	if fname.find("/") >= 0:
		return HTTPUnauthorized()
	fname = converted + fname + "." + request.matchdict["type"]
	try:
		scores = PepXML.GetAvaliableScores(fname)
		score = PepXML.SearchEngineName(scores)
		head = "<tr class=\\\"results_table_head\\\"><th><span onclick=\\\"Sort('peptide');\\\">Peptide</span></th><th><span onclick=\\\"Sort('protein');\\\">Protein</span></th><th><span onclick=\\\"Sort('masdiff');\\\">Mass Difference</span></th><th><span onclick=\\\"Sort('" + PepXML.DefaultSortColumn(scores) + "');\\\">" + score + "</span></th></tr>"
		res = render(templates + "list_" + request.matchdict["type"] + ".pt", {"type": request.matchdict["type"], "file": query["file"], "head": Literal(head)}, request=request)
	except:
		return HTTPNotFound()
	return Response(res)

def ListPeptide(request):
	query = DecodeQuery(request.query_string)
	try:
		fname = query["file"]
		if fname.find("/") >= 0:
			return HTTPUnauthorized()
		fname = converted + fname + "." + request.matchdict["type"]
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
			reverse = False
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
		return Response(" ".join([str(start), str(total)]) + "\n" + "\n".join([DumpPeptideResult(r, score) for r in results]))
	except:
		return HTTPBadRequest()

def SearchQuery(request):
	query = DecodeQuery(request.query_string)
	fname = query["file"]
	if fname.find("/") >= 0:
		return HTTPUnauthorized()
	fname = converted + fname + "." + request.matchdict["type"]
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
	try:
		fname = query["file"]
		if fname.find("/") >= 0:
			return HTTPUnauthorized()
		fname = converted + fname + "." + request.matchdict["type"]
		sid = int(query["sid"])
		qid = int(query["qid"])
		rid = int(query["rid"])
		hid = int(query["hid"])
	except:
		return HTTPBadRequest()
	[spectrum, results] = PepXML.PepBinGetScores(fname, sid, qid, rid, hid)
	#i = 0
	items = sorted(results.items())
	#styles = ["norm", "alt"]
	rows = spectrum;
	for name, val in items:
		#rows += "<tr class=\"" + styles[i] + "\" style=\"text-align: center;\"><td>" + name + "</td><td>" + str(val) + "</td></tr>"
		rows += "\n" + str(val) + " " + name;
		#i = (i + 1) % 2
	return Response(rows)
	#res = render(templates + "search_" + request.matchdict["type"] + "_score.pt", {"spectrum": "hello world", "results": Literal(rows)}, request=request)
	#except:
	#	return HTTPNotFound()
	#return Response(res)

def Tooltip(request):
		query = DecodeQuery(request.query_string)
	#try:
		fname = query["file"]
		if fname.find("/") >= 0:
			return HTTPUnauthorized()
		fname = converted + fname + "." + request.matchdict["type"]
		[scores, results] = PepXML.PepBinSearchPeptide(fname, query["peptide"])
		score = "expect"#PepXML.DefaultSortColumn(scores)
		#for r in results:
		#	print(r)
		#results = sorted(results, key = lambda key: key[score])
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
			rows += "".join(["<tr class=\"", styles[i], "\" style=\"text-align: center;\"><td>", str(r["massdiff"]), "</td><td>", str(r[score]), "</td><td>", engine, "</td><td>", engine_score, "</td></tr>"])
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
		return Response(disp + "<br/>" + hits + "<br/><table id=\"results\" style=\"width: 100%;\"><tr><th>Mass Difference</th><th>" + PepXML.SearchEngineName(scores) + "</th><th>Search Engine</th></th><th>Raw Score</th></tr>" + rows + "</table>")
	#except:
	#	return HTTPBadRequest()

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

def GetDojoResource(request):
	return GetResource(request, "dojo")

def GetImageResource(request):
	return GetResource(request, "images")
	
def GetStyleResource(request):
	return GetResource(request, "styles")

def GetDecoderResource(request):
	return GetResource(request, "decoders")

if __name__ == "__main__":
	config = Configurator()
	config.add_route("pepxml", "/pepxml/{file}")
	config.add_route("xml", "/xml/{file}")
	config.add_route("get", "/get/{type}/")
	config.add_route("query_get", "/query_get")
	config.add_route("list", "/list/{type}/")
	config.add_route("list_peptide", "/list/{type}/peptide")
	config.add_route("search_query", "/search/{type}/query/{level}")
	config.add_route("search_hit", "/search/{type}/hit/")
	config.add_route("search_score", "/search/{type}/score/")
	config.add_route("tooltip", "/tooltip/{type}/{field}")
	config.add_route("image", "/images/{file}")
	config.add_route("style", "/styles/{file}")
	config.add_route("dojo", "/dojo/{file:.+}")
	config.add_route("decoders", "/decoders/{file}")
	config.add_view(PepXml, route_name="pepxml")
	config.add_view(Xml, route_name="xml")
	config.add_view(GetFile, route_name="get")
	config.add_view(QueryGetFileStatus, route_name="query_get")
	config.add_view(DisplayList, route_name="list")
	config.add_view(ListPeptide, route_name="list_peptide")
	config.add_view(SearchQuery, route_name="search_query")
	config.add_view(SearchHit, route_name="search_hit")
	config.add_view(SearchScore, route_name="search_score")
	config.add_view(Tooltip, route_name="tooltip")
	config.add_view(GetImageResource, route_name="image")
	config.add_view(GetStyleResource, route_name="style")
	config.add_view(GetDojoResource, route_name="dojo")
	config.add_view(GetDecoderResource, route_name="decoders")
	app = config.make_wsgi_app()
	serve(app, host="127.0.0.1", port=8000)
