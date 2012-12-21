from wsgiref.simple_server import make_server  # required though unused
from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.response import Response
from pyramid.renderers import render, render_to_response
import binascii
import os
from pyramid.httpexceptions import *
import urllib
import re
import Reference
from Common import *
from FileTypes import *
from peptide import read_peptide_info
from job_manager import Jobs
import GPMDB
import time
import subprocess
import parameters
import platform

converted = parameters.converted
templates = parameters.HOME + "/templates/"
decoy_regex = re.compile(parameters.DECOY_REGEX)
spectrum_regex = re.compile(parameters.SPECTRUM_REGEX)

Parsers = {"mzml": MzML, "mgf": MGF, "pep": PepXML, "prot": ProtXML}
Referencers = {"protxml": Reference.LoadChainProt, "pepxml": Reference.LoadChainPep, "mgf": Reference.LoadChainMgf, "mzml": Reference.LoadChainMzml}


#returns an script which will display an error message and retry button when an error occurs during an ajax call
#this prevents it from returning an epty response which is then cached
def AjaxError(msg, req):
    return Response('<script>DetailsDialog.attr("title", "Error Loading Data").attr("style", "width: 300px;").attr("content", "' + msg + '");DetailsDialog.show();</script>', request=req)


#Defines a set of global variables which will be automatically defined in every template file
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
            mods = sorted(mods, key=lambda mam: mam[0], reverse=True)
            for m in mods:
                (pos, mass) = m
                pep = pep[:pos] + '<span class="modification">[' + str(int(mass)) + ']</span>' + pep[pos:]
        return Literal(pep)

    def unique_dataset():
        return abs(hash(time.gmtime()))

    return {"test": test, "Literal": Literal, "render_peptide": render_peptide, "try_get": TryGet, "urlencode": urllib.quote, "unique_dataset": unique_dataset}


#Extracts the name of the file that the HTTP request was for, and checks that it does not try to get a file from another folder
def GetQueryFileName(query):
    try:
        fname = query["file"]
    except:
        raise HTTPBadRequest_Param("file")
    if fname.find("/") >= 0:
        raise HTTPUnauthorized()
    return converted + fname


#Checks the name of a protein to see if it is a decoy in order to change the color of it in the list
def DecodeDecoy(protein):
    if decoy_regex.match(protein.lower()) != None:
        return "rowdecoy"
    return "row"


#sorts a list of peptides using the best avaliable score
def SortPeptides(results, sortcol, score, reverse=False):
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
        return sorted(results, cmp=Comparator, reverse=reverse)
    else:
        return sorted(results, key=lambda key: key[sortcol], reverse=reverse)


#HTTP: Returns the homepage
def Index(req):
    #for when this is used as a standalone tool
    return render_to_response(templates + "index.pt", {}, request=req)


#HTTP: Handles the uploading of files from the homepage
def Upload(req):
    #uploading from a remote server
    fs = req.POST.getall("uploadedfiles[]")
    if platform.system() == "Windows":  # Windows has an extra .file in here for some reason
        for f in fs:
            if hasattr(f.file, "file"):
                f.file = f.file.file
    for f in fs:
        f.file.seek(0)
    #Build the index file
    if not os.path.exists(converted):
        os.makedirs(converted)
    try:
        cleanup = req.POST["delete"]
    except:
        cleanup = 7
    (jobid, f) = Jobs.add_job("remote", fs, cleanup * 24 * 60 * 60)
    json_response = '{"file":"' + f + '","jobid":' + str(jobid) + '}\r\n'
    resp = Response(json_response)
    resp.cache_expires(0)
    return resp


def _read_shortcut_params(req):
    """
    Params to jump to render specific peptide or jump to specific spectrum.
    """
    try:
        req_peptide = req.GET["peptide"]
        peptide_info = read_peptide_info(req_peptide)
        req.session["peptides"] = [peptide_info]
    except KeyError:
        pass


