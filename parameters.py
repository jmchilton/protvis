"""
Proteomics Analysis defaults configuration file

If you need to make any changes you should create a new file "conf.py" and set the modified values in there
You only need to specify the parameters which you change
"""


#Listening address of server.
#Typically "0.0.0.0"
HOST = "0.0.0.0"

#Listening port of server.
#Typically 80
PORT = 80

#Root directory of your galaxy install.
#Typically /var/www/galaxy
GALAXY_ROOT = "/var/www/galaxy"

#Regex to match against your decoys.
#Only used for changing display colours.
DECOY_REGEX = "^decoy_.*"

#Regex to determine if 2 spectrums are the same.
#This is only used for statistics in the peptide view.
SPECTRUM_REGEX = r"(.+?)(\.mzML)?\.[0-9]+\.[0-9]+\.[0-9]+"

#A list of .fasta files which contain the sequences for all the proteins
#These databases will be indexed with blast+
#For performance you should place the most likely database to match a protein first
PROTEIN_DATABASES = []

### There are no options beyond this point ###
#Import user-defined settings
try:
	from conf import *
except:
	print " * No user supplied options. You may want to make a conf.py file. Look at parameters.py for options"

#Check settings for porential issues
import subprocess

if len(PROTEIN_DATABASES) == 0:
	print " * No protein databases specified. Users will not be able to view the coverage graph."

try:
	f = open("/dev/null")
	subprocess.call(["bin/blastdbcmd", "-h"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
	subprocess.call(["bin/makeblastdb", "-h"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
except:
	print " * blast+ cannot be found or is not working correctly. Users will not be able to view the coverage graph."