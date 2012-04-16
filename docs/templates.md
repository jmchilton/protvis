#Template files

Templates are used to provide the structure of the final webpage, in HTML, but provide extra functions such as loops to embed dynamic data
These templates use the ZPT format

##dataview.pt
This is the base webpage which will have all results embedded into it
It contains mostly only JavaScript helpers to load the results

##index.pt
This is displayed as the first page the user will see if not using galaxy
This is the homepage, which presents a breif description of the project and a form to upload data

##mgf_results.pt
This is displayed when a user clicks on an MFG file
This is the main results page of the list of all results from an MFG file
It is a simple list presenting the spectrum names

##missing_results.pt
This is displayed when a user clicks on a file which has no contents
This presents a form for uploading the contents of a file which was missing when the data was first processed upon upload

##mzml_display.pt
This is dispalyed when a user clicks on an mzML file
It displays an LC view of all MS1 and MS2 data

##pep_results.pt
This is displayed when a user clicks on a pepXML file
It displays a list of all peptides found, along with the protein and score

##pepxml_peptide.pt
This is displayed when a user clicks on a peptide
It displays a list of all spectrums where the selected peptide
This is only responsible for the bottom list, _pepxml_peptide_spectrums_ is responsible for the top statistics list

##pepxml_peptide_spectrums.pt
This is displayed when a user clicks on a peptide
It displays a summary list of the datasets were the selected peptide was found
This is only responsible for the top list, _pepxml_peptide.pt_ is responsible for the main list at the bottom

##pepxml_peptide_tooltip.pt
This file is displayed when a user hovers over a peptide
It displays a list of the top spectrums where the peptide was found, and some statistics

##prot_results.pt
This is displayed when a user clicks on a protXML file
This is the main results page of the list of all results from a protXML file

##select_indistinguishable_protein.pt
This is displayed when a user clicks on the green __+X__ number next to a protein name where avaliable
It shows a of all proteins which could not be distinguished from the selected, shown in a popup box

##select_protein.pt
This is displayed when a user clicks the __X more__ link next to a peptide in the list of proteins
It displays the list of all peptides in the proteins, as well as a coverage graph when the data is avaliable

##select_scores.pt
This is displayed when a user clicks the score in the list of peptides
It shows a list of all avaliable scores for the peptide, shown in a popup box

##specview.pt
This is displayed when a user clicks on a spectrum name
It displays the interactive spectrum viewer for the selected spectrum

##upload.pt
This is displayed when the user clicks a display link from within galaxy
It shows the progress of the data processing