def ConvertUrl(req):
    _read_shortcut_params(req)
    default_hash = ""
    try:
        req_scan = req.GET["scan"]
        default_hash = "#S0;None;%s" % req_scan
    except KeyError:
        pass

    try:
        url = req.GET["url"]
    except:
        return HTTPBadRequest_Param("url")
    try:
        ref = Referencers[req.GET["type"]]
    except:
        return HTTPBadRequest_Param("type")
    #Build the index file
    if not os.path.exists(converted):
        os.makedirs(converted)
    (jobid, f) = Jobs.add_job("url", str(url), 7 * 24 * 60 * 60, ref=ref)
    resp = render_to_response(templates + "upload.pt", {"file": f, "jobid": str(jobid), "default_hash": default_hash}, request=req)
    resp.cache_expires(0)
    return resp


#HTTP: Handles the processing of files from a locally accesible galaxy
def Convert(req):
    #for when this is running on the same server as galaxy
    #just use the local files directly
    try:
        fs = binascii.unhexlify(req.GET["file"])
    except:
        return HTTPBadRequest_Param("file")
    try:
        ref = Referencers[req.GET["type"]]
    except:
        return HTTPBadRequest_Param("type")
    #Build the index file
    if not os.path.exists(converted):
        os.makedirs(converted)
    (jobid, f) = Jobs.add_job("local", fs, 7 * 24 * 60 * 60, ref=ref)
    resp = render_to_response(templates + "upload.pt", {"file": f, "jobid": str(jobid)}, request=req)
    resp.cache_expires(0)
    return resp


#HTTP: Checks the progress of processing and converting files after uploaded
def QueryInitStatus(req):
    try:
        f = req.GET["file"]
    except:
        return HTTPBadRequest_Param("file")
    try:
        i = int(req.GET["id"])
    except:
        return HTTPBadRequest_Param("id")
    try:
        alive = Jobs.QueryStatus(f, i)
        resp = Response(str(alive) + "\r\n", request=req)
    except HTTPException:
        raise
    except:
        resp = Response("-\r\n", request=req)
    resp.cache_expires(0)
    return resp


#HTTP: Addes a file to an existing dataset
#A reference to the file must already exist in the dataset, but the contents of the file missing
def AddFile(req):
    def DecreaseLarger(arr, n):
        for i in xrange(len(arr)):
            if arr[i] > n:
                arr[i] -= 1

    fname = GetQueryFileName(req.GET)
    links = Reference.FileLinks(fname)
    try:
        n = req.GET["n"]
        ni = int(n)
    except:
        return HTTPBadRequest_Param("n")
    l = links[ni]
    try:
        s = req.POST["datas[]"]
    except:
        try:
            s = req.POST["data0"]
        except:
            try:
                s = req.POST["data"]
            except:
                return HTTPBadRequest_Param("data")
    sf = s.file
    sf.seek(0)
    t = l.Type & 0x7F
    if t == Reference.FileType.UNKNOWN:
        t = TryGet(req.POST, "type")
        if t != None and int(t) != 0:
            t = int(t)
        else:
            t = Reference.GuessType(sf)
            if t == Reference.FileType.UNKNOWN:
                return HTTPUnsupportedMediaType("File type could not be determined")
            sf.seek(0)
    sf.seek(0)
    t2 = Reference.GetTypeParser(t).ToBinary(sf, fname + "_" + n, s.filename)
    l.Name = s.filename
    if t2 > t:
        t = t2
    l.Type = t
    same = TryGet(req.POST, "similar")
    removed = []
    if same != None:
        same = [int(m) for m in set(same.split(","))]
        for idx in xrange(len(same)):
            i = same[idx]
            for j in links:
                if i in j.Depends:
                    removed.append(str(i))
                    j.Depends.remove(i)
                    if not ni in j.Depends:
                        j.Depends = list(set(j.Depends + [ni]))
                DecreaseLarger(j.Depends, i)
            if ni > i:
                ni -= 1
                n = str(ni)
            del links.Links[i]
            DecreaseLarger(same, i)
            for i in xrange(i, len(links) - 1):
                f = fname + "_" + str(i + 1)
                if os.path.exists(f):
                    os.rename(f, fname + "_" + str(i))
    new = Reference.LoadChainGroup([[s.filename, sf]], t)
    deps_start = len(links)
    deps_exists = []
    added = []
    for f in new:
        if f.Stream != sf:
            found = False
            i = 0
            for link in links:
                if link.Name == f.Name:
                    found = True
                    deps_exists.append(i)
                    break
                i += 1
            if not found:
                if (f.Type & ~Reference.FileType.MISSING) == Reference.FileType.DATABASE:
                    links.AddDB(f.Name)
                else:
                    added.append(str(len(links)))
                    links.Add(f.Name, f.Type, [])
    l.Depends = deps_exists + range(deps_start, len(links))
    links.Write(fname)
    resp = Response('{"added":[' + ",".join(added) + '],"removed":[' + ",".join(removed) + '],"select":' + n + ',"files":[' + ",".join(['{"name":"' + os.path.split(l.Name)[1] + '","type":' + str(l.Type) + ',"deps":[' + ",".join([test(d < 65535, str(d), "-1") for d in l.Depends]) + ']}' for l in links]) + ']}\r\n', request=req)
    resp.cache_expires(0)
    return resp


