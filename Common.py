import struct
import xml.sax
import xml.parsers.expat
from xml.sax.saxutils import unescape
from cStringIO import StringIO
import sys
from pyramid.httpexceptions import *

#Util functions
def TRACE(*args):
	message = "".join([str(i) for i in args])
	print(message)
	return

def TRACEPOS(*args):
	#TRACE(*args)
	return

def TRACEPOSXML(stream, *args):
	"""if type(stream) is type(StringIO()):
		args += (str(stream.tell()), " (StringIO)")
	else:
		args += (str(stream.tell()),)
	TRACE(*args)"""
	return

def TryGetAttrib(elem, attr):
	try:
		return elem.attrib[attr]
	except:
		return None

def YNBit(value, mask):
	if value.upper() == "Y":
		return mask
	return 0

def TryGet(dic, elem):
	try:
		return dic[elem]
	except:
		return None

def EncodeOptional(*attrs):
	Flags = 0
	Bit = 1
	for attr in attrs:
		if attr != None:
			Flags |= Bit
		Bit <<= 1
	return Flags

def EncodeStringToFile(f, s):
	l = len(s)
	f.write(struct.pack("=H{0}s".format(l), l, str(s)))

def EncodeStringToFileUnescape(f, s):
	l = len(s)
	f.write(struct.pack("=H{0}s".format(l), l, unescape(str(s))))

def EncodeString(f, s):
	l = len(s)
	return struct.pack("=H{0}s".format(l), l, str(s))

def DecodeStringFromFile(f):
	l = struct.unpack("=H", f.read(2))[0]
	return struct.unpack("={0}s".format(l), f.read(l))[0]

def EatStringFromFile(f):
	l = struct.unpack("=H", f.read(2))[0]
	return f.seek(l, 1)

class SearchStatus:
	def __init__(self, dic):
		self.Terms = dic
		self.Matched = {}
		self.Results = []
		self.Total = 0
		
	def copy(self):
		dic = {}
		for k in self.Terms:
			dic[k] = [i for i in self.Terms[k]]
		new = SearchStatus(dic)
		dic = {}
		for k in self.Matched:
			dic[k] = [i for i in self.Matched[k]]
		new.Matched = dic
		new.Results = self.Results
		return new

	def IsMatched(self):
		return len(self.Terms) == 0

	def _SearchItem(self, name, value, comparator):
		#returns:
		# -1 if this key is not required for searhing
		#  0 if this key was searched against the basic or specific search, but did not completly match either
		#  1 if matched either the basic or specific search
		phrases = None
		key = name
		try:
			phrases = self.Terms[name]
		except:
			try:
				phrases = self.Terms[None]
				key = None
			except:
				return -1
		i = 0
		count = len(phrases)
		while i < count:
			if comparator(value, phrases[i]) != 0:
				try:
					self.Matched[key].append(phrases[i])
				except:
					self.Matched[key] = [phrases[i]]
				del phrases[i]
				count -= 1
			else:
				i += 1
		if count == 0:
			del self.Terms[key]
			return 1
		return 0

	def SearchItemInt(self, name, value):
		def CmpInt(val, s):
			try:
				if val == int(s):
					return 1
				else:
					return 0
			except:
				return 0
		return self._SearchItem(name, value, CmpInt)

	def SearchItemFloat(self, name, value):
		def Precision(s):
			l = s.split(".")
			if len(l) == 1:
				l = s.split("e")
				if len(l) > 1:
					return -int(l[1])
				else:
					return 0;
			l = l[1].split("e")
			if len(l) > 1:
				[frac, exp] = l
				return len(frac) - int(exp) #works for + and - exp's
			else:
				return len(l[0])

		def CmpFloat(val, s):
			try:
				f = float(s)
				prec = Precision(s)
				if abs(val - f) < pow(10, -prec):
					return 1
				else:
					return 0
			except:
				return 0

		return self._SearchItem(name, value, CmpFloat)
	
	def SearchItemString(self, name, value):
		def CmpString(val, s):
			try:
				if val.upper().find(s) >= 0:
					return 1
				return 0
			except:
				return 0
		return self._SearchItem(name, value, CmpString)

def SplitPhrase(phrase):
	return phrase.split(); #FIXME: don't split quotes

def EncodeTermsBasic(terms):
	return { None: SplitPhrase(terms.upper()) }

def EncodeTermsAdvanced(terms_dict):
	terms = {}
	for k, v in terms_dict.items():
		terms[k] = SplitPhrase(v.upper())

#XML Helpers
class NullStream:
	def tell(self):
		return 0

	def write(self, bytes):
		#do nothing
		return

	def seek(self, offset, origin = 0):
		return

	def __setitem__(self, name, val):
		return

class TagHandler(object):
	def __new__(cls, stream, *args, **kwargs):
		obj = object.__new__(cls, *args, **kwargs)
		obj.Stream = stream
		return obj

	def End(self):
		return

	def BeginChild(self, name):
		raise NotImplementedError(name)

	def EndChild(self):
		return self.Stream

class Eater:
	def End(self):
		return

	def BeginChild(self, name):
		return NullStream()

	def EndChild(self):
		return

class SaxHandlerBase(xml.sax.ContentHandler):
	def __init__(self, stream, stat):
		self.Stream = stream
		self.Stat = stat
		self.State = []
		#self.Handlers = {} #This must be defined in the child class
		
	def startElement(self, name, attrs):
		#try:
			if len(self.State) > 0:
				stream = self.State[-1].BeginChild(name)
			else:
				stream = self.Stream
			self.State.append(self.Handlers[name](stream, self.Stat, attrs))
		#except:
		#	print("Ignoring unknown element '" + name + "'")
		#	self.State.append(Eater())

	def endElement(self, name):
		stream = self.State.pop().End()
		#State[-1].EndChild(stream) #Not used

#General
class Literal(object):
    def __init__(self, s):
        self.s = s

    def __html__(self):
        return self.s

def test(cond, t, f):
	if cond == True:
		return t
	return f

#Extended HTTP Errors
class HTTPBadRequest_Param(HTTPBadRequest):
	def __init__(self, param, **kw):
		HTTPBadRequest.__init__(self, explanation=Literal("The parameter <i>" + param + "</i> is required to view this page, and was not supplied or has an invalid value.<br><br>Make sure you entered the URL correctly."), **kw)

class HTTPNotFound_Data(HTTPNotFound):
	def __init__(self, param, **kw):
		HTTPNotFound.__init__(self, explanation=Literal("The dataset <i>" + param + "</i> could not be found.<br><br>It may have been deleted from the server to free some space.<br>Make sure you entered the URL correctly, or upload your data to the server again."), **kw)
