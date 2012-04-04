# Proteomics Visualise (ProtVis)

***

## What is it?

Proteomics visualise is a web based tool for visualising and navigating data from a proteomics workflow with any modern web browser.

It supports Protein Prophet, Interprophet, Peptide Prophet, Search Engines (tested with Mascot, X! Tandem and Omssa), and mzML raw spectrums.

ProtVis works as a standalone tool where files can be uploaded, or integrated directly into galaxy with the galaxy-proteomics.

![Screenshot of ProtVis](https://bitbucket.org/Andrew_Brock/proteomics-visualise/raw/97b43cab8533/docs/coverage.png "ProtVis protein and coverage view")

***

## Quick installation

Either [download](https://bitbucket.org/Andrew_Brock/proteomics-visualise/downloads) a copy of the code

OR

Access the code through Mercurial

On Debian/Ubuntu:

    sudo apt-get install mercurial

On Red Hat/CentOS: You may need to append your platform on the end of the name

    sudo yum install mercurial  #Possibly  mercurial.i386  OR  mercurial.x86_64

On SuSE:

	sudo zypper install mercurial

Once you have mercurial, you can clone the repositories and run them.
Copy and paste one of the following script into the shell on a unix/linux or OSX computer in a directory where you have write permission.

Running without galaxy:

    #If using mercurial
    hg clone https://bitbucket.org/Andrew_Brock/proteomics-visualise
    
    #OR if using download
    curl https://bitbucket.org/Andrew_Brock/proteomics-visualise/get/tip.tar.gz -o proteomics-visualise.tar.gz
    tar xf proteomics-visualise.tar.gz
    
    #now setup and run
    cd proteomics-visualise
    ./setup.sh --auto-install
    ./run --daemon
    
Running with galaxy:

    #If using mercurial
    hg clone https://bitbucket.org/iracooke/protk
    hg clone https://bitbucket.org/iracooke/galaxy-proteomics
    hg clone https://bitbucket.org/Andrew_Brock/proteomics-visualise
    
    #OR if using download
    curl https://bitbucket.org/iracooke/protk/get/tip.tar.gz -o protk.tar.gz
    curl https://bitbucket.org/iracooke/galaxy-proteomics/get/tip.tar.gz -o galaxy-proteomics.tar.gz
    curl https://bitbucket.org/Andrew_Brock/proteomics-visualise/get/tip.tar.gz -o proteomics-visualise.tar.gz
    tar xf protk.tar.gz
    tar xf galaxy-proteomics.tar.gz
    tar xf proteomics-visualise.tar.gz

    #now setup and run
    cd protk
    ./setup.sh
    cd ../galaxy-proteomics
    ./run.sh --daemon
    cd ../
    cat >proteomics-visualise/conf.py <<%%%
    GALAXY_ROOT = "`pwd`/galaxy-proteomics"
    PATH_WHITELIST = [GALAXY_ROOT + "/database/files/"]
    %%%
    cd proteomics-visualise
    ./setup.sh --auto-install
    ./run --daemon

You can now connect to the ProtVis server on [http://127.0.0.1:8500](http://127.0.0.1:8500) and the Galaxy server (if installed) on [http://127.0.0.1:8080](http://127.0.0.1:8080)

***

## Full installation

See INSTALLING for a more detailed set of instructions.

Installation is as easy as running the `setup.sh` script.
If you have administrative access and want the script to atuomaically download the required tools into your system with the package manager, you can supply the `--auto-install` option to the setup script
`./setup.sh` OR `./setup.sh --auto-install`

Regardless of the `--auto-install` option, some packages will still be downloaded and installed into the local directory away from your system configuration.

The server can still run with limited functionality even if some packages failed to download or install.

***

## Configuring

Configurations are provided in the `conf.py` file.
This file needs to be created by taking relavant options from `parameters.py`. Any values not set in `conf.py` will get the default value from `parameters.py`

The listening address and server port are provided as run-time options to the `run` script with `--address=` and `--port=`.

### Configuring default protein databases [OPTIONAL]

You can provide default locations to for protein databases for when the database used by the user is not avaliable.
These databases will be indexed by blast+ if they are not already.
This is a comma seperated list of full paths to the .fasta file.

    PROTEIN_DATABASES = ["/path/to/db1.fasta", "/path/to/db2.fasta"]

### Configuring the whitelist of paths [OPTIONAL]

ProtVis can read files directly off the server based on a filename provided in either the URL or in the contents of a file.
By default the user cannot access files stored on the server. By adding paths into the whitelist you allow Protvis to read the contents of any file in the director, or a specific file.
Any additional protien databases, and the Galaxy datasets, if using Galaxy, should be in this path.

    PATH_WHITELIST = ["/path/to/readable/files", GALAXY_ROOT + "/database/files/"]

***

## Running the web server

The server should be run as a daemon (background service) for normal use.

    ./run --daemon

It is possible to run the server as a module of either Apache or nginx. See Section 3 of INSTALLING for details on configuration.

To stop the running daemon server use

    ./run --stop-daemon

***

## Accessing the web interface

To connect to a default configuration of ProtVis navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.

If you started the server with `--address=A.B.C.D --port=E` you can navigate to `http://A.B.C.D:E`, or if `--port=80` you only need the address `http://A.B.C.D`.
__Note: You may need root (sudo) permission to run the server on a ports 1-1024.__

Once you have connected you can upload files for viewing with the form on the right.

***

## Integrating with Galaxy

Download a copy of [galaxy-proteomics](https://bitbucket.org/iracooke/protk/overview)
Run galaxy from the galaxy-proteomics directory with

    ./run.sh --daemon

If your galaxy is installed into a location other than `/var/www/galaxy` you need to provide a `conf.py` file in the ProtVis directory with the lines:

    GALAXY_ROOT = "/full/path/to/galaxy"
    PATH_WHITELIST = [GALAXY_ROOT + "/database/files/"]
    

Now you can run ProtVis from the proteomics-visualise directory with
The server URL for the galaxy integration is presently hard-coded to port 8500 in galaxy/display_applications/proteomics/*.xml

    ./run --daemon --port=8500

Now when you upload or process proteomics data with galaxy a link should appear in the green history boxes for viewing the data with ProtVis

***

##Using ProtVis
A graph of all files used in the analysis can be found at the top of the page.
![Data flow graph](https://bitbucket.org/Andrew_Brock/proteomics-visualise/raw/97b43cab8533/docs/files.png "Data flow graph")
You can quickly navigate between each of the stages in your data analysis by clicking on any of the blocks in this graph.