#HTTP: Merges a file which the contents could not be found into a file which could
#useful for when the same file is references with different file extensions as the tools add and remove them at their will
def MergeFile(req):
    def DecreaseLarger(arr, n):
        for i in xrange(len(arr)):
            if arr[i] > n:
                arr[i] -= 1

    fname = GetQueryFileName(req.GET)
    links = Reference.FileLinks(fname)
    try:
        n = int(req.GET["n"])
    except:
        return HTTPBadRequest_Param("n")
    try:
        o = int(req.GET["o"])
    except:
        return HTTPBadRequest_Param("o")
    for j in links:
        if n in j.Depends:
            j.Depends.remove(n)
            if not o in j.Depends:
                j.Depends = sorted(j.Depends + [o])
        DecreaseLarger(j.Depends, n)
    for i in xrange(n, len(links) - 1):
        f = fname + "_" + str(i + 1)
        if os.path.exists(f):
            os.rename(f, fname + "_" + str(i))
    if o > n:
        o -= 1
    del links.Links[n]
    links.Write(fname)
    resp = Response('{"removed":[' + str(n) + '],"select":' + str(o) + ',"files":[' + ",".join(['{"name":"' + os.path.split(l.Name)[1] + '","type":' + str(l.Type) + ',"deps":[' + ",".join([test(d < 65535, str(d), "-1") for d in l.Depends]) + ']}' for l in links]) + ']}\r\n', request=req)
    resp.cache_expires(0)
    return resp


#HTTP: The main results page
#it does not contain any data, only the information relating to what data you had, what files, how they were linked, ...
def View(req):
    try:
        links = Reference.FileLinks(GetQueryFileName(req.GET))
    except HTTPException:
        raise
    except:
        return HTTPNotFound_Data(req.GET["file"])
    try:
        index = int(req.GET["n"])
        typename = Reference.FileType.NameBasic(links.Links[req.GET["n"]].Type)
    except:
        index = links.GetTopInfo()
        typename = Reference.FileType.NameBasic(index["type"])
        index = index["index"]
    files = ",".join(["{" + ",".join(["name:'" + os.path.split(l.Name)[1] + "'", "type:" + str(l.Type), "deps:[" + ",".join([test(d < 65535, str(d), "-1") for d in l.Depends]) + "]"]) + "}" for l in links])
    return render_to_response(templates + "dataview.pt", {"file": req.GET["file"], "index": index, "type": typename, "files": files, "nfiles": len(links)}, request=req)


