import json
import urllib2
import urllib
from pyramid.response import Response
from Common import HTTPBadRequest_Param
from pyramid.httpexceptions import HTTPNotFound


def uniprot_map_protein_id(from_type, to_type, protein_id):
    mapping_url = 'http://www.uniprot.org/mapping/'
    params = {
    'from': 'ID',
    'to': 'ENSEMBL_PRO_ID',
    'format': 'list',
    'query': protein_id,
    }

    data = urllib.urlencode(params)
    request = urllib2.Request(mapping_url, data)
    response = urllib2.urlopen(request)
    response_string = response.read(200000)
    id_list = str(response_string).split()
    return id_list


def proteins_for_peptide_sequence(seq):
    urlrequest = urllib2.urlopen("http://gpmdb.thegpm.org/1/peptide/accessions/seq=%s" % seq)
    return json.loads(urlrequest.read())


def total_peptide_count(pep_seq):
    urlrequest = urllib2.urlopen("http://gpmdb.thegpm.org/1/peptide/count/seq=%s" % pep_seq)
    return json.loads(urlrequest.read())


def peptide_counts_for_protein(prot_acc, pep_seq):
    urlrequest = urllib2.urlopen("http://gpmdb.thegpm.org/1/protein/peptide_count/acc=%s&seq=%s" % (prot_acc, pep_seq))
    return json.loads(urlrequest.read())


def total_peptide_counts_for_protein(prot_acc):
    urlrequest = urllib2.urlopen("http://gpmdb.thegpm.org/1/protein/peptides_z/acc=%s" % prot_acc)
    return json.loads(urlrequest.read())


def info_for_protein(prot_acc):
    urlrequest = urllib2.urlopen("http://gpmdb.thegpm.org/1/protein/description/acc=%s" % prot_acc)
    return json.loads(urlrequest.read())


def detailed_counts_for_peptide(peptide_seq):
    # Get all protein accessions for a peptide
    # Then go through for each protein and get the relative frequency with which that peptide
    prots = proteins_for_peptide_sequence(peptide_seq)

    output = {}
    for protein in prots.keys():
        counts = peptide_counts_for_protein(str(protein), peptide_seq)
        totals = total_peptide_counts_for_protein(str(protein))
        info = info_for_protein(str(protein))
        output[str(protein)] = {'counts': counts, 'info': info, 'accession': str(protein), 'totals': totals}

    return output


#HTTP: Get all proteins observed for a peptide and then for each protein, get its relative frequency of occurrence in that protein
# This is done using the gpmdb REST api and returns a json formatted result
#The full API is described here http://wiki.thegpm.org/wiki/GPMDB_REST
def GetObservationsForPeptide(req):
    try:
        peptide_seq = req.GET["peptideseq"]
    except:
        return HTTPBadRequest_Param("peptideseq")

    pep_count = total_peptide_count(peptide_seq)
    if len(pep_count) == 0:
        return HTTPNotFound()

    return Response(str(pep_count[0]))
