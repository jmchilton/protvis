"""
Proteomics Analysis defaults configuration file

If you need to make any changes you should create a new file "conf.py" and set the modified values in there
You only need to specify the parameters which you change
"""

#Root directory of your galaxy install.
#Typically /var/www/galaxy
GALAXY_ROOT = "/var/www/galaxy"

#Any directories that the remote user is allowed to read from.
#This would be any directories where useful files such as protien databases would lie
#If using with galaxy, you should also include GALAXY_ROOT+"/database/files/"
PATH_WHITELIST = [GALAXY_ROOT + "/database/files/", "/tmp"]

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

import os
HOME = os.path.realpath(os.path.dirname(__file__))

#Location of cached files
CONVERTED_FILES = HOME + "/ConvertedFiles/"


### There are no options beyond this point ###
import subprocess

#Import user-defined settings
try:
    from conf import *
except:
    print " * No user supplied options. You may want to make a conf.py file. Look at parameters.py for options"

#Check settings for porential issues
if len(PROTEIN_DATABASES) == 0:
    print " * No protein databases specified. Users will not be able to view the coverage graph."

try:
    subprocess.call([HOME + "/bin/blastdbcmd", "-h"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    subprocess.call([HOME + "/bin/makeblastdb", "-h"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
except:
    print " * blast+ cannot be found or is not working correctly. Users will not be able to view the coverage graph."

if GALAXY_ROOT != "" and not os.path.exists(GALAXY_ROOT + "/database"):
    print " * Galaxy could not be found or accessed at " + GALAXY_ROOT + ". Galaxy integration will not work."