#HTTP: Retreives the main list of results for the file
#has special cases for mzML LC view and missing file
def ListResults(req):
    fname = GetQueryFileName(req.GET)
    try:
        links = Reference.FileLinks(fname)
    except HTTPException:
        raise
    except:
        return HTTPNotFound_Data(req.GET["file"])
    try:
        n = req.GET["n"]
        ni = int(n)
    except:
        return HTTPBadRequest_Param("n")
    q = TryGet(req.GET, "q")
    if q == None:
        q = ""
    else:
        q = urllib.unquote(q)
    if links.Links[ni].Type & Reference.FileType.MISSING:
        exts = ["mzml", "mzxml", "mgf", "pepxml", "pep", "protxml", "prot", "xml", "dat"]
        mypath = os.path.split(links.Links[ni].Name)
        myname = mypath[1].split(".")
        j = len(myname) - 1
        while j >= 0:
            if myname[j].lower() in exts:
                del myname[j]
            else:
                break
            j -= 1
        myname = ".".join(myname)
        similar = []
        i = 0
        for l in links.Links:
            if (l.Type & Reference.FileType.MISSING) == Reference.FileType.MISSING and i != ni:
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
                        similar.append({"index": i, "name": os.path.basename(l.Name)})
            i += 1
        return render_to_response(templates + "missing_results.pt", {"links": links, "query": req.GET, "similar": similar, "os": os}, request=req)
    else:
        t = Reference.FileType.NameBasic(links.Links[ni].Type)
        try:
            parser = Parsers[t]
            if parser == None:
                return Response("The server has not been configured to understand " + t + " files")
        except:
            return Response("The type of the selected file could not be determined")
        if t == "mzml" and TryGet(req.GET, "list") != "1":
            results = parser.Display(fname + "_" + n, req.GET)
            points = parser.points_ms2_chunks(fname + "_" + n, 16)
            info = {"type": t, "file": req.GET["file"], "datafile": n, "query": q, "datas": links.Types()}
            return render_to_response(templates + t + "_display.pt", {"info": info, "results": results, "points": points, "url": Literal(req.path_qs)}, request=req)
        else:
            if TryGet(req.GET, "level") == "adv":
                [scores, total, results] = parser.Search(fname + "_" + n, EncodeTermsAdvanced(q))
            else:
                [scores, total, results] = parser.Search(fname + "_" + n, EncodeTermsBasic(q))
            matches = len(results)
            [score, scorename, reverses] = parser.DefaultSortColumn(scores)
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
            results = sorted(results, key=lambda key: key.HitInfo[sortcol], reverse=test(test(sortcol == "score", score, sortcol) in reverses, not reverse, reverse))
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
                    if start + limit > len(results):
                        start -= start % limit
                    results = results[start:start + limit]
                else:
                    results = results[start:]
            elif limit > 0:
                results = results[:limit]
            for r in results:
                try:
                    r.style = DecodeDecoy(r.HitInfo["protein"])
                except:
                    r.style = "row"
            info = {"total": total, "matches": matches, "start": start + 1, "end": start + len(results), "type": t, "score": score, "scorename": scorename, "file": req.GET["file"], "datafile": n, "query": q, "datas": links.Types(), "limit": limit}
            return render_to_response(templates + t + "_results.pt", {"sortcol": sortcol, "sortdsc": reverse, "info": info, "results": results, "url": Literal(req.path_qs)}, request=req)


