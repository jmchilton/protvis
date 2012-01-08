"""
Proteomics Analysis main configuration file
"""

#Listening address of server.
#Typuically "0.0.0.0"
HOST = "127.0.0.1"

#Listening port of server.
#Typically 80
PORT = 8000

#Root directory of your galaxy install.
#Typically /var/www/galaxy
GALAXY_ROOT = "/home/andrew/Desktop/hg/galaxy-proteomics"

#Regex to match against your decoys.
#Only used for changing display colours.
DECOY_REGEX = "^decoy_.*"

#Regex to determine if 2 spectrums are the same.
#This is only used for statistics in the peptide view.
SPECTRUM_REGEX = r"(.+?)(\.mzML)?\.[0-9]+\.[0-9]+\.[0-9]+"
