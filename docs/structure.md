#File and Directory structure

##Directory: bin
This directory holds all 3rd party tools which are used by the web server.
All tools in this directory can be either a link to a system installed copy of the tool, or the tool itself.
Presently, parts of blast+ are the only 3rd party tools used.
Contents of this directory are created automatically by the setup scripts

##Directory: C
This directory contains the C code that can be compiled to provide extra features and performance enhancements
Compilation of this code is handled automatically by the setup scripts

##Directory: compile
This directory contains the modifications and additions to the dojo library.
These are only required if further modifications are required and dojo needs to be recompiled.
Compiling dojo is handled by the script _dojo_build_ in the main directory

##Directory: ConvertedFiles
This directory contains all of the files which have either been uploaded or viewed from within galaxy, stored in an optimised binary format.
Files will automatically be deleted after 7 days

##Directory: docs
This directory contains documentation relating to use and development of ProtVis

##Directory: env
This directory is created as part of the setup scripts and contains the python virtual environment.
The virtual environment is not nesseccary but ensures that the project will work correctly and seperate from your system python for security

##Directory: res
This directory contains all static resources which can be loaded by the web browser.
This includes layout styles, JavaScript, images and the compiled copy of the dojo library

##Directory: templates
This directory contains all of the HTML template files.
These files are used to build the overall structure of everything displayed in the web browser
These files are in the ZPT format.
Refer to _templates.md_ for detailed information on each template

##Directory: test
This contains testing files for some of the javascript code to assist with development

***

##Script: dojo_build
This script is used to compile the dojo library and additions to it.
It will automatically download the complete code to be used for compiling if not already present in the _compile_ directory
This script only works on unix-based OSs such as Linux or OSX

##Script: run / run.bat
This script is used to start or stop the web server
The server is usually run with the _--daemon_ option provided to run as a service
The default port is 8500, listening on all interfaces

##Script: setup.sh / setup.bat
This script performs all the checks to ensure that the system is setup to run ProtVis, and perform some final configuration.
On systems other than Windows it can also optionally install missing software by providing the _--auto-install_ option

##Script: wsgi.sh
This script generates a default configuration for using the apache web server instead of the built-in web server.
It produces the files _protvis.conf_ and _apache.wsgi_. Instructions are printed detailing how to use the generated _apache.conf_ file.

***

##Configuration: conf.py
This is an optional file that you can create, using _parameters.py_ as a sample.
It provides changes to the default configuration of the server, such as where galaxy can be found (if used), and what built-in protein databases are avaliable (if any).

##Configuration: production.ini.sample
This provides a template for the default configuration for when the server is run as a WSGI module in either apache or nginx.
If there is no _production.ini_ present when configuring these servers it file will be it will be produced by copying _production.ini.sample_.
The default configuration should be correct in most cases.

***

##Code: Common.py
This file contains code which is common to several modules, including the XML parser and encoding/decoding functions

##Code: FileTypes.py
This file contins code which is used to search for and load the best modules avalible for each file type.
It will attempt to load a compiled copy of the library if present, otherwise fall back to a python copy. If neither of these load successfully then the modue is disabled and the server can be used without the functionality provided by the module.

##Code: MGF.py
This is the python implementation of the MGF file type.
It provides both searching and converting to binary functionality

##Code: parameters.py
This file provides the default configuration of the server as well as loading of user defined settings.
No settings should be changed in this file, instead a new file, _conf.py_, should be created and define any variables which need to be changed with the same name as in this file.

##Code: PepXML.py
This is the python implementation of the pepXML file type.
It provides both searching and converting to binary functionality

##Code: protvis.py
This file provides the main server code which is responsible for handling the web requests and replying with data. It handles everything, including what each file should contain, however the method of storing such data is handled by seperate modules.

##Code: ProtXML.py
This is the python implementation of the protXML file type.
It provides both searching and converting to binary functionality

##Code: Reference.py
This file provides code used to find all the links between each of the file types.

##Code: Server.py
This file provides wrapper code to allow the server to be run as an application for debugging.
The debug application prints debug information of HTTP requests to the screen.