#HTTP: Gets a list of all proteins which reference a given peptide in a single file
def ListPeptide(req):
    fname = GetQueryFileName(req.GET)
    try:
        n = req.GET["n"]
        int(n)
    except:
        return HTTPBadRequest_Param("n")
    try:
        peptide = req.GET["peptide"]
    except:
        return HTTPBadRequest_Param("peptide")

    class Spec:
        def __init__(self, spectrum, count):
            self.Spectrum = spectrum
            self.Count = count

        def __str__(self):
            return str(self.Count) + "/" + self.Spectrum

    def ViewSpectrum(row):
        return "ShowSpectrumFromPeptide(" + n + ", '" + row["spectrum"] + "', " + str(row["query__offset"]) + ", " + str(row["hit__offset"]) + ");"

    [scores, results] = PepXML.SearchPeptide(fname + "_" + n, peptide)
    if results == None or len(results) == 0:
        return AjaxError("The requested peptide could not be found.", req)
    total = len(results)
    [score, scorename, reverses] = PepXML.DefaultSortColumn(scores)
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
    SearchEngines = {"X-Tandem": 0, "Mascot": 0, "Omssa": 0}
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
    if SearchEngines["X-Tandem"] == 0:
        del SearchEngines["X-Tandem"]
    if SearchEngines["Mascot"] == 0:
        del SearchEngines["Mascot"]
    if SearchEngines["Omssa"] == 0:
        del SearchEngines["Omssa"]
    spectrums = sorted([Spec(k, v) for k, v in spectrums.items()], reverse=True, key=lambda spec: spec.Count)
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
            results = results[start:start + limit]
        else:
            results = results[start:]
    elif limit > 0:
        results = results[:limit]
    info = {"total": total, "start": start + 1, "end": start + len(results), "peptide": peptide}
    columns = [{"name": "spectrum", "title": "Spectrum", "click": ViewSpectrum}, {"name": "massdiff", "title": "Mass Diff"}, {"name": "score", "title": "Score"}, {"name": "engine", "title": "Search Engine"}, {"name": "engine_score", "title": "Engine Score"}]
    specs = render(templates + "pepxml_peptide_spectrums.pt", {"count": len(spectrums), "spectrums": spectrums}, request=req)
    instances = render(templates + "pepxml_peptide.pt", {"info": info, "peptides": results, "columns": columns, "datafile": n, "sortcol": sortcol, "sortdsc": reverse, "counts": SearchEngines.items()}, request=req)
    return Response('<span class="link" onclick="ReturnToResults(' + n + ');">Back to all results</span>' + specs + '<div id="peptide_results_list">' + instances + "</div>", request=req)


#HTTP: A generic function which calls "select_X" on the datafile
#used to retreive: scores avaliable for a pepXML result, coverage of a protein and indistinguishable results from protXML
def SelectInfo(req):
    fname = GetQueryFileName(req.GET)
    try:
        n = int(req.GET["n"])
    except:
        return HTTPBadRequest_Param("n")
    try:
        t = req.GET["type"]
        if "/" in t:
            raise Exception()
    except:
        return HTTPBadRequest_Param("type")
    links = Reference.FileLinks(fname)
    parser = links.GetParser(n)
    select = eval("parser.select_" + t)
    results = select(fname, req.GET)
    return render_to_response(templates + "select_" + t + ".pt", {"query": req.GET, "results": results}, request=req)


#HTTP: Retreives a PNG image for the given MS level showing the datapoints
def SpectumLC(req):
    fname = GetQueryFileName(req.GET)
    try:
        n = req.GET["n"]
        ni = int(n)
    except:
        return HTTPBadRequest_Param("n")
    try:
        w = int(req.GET["w"])
    except:
        return HTTPBadRequest_Param("w")
    try:
        h = int(req.GET["h"])
    except:
        return HTTPBadRequest_Param("h")
    parser = Reference.FileLinks(fname).GetParser(ni)
    x1 = TryGet(req.GET, "x1")
    x2 = TryGet(req.GET, "x2")
    y1 = TryGet(req.GET, "y1")
    y2 = TryGet(req.GET, "y2")
    if x1 == None:
        x1 = -1.0
    else:
        x1 = float(x1)
    if x2 == None:
        x2 = -1.0
    else:
        x2 = float(x2)
    if y1 == None:
        y1 = -1.0
    else:
        y1 = float(y1)
    if y2 == None:
        y2 = -1.0
    else:
        y2 = float(y2)
    level = req.GET["level"]
    if (level == "1s"):
        try:
            contrast = float(req.GET["contrast"])
        except:
            return HTTPBadRequest_Param("contrast")
        return Response(parser.spectrum_ms1_smooth(fname + "_" + n, contrast, w, h, x1, x2, y1, y2), request=req, content_type="image/png")
    if (level == "1p"):
        try:
            contrast = float(req.GET["contrast"])
        except:
            return HTTPBadRequest_Param("contrast")
        return Response(parser.spectrum_ms1_points(fname + "_" + n, contrast, w, h, x1, x2, y1, y2), request=req, content_type="image/png")
    if (level == "2"):
        return Response(parser.spectrum_ms2(fname + "_" + n, w, h, x1, x2, y1, y2), request=req, content_type="image/png")
    else:
        return HTTPBadRequest_Param("level")


