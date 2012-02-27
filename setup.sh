#!/bin/bash

super() {
	if [ "`which sudo` 2>/dev/null" != "" ]; then
		sudo $@
	elif [ "`which su` 2>/dev/null" != "" ]; then
		su -c "$@" `whoami`
	else
		$@
	fi
}

get() {
	if [ "`which apt-get` 2>/dev/null" != "" ]; then
		super "apt-get install $1"
	elif [ "`which yum` 2>/dev/null" != "" ]; then
		super "yum install $1"
	else
		if [ "$2" = "" ]; then 
			echo "Failed to install $1."
			echo "The following packages are required before running: make python python-setuptools python-virtualenv"
			echo "Exiting."
			exit
		else
			super "$2"
		fi
	fi
}

bin_need() {
	echo "Checking for $1"
	if [ "`which $1` 2>/dev/null" = "" ]; then
		echo "$1 is not installed. Installing it now."
		get $1
	else
		echo "$1 is already installed"
	fi
}

py_need() {
	echo "Checking for $1 package"
	python 2>&1 1>/dev/null <<%%%
import $1
%%%
	if [ $? -eq 1 ]; then
		echo "$1 is not installed. Installing it now."
		get "$1" "$2"
	else
		echo "$1 is already installed"
	fi
}

bin_need python
bin_need make
py_need "setuptools" "wget http://peak.telecommunity.com/dist/ez_setup.py -O- | super python"
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
		wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.2.25/ncbi-blast-2.2.25+-$arch-linux.tar.gz
		tar xf ncbi-blast-2.2.25+-$arch-linux.tar.gz
		rm ncbi-blast-2.2.25+-$arch-linux.tar.gz
		mv ncbi-blast-2.2.25+/bin/makeblastdb ncbi-blast-2.2.25+/bin/blastdbcmd bin/
		rm -rf ncbi-blast-2.2.25+
	else
		echo "Unrecognised OS. Please visit ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST to download and install blast+ either into `pwd`/bin or a location in PATH"
	fi
else
	ln -s `which makeblastdb` bin/makeblastdb
	ln -s `which blastdbcmd` bin/blastdbcmd
	echo "blast+ is already installed"
fi

echo "Building the virtual environment"
virtualenv --no-site-packages env

echo "Installing pyramid into the virtual environment"
echo "This could take a while"
cd env
bin/easy_install pyramid

echo "The environment has been set up"

cd ../res
rm dojo 2>/dev/null
ln -s dojo_mini dojo
cd ..

echo "Compiling C++ bindings"
cd ../C
make -s
cd ..

echo "You can now run the program by typing ./run"
