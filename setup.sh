#!/bin/bash

allow_install=0

usage() {
	cat <<%%%
Usage: ./setup.sh [OPTIONS]

Where [OPTIONS] can be any combination of:
  --auto-install   Automatically download and install missing packages into
                   your package manager.
                   This option only affects system packages. Some packages
                   will still be downloaded and installed into the local
                   directory
%%%
}

for arg in $@; do
	case $arg in
		--auto-install)
			allow_install=1
			;;
		--help)
			usage
			exit 0
			;;
		*)
			echo "Unrecognised argument $arg"
			usage
			exit 0
			;;
	esac
done

super() {
	if [ "`which sudo 2>/dev/null`" ]; then
		sudo -E $@
	elif [ "`which su 2>/dev/null`" ]; then
		su -c "$@" `whoami`
	elif [ "`which pfexec 2>/dev/null`" ]; then
		pfexec $@
	else
		$@
	fi
	return $?
}

get() {
	if [ $allow_install -ne 0 ]; then
		echo "$1 is not installed. Installing it now."
		if [ "`which apt-get 2>/dev/null`" ]; then
			super apt-get install --yes $1
		elif [ "`which yum 2>/dev/null`" ]; then
			super yum -y install $1
		fi
		if [ $? -eq 0 ]; then
			return 0
		else
			if [ "$2" ]; then
				super "$2"
				return $?
			else
				echo "Failed to install $1."
				echo "The following packages are required before running: make python python-setuptools python-virtualenv make gcc g++"
				exit
			fi
		fi
	else
		echo "$1 could not be located"
		echo "The following packages are required before running: make python python-setuptools python-virtualenv make gcc g++"
		echo "You can run this script with --auto-install to automatically install packages into your system"
		exit
	fi
}

has() {
	if [ $allow_install -ne 0 ]; then
		if [ "`which apt-get 2>/dev/null`" ]; then
			if [ "`apt-cache search $1 | grep "^$1[ \t]"`" ]; then
				echo $1
			fi
		elif [ "`which yum 2>/dev/null`" ]; then
			if [ "`yum list | grep "^$1[ \t]"`" ]; then
				echo "$1"
			fi
		fi
	fi
}

bin_need() {
	echo "Checking for $1"
	for b in $@; do
		if [ ! "`which $b 2>/dev/null`" ]; then
			echo "$b is already installed"
			return 0
		fi
	done
	for b in $@; do
		if [ "`has $b`" ]; then
			get $b
			return $?
		fi
	done
	echo 
	return 1
}

py_need() {
	echo "Checking for $1 package"
	python -c "import $1" 2>/dev/null >/dev/null
	if [ $? -ne 0 ]; then
		get "python-$1" "$2"
		return $?
	else
		echo "$1 is already installed"
		return 0
	fi
}

dl() {
	if [ "`which curl 2>/dev/null`" ]; then
		curl $1
	elif [ "`which wget 2>/dev/null`" ]; then
		wget $1 -O-
	else
		python -c "import urllib, sys; s=urllib.urlopen('$1').read(); sys.stdout.write(s); exit(len(s) == 0)"
	fi
}

bin_need python
bin_need make
bin_need gcc
bin_need g++ gpp gcc-c++.`uname -i`
py_need "setuptools" "dl http://peak.telecommunity.com/dist/ez_setup.py | super python"
py_need "virtualenv" "easy_install virtualenv"

echo "Checking for blast+"
mkdir bin 2>/dev/null
PATH=$PATH:./bin/
if [ "`which makeblastdb 2>/dev/null`" == "" ] || [ "`which blastdbcmd 2>/dev/null`" == "" ]; then
	if [ "`uname`" == "Linux" ]; then
		if [ "`uname -p`" == "x86_64" ]; then
			arch="x64"
		else
			arch="ia32"
		fi
		ver=2.2.25
		dl ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/$ver/ncbi-blast-$ver+-$arch-linux.tar.gz > ncbi-blast-$ver+-$arch-linux.tar.gz
		if [ $? -eq 0 ]; then
			tar xf ncbi-blast-$ver+-$arch-linux.tar.gz
			rm ncbi-blast-$ver+-$arch-linux.tar.gz 2>/dev/null
			mv ncbi-blast-$ver+/bin/makeblastdb ncbi-blast-$ver+/bin/blastdbcmd bin/
			rm -rf ncbi-blast-$ver+ 2>/dev/null
		else
			echo "Could not locate or get blast+. Please visit ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST to download and install blast+ either into `pwd`/bin or a location in PATH"
			echo "This is an OPTIONAL feature"
		fi
	else
		echo "Unrecognised OS. Please visit ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST to download and install blast+ either into `pwd`/bin or a location in PATH"
		echo "This is an OPTIONAL feature"
	fi
else
	ln -s `which makeblastdb` bin/makeblastdb 2>/dev/null
	ln -s `which blastdbcmd` bin/blastdbcmd 2>/dev/null
	echo "blast+ is already installed"
fi

echo "Building the virtual environment"
virtualenv --no-site-packages env
echo "`pwd`" >`env/bin/python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`/protvis.pth

echo "Installing pyramid into the virtual environment"
echo "This could take a while"
cd env
bin/easy_install pyramid
bin/easy_install PasteScript
bin/easy_install WebError
bin/pip install cherrypy
cd ..

echo "The environment has been set up"

cd res
rm dojo 2>/dev/null
ln -s dojo_mini dojo
cd ..

echo "Compiling C++ bindings"
cd C
./configure --auto-install
if [ $? -eq 0 ]; then
	make -s
	if [ $? -eq 0 ]; then
		echo "You can now run protvis by typing ./run"
		exit 0
	fi
fi
echo "There was an error while compiling the C bindings."
echo "You can still run the server without them, but mzML files will not display"
echo "You can now run protvis by typing ./run"