#HTTP: Retreives a spectrum viewer for the selected spectrum
def Spectrum(req):
    def PeptideInfo(pep):
        peptide = {"peptide": pep["peptide"], "modification_info": pep["modification_info"], "protein": pep["protein"], "sort": pep["expect"], "masstol": pep["masstol"]}
        if "hyperscore" in pep:
            peptide["engine"] = "X-Tandem"
            peptide["score"] = str(pep["hyperscore"])
        elif "ionscore" in pep:
            peptide["engine"] = "Mascot"
            peptide["score"] = str(pep["ionscore"])
        elif "expect" in pep:
            peptide["engine"] = "Omssa"
            peptide["score"] = str(pep["expect"])
        else:
            peptide["engine"] = ""
            peptide["score"] = ""
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
                    cterm = TryGet(mi, "mod_cterm_mass")
                    if cterm != None:
                        cterm_mod = cterm
                mods += [{"index": m[0], "mass": m[1], "aa": pep["peptide"][m[0]]} for m in mi.get("mod_aminoacid_mass", [])]
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
            mods = sorted(mods, key=lambda mam: mam["index"], reverse=True)
            for m in mods:
                pep = pep[:m["index"]] + '<span class="modification">[' + str(int(m["mass"])) + ']</span>' + pep[m["index"]:]
        return Literal(pep)

    fname = GetQueryFileName(req.GET)
    spectrum = TryGet(req.GET, "spectrum")
    datafile = TryGet(req.GET, "n")
    offset = TryGet(req.GET, "off")
    if offset == "None":
        offset = None
    filetype = None
    pep_datafile = None
    init_pep = 0
    peptide = None
    score = None
    if datafile == None:
        links = Reference.FileLinks(fname)
        possible = []
        pep_datafile = TryGet(req.GET, "pn")
        missing = False
        if pep_datafile == None:
            for i in xrange(len(links.Links)):
                l = links.Links[i]
                t = l.Type & ~Reference.FileType.MISSING
                if t == Reference.FileType.MZML or t == Reference.FileType.MGF:
                    if l.Type & Reference.FileType.MISSING:
                        missing = True
                    else:
                        possible.append(i)
        else:
            deps = links.Links[int(pep_datafile)].Depends
            i = 0
            while i < len(deps):
                if deps[i] >= 0 and deps[i] < len(links.Links):
                    deps += links.Links[deps[i]].Depends
                i += 1
            for d in deps:
                if d >= 0 and d < len(links.Links):
                    l = links.Links[d]
                    t = l.Type & ~Reference.FileType.MISSING
                    if t == Reference.FileType.MZML or t == Reference.FileType.MGF:
                        if l.Type & Reference.FileType.MISSING:
                            missing = True
                        else:
                            possible.append(d)
        pep_datafile = int(pep_datafile)
        possible = list(set(possible))
        offset = -1
        for t in [Reference.FileType.MGF, Reference.FileType.MZML]:
            if offset < 0:
                for f in possible:
                    if links.Links[f].Type == t:
                        offset = Parsers[Reference.FileType.NameBasic(t)].GetOffsetFromSpectrum(fname + "_" + str(f), spectrum)
                        if offset >= 0:
                            datafile = f
                            filetype = t
                            break
        if datafile == None and not missing and len(possible) == 1:  # There is only 1 choice of where the spectrum came from
            f = possible[0]
            t = links.Links[f].Type
            offset = Parsers[Reference.FileType.NameBasic(t)].GetOffsetFromSpectrum(fname + "_" + str(f), spectrum, True)
            if offset >= 0:
                datafile = f
                filetype = t
        pep_query_offset = TryGet(req.GET, "pqoff")
        if pep_query_offset != None:
            #pep_hit_offset = TryGet(req.GET, "phoff")
            #if pep_hit_offset == None:
            peptide = PepXML.GetQueryHitInfosFromOffset(fname + "_" + str(pep_datafile), int(pep_query_offset))
            pep = TryGet(req.GET, "pep")
            if pep != None:
                i = 0
                for p in peptide["peptides"]:
                    if p["peptide"] == pep:
                        init_pep = i
                        break
                    i += 1
            #else:
            #       sortcol = None
            #       pep = PepXML.GetHitInfo(fname + "_" + str(pep_datafile), int(pep_query_offset), int(pep_hit_offset))
            #       peptide = { "peptides":[pep], "precursor_neutral_mass":pep["precursor_neutral_mass"] }
    else:
        datafile = int(datafile)
    if datafile == None:
        return AjaxError("The requested spectrum could not be found.<br/> It's name may have been modified by some of the processing tools.", req)
    links = Reference.FileLinks(fname)
    if filetype == None:
        filetype = links.Links[datafile].Type
    i = 0
    if peptide == None:
        peptide = {"peptides": [], "precursor_neutral_mass": 0}
    for f in links.Links:
        if datafile in f.Depends and f.Type < Reference.FileType.PEPXML_COMPARE and i != pep_datafile:
            #peptide["peptides"] += PepXML.GetQueryHitInfosFromName(fname + "_" + str(i), spectrum)
            p = PepXML.GetQueryHitInfosFromName(fname + "_" + str(i), spectrum)
            if p != None:
                peptide["peptides"] += p
        i += 1
    if not peptide["peptides"]:
        try:
            peptide["peptides"] = req.session["peptides"]
        except KeyError:
            pass
    peptide["peptides"] = sorted([PeptideInfo(p) for p in peptide["peptides"]], key=lambda key: key["sort"])

    for r in peptide["peptides"]:
        try:
            r["style"] = DecodeDecoy(r["protein"])
        except:
            r["style"] = "row"
    parser = Parsers[Reference.FileType.NameBasic(filetype)]
    if datafile == None:
        raise HTTPBadRequest_Param("n")
    if spectrum and spectrum.isdigit():
        scan = int(spectrum)
        spectrum_info = parser.GetSpectrumFromScan(fname + "_" + str(datafile), scan)
        spectrum = "input.%d.%d.%d" % (scan, scan, spectrum_info["charge"])
        if offset == None or offset < 0:
            offset = spectrum_info["offset"]
    if offset == None and datafile != None:
        offset = parser.GetOffsetFromSpectrum(fname + "_" + str(datafile), spectrum)
    if offset == None or offset < 0:
        raise HTTPBadRequest_Param("offset")
    if spectrum != None:
        spec = spectrum.split(".")
        spectrum = {"file": Literal(".".join(spec[:-3]).replace("\\", "\\\\").replace("\"", "\\\"")), "scan": int(spec[-3]), "charge": int(spec[-1]), "offset": str(offset), "ions": parser.GetSpectrumFromOffset(fname + "_" + str(datafile), int(offset))}
    else:
        spectrum = {"file": None, "scan": 1, "charge": 1, "offset": str(offset), "ions": parser.GetSpectrumFromOffset(fname + "_" + str(datafile), int(offset))}
    return render_to_response(templates + "specview.pt", {"query": req.GET, "datafile": str(datafile), "spectrum": spectrum, "peptide": peptide, "init_pep": init_pep, "score": score, "render_peptide_lorikeet": render_peptide_lorikeet}, request=req)


