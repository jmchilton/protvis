#!/bin/bash

allow_install=0
log=setup.log

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
			exit 1
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
		echo -n "installing... " | tee -a $log
		if [ "`which apt-get 2>/dev/null`" ]; then
			super apt-get install --yes $1 >>$log
		elif [ "`which yum 2>/dev/null`" ]; then
			super yum -y install $1 >>$log
		fi
		if [ $? -eq 0 ]; then
			echo "done" | tee -a $log
			return 0
		else
			if [ "$2" ]; then
				super "$2" >>$log
				if [ $? -eq 0 ]; then
					echo "done" | tee -a $log
					return 0
				fi
			fi
			echo "failed" | tee -a $log
			echo "" | tee -a $log
			echo "The following packages are required before running: make python python-setuptools python-virtualenv make gcc g++" | tee -a $log
			return 1
		fi
	else
		echo "can't find a suitable package" | tee -a $log
		echo "" | tee -a $log
		echo "The following packages are required before running: make python python-setuptools python-virtualenv make gcc g++" | tee -a $log
		echo "You can run this script with --auto-install to automatically install packages into your system" | tee -a $log
		return 1
	fi
}

has() {
	if [ $allow_install -ne 0 ]; then
		if [ "`which apt-get 2>/dev/null`" ]; then
			apt-cache show $1 2>/dev/null 1>/dev/null
			if [ $? -eq 0 ]; then
				echo $1
			fi
		elif [ "`which yum 2>/dev/null`" ]; then
			yum list $1 2>/dev/null 1>/dev/null
			if [ $? -eq 0 ]; then
				echo "$1"
			fi
		fi
	fi
}

bin_need() {
	echo -n "Checking for $1: " | tee -a $log
	for b in $@; do
		if [ "`which $b 2>/dev/null`" ]; then
			echo "already installed" | tee -a $log
			return 0
		fi
	done
	if [ $allow_install -ne 0 ]; then
		for b in $@; do
			if [ "`has $b`" ]; then
				get $b
				return $?
			fi
		done
	fi
	echo "can't find a suitable package" | tee -a $log
	echo "" | tee -a $log
	if [ $allow_install -eq 0 ]; then
		echo "You can run this script with --auto-install to automatically install packages into your system" | tee -a $log
	fi
	exit 1
}

py_need() {
	echo -n "Checking for $1: " | tee -a $log
	python -c "import $1" 2>/dev/null >/dev/null
	if [ $? -ne 0 ]; then
		get "python-$1" "$2"
		if [ $? -eq 0 ]; then
			return 0
		fi
		echo "can't find a suitable package" | tee -a $log
		echo "" | tee -a $log
		if [ $allow_install -eq 0 ]; then
			echo "You can run this script with --auto-install to automatically install packages into your system" | tee -a $log
		fi
		exit 1
	else
		echo "already installed" | tee -a $log
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

rm $log 2>/dev/null

bin_need python python27.`uname -i` python26.`uname -i`
bin_need make make.`uname -i`
bin_need gcc | tee -a $log
bin_need g++ gpp gcc-c++.`uname -i`
py_need "setuptools" "dl http://peak.telecommunity.com/dist/ez_setup.py | super python"
py_need "virtualenv" "easy_install virtualenv"

echo -n "Checking for blast+: " | tee -a $log
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
			echo "can't find a suitable package"
			echo ""
			echo "Please visit ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST to download and install blast+ either into `pwd`/bin or a location in PATH" | tee -a $log
			echo "This is an OPTIONAL feature" | tee -a $log
		fi
	else
		echo "unrecognised OS"
		echo ""
		echo "Please visit ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST to download and install blast+ either into `pwd`/bin or a location in PATH" | tee -a $log
		echo "This is an OPTIONAL feature" | tee -a $log
	fi
else
	ln -s `which makeblastdb` bin/makeblastdb 2>/dev/null
	ln -s `which blastdbcmd` bin/blastdbcmd 2>/dev/null
	echo "already installed" | tee -a $log
fi

echo "Building the virtual environment" | tee -a $log
virtualenv --no-site-packages env >>$log
echo "`pwd`" >`env/bin/python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`/protvis.pth

echo "Installing pyramid into the virtual environment" | tee -a $log
cd env
bin/easy_install pyramid >>$log
bin/easy_install PasteScript >>$log
bin/easy_install WebError >>$log
bin/pip install cherrypy >>$log
cd ..

echo "The environment has been set up" | tee -a $log

cd res
rm dojo 2>/dev/null
ln -s dojo_mini dojo
cd ..

echo "Configuring C++ bindings" | tee -a $log
cd C
./configure --auto-install
if [ $? -eq 0 ]; then
	echo "Compiling C++ bindings" | tee -a $log
	make -s
	if [ $? -eq 0 ]; then
		echo ""
		echo "You can now run protvis by typing ./run" | tee -a $log
		exit 0
	fi
fi
echo ""
echo "There was an error while compiling the C bindings." | tee -a $log
echo "You can still run the server without them, but mzML files will not display" | tee -a $log
echo "You can now run protvis by typing ./run" | tee -a $log
exit 1
