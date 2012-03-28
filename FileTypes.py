import sys
import MGF, PepXML, ProtXML #import python only modules

class Compiled:
	def __init__(self, name, version):
		self.name = name
		self.version = version
		
Compiled = [ Compiled("MzML", 0.8) ] #import C/python modules


module = sys.modules[__name__]
for mod in Compiled:
	try:
		m = __import__(mod.name)
		if m.version() != mod.version:
			print " * The compiled " + mod.name + " module is the incorrect version. Expecting " + str(mod.version) + ", received " + str(m.version()) + ". You should recompile it with"
			print "   cd C; make clean -s; make -s; cd .."
			try:
				m = __import__("Py" + mod.name)
				print " + " + mod.name + " is running the slower python code"
			except:
				print " + " + mod.name + " module has been disabled"
				m = None
	except:
		print " * Compiled version of " + mod.name + " could not be found."
		try:
			m = __import__("Py" + mod.name)
			print " + " + mod.name + " is running the slower python code"
		except:
			print " + " + mod.name + " module has been disabled"
			m = None
	setattr(module, mod.name, m)