#HTTP: Retreives the contents of a dynamic tooltip
#presently only the information on a peptide
def Tooltip(req):
    t = req.matchdict["type"]
    fname = GetQueryFileName(req.GET)
    if t == "peptide":
        try:
            n = req.GET["n"]
            int(n)
        except:
            return HTTPBadRequest_Param("n")
        [scores, results] = PepXML.SearchPeptide(fname + "_" + n, req.GET["peptide"])
        [score, scorename, reverses] = PepXML.DefaultSortColumn(scores)
        results = SortPeptides(results, "score", score, score in reverses)
        count = len(results)
        shown = count
        SearchEngines = {"X-Tandem": 0, "Mascot": 0, "Omssa": 0}
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
        info = {"shown": shown, "total": count, "engine": PepXML.SearchEngineScoreName(scores)}
        return render_to_response(templates + "pepxml_peptide_tooltip.pt", {"info": info, "peptides": results, "counts": SearchEngines.items()}, request=req)
    return HTTPNotFound()


#Provides the configuration to the pyramid or paster web server
def main(*args, **kwargs):
    #check to make sure everything is set up properly
    if not os.path.exists(converted):
        os.makedirs(converted)
    if len(parameters.PROTEIN_DATABASES) > 0:
        if os.path.exists(parameters.HOME + "/bin/blastdbcmd") and os.path.exists(parameters.HOME + "/bin/makeblastdb"):
            print " + Validating protein databases indexes"
            for f in parameters.PROTEIN_DATABASES:
                p = subprocess.Popen([parameters.HOME + "/bin/blastdbcmd", "-db", f, "-info"], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                (out, err) = p.communicate()
                p.stderr.close()
                p.stdout.close()
                if p.wait() != 0:
                    subprocess.call([parameters.HOME + "/bin/makeblastdb", "-in", f, "-parse_seqids", "-dbtype", "prot"])
    Jobs.start()

    session_factory = UnencryptedCookieSessionFactoryConfig(parameters.SECRET_KEY)
    config = Configurator(renderer_globals_factory=RendererGlobals, session_factory=session_factory)
    #Routes: give each URL a name
    config.add_route("index", "/")
    config.add_route("upload", "/init")
    config.add_route("convert", "/init_local")
    config.add_route("convert_url", "/init_url")
    config.add_route("query_init", "/query_init")
    config.add_route("add", "/add")
    config.add_route("merge", "/merge")
    config.add_route("view", "/view")
    config.add_route("results", "/results")
    config.add_route("peptide", "/peptide")
    config.add_route("select", "/select")
    config.add_route("spectrum", "/spectrum")
    config.add_route("lc", "/lc")
    config.add_route("tooltip", "/tooltip/{type}")
    config.add_route("gpmdb_peptide", "/gpmdb_peptide")
    #Views: now associate a function with each route name
    #config.add_view(SearchHit, route_name="search_hit")
    config.add_view(Index, route_name="index")
    config.add_view(Upload, route_name="upload")
    config.add_view(Convert, route_name="convert")
    config.add_view(ConvertUrl, route_name="convert_url")
    config.add_view(QueryInitStatus, route_name="query_init")
    config.add_view(AddFile, route_name="add")
    config.add_view(MergeFile, route_name="merge")
    config.add_view(View, route_name="view")
    config.add_view(ListResults, route_name="results")
    config.add_view(ListPeptide, route_name="peptide")
    config.add_view(SelectInfo, route_name="select")
    config.add_view(Spectrum, route_name="spectrum")
    config.add_view(SpectumLC, route_name="lc")
    config.add_view(Tooltip, route_name="tooltip")
    config.add_view(GPMDB.GetObservationsForPeptide, route_name="gpmdb_peptide", renderer="json")
    #these views provide content which does not change, such as images and javascript
    config.add_static_view("/favicon.ico", parameters.HOME + "/res/favicon.ico", cache_max_age=3600 * 24 * 7)
    config.add_static_view("res", parameters.HOME + "/res", cache_max_age=3600 * 24 * 7)
    config.add_static_view("test", parameters.HOME + "/test", cache_max_age=0)
    return config.make_wsgi_app()
