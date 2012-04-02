#!/bin/bash

allow_install=0
compile=1

log=setup.log

usage() {
	cat <<%%%
Usage: ./setup.sh [OPTIONS]

Where [OPTIONS] can be any combination of:
  --no-compile      Dont compile the C bindings
                    This will make mzml files unavaliable and will reduce
                    performance in other files

  --auto-install=X  Automatically download and install missing requirements
                    X=all
                       Installs any missing dependancies. This includes
                       installing into your systems package manager
                       May require root access
                       Equivelent to just --auto-install
                    X=local
                       Only download and install packages that will be used
                       locally, and have no impact on the system configuration
                    X=none
                       Dont download or install anything.
                       Default when --auto-install is not provided
%%%
}

for arg in $@; do
	case $arg in
		--no-compile)
			compile=0
			;;
		--auto-install)
			allow_install=2
			;;
		--auto-install=*)
			case `echo "$arg" | cut -b 16-` in
				all)
					allow_install=2
					;;
				local)
					allow_install=1
					;;
				none)
					allow_install=0
					;;
				*)
					echo "Unrecognised argument $arg"
					usage
					exit 1
					;;
			esac
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
	if [ `id -u` -eq 0 ]; then
		$@
	elif [ "`which sudo 2>/dev/null`" ]; then
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
	if [ $allow_install -ge 2 ]; then
		echo -n "installing... " | tee -a $log
		_tried=1
		if [ "`which apt-get 2>/dev/null`" ]; then
			super apt-get install --yes $1 2>>$log >>$log
		elif [ "`which yum 2>/dev/null`" ]; then
			super yum -y install $1 2>>$log >>$log
		elif [ "`which zypper 2>/dev/null`" ]; then
			super zypper -n install $1 2>>$log >>$log
		else
			_tried=0
		fi
		if [ $_tried -ne 0 ] && [ $? -eq 0 ]; then
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
			echo "The following packages are required before running: python python-setuptools python-virtualenv make gcc g++" | tee -a $log
			return 1
		fi
	else
		echo "can't find a suitable package" | tee -a $log
		echo "" | tee -a $log
		echo "The following packages are required before running: python python-setuptools python-virtualenv make gcc g++" | tee -a $log
		echo "You can run this script with --auto-install to automatically install packages into your system" | tee -a $log
		return 1
	fi
}

has() {
	if [ $allow_install -ge 2 ]; then
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
		elif [ "`which zypper 2>/dev/null`" ]; then
			if [ ! "`zypper info $1 | grep "package '[^']*' not found"`" ]; then
				echo "$1"
			fi
		fi
	fi
}

bin_need() {
	echo -n "Checking for $1: " | tee -a $log
	for b in $@; do
		if [ "`which $b 2>/dev/null | tee -a $log`" ]; then
			echo "already installed" | tee -a $log
			return 0
		fi
	done
	if [ $allow_install -ge 2 ]; then
		for b in $@; do
			echo "Trying $b" >> $log
			if [ "`has $b`" ]; then
				get $b
				return $?
			fi
		done
	fi
	echo "can't find a suitable package" | tee -a $log
	echo "" | tee -a $log
	if [ $allow_install -ge 2 ]; then
		echo "You need to manually install $1 then re-run this script"
	else
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
		if [ $allow_install -ge 2 ]; then
			echo "You can run this script with --auto-install to automatically install packages into your system" | tee -a $log
		else
			echo "You need to manually install $1 then re-run this script"
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

bin_need python python27.`uname -m` python26.`uname -m`
bin_need make make.`uname -m`
bin_need gcc
bin_need g++ gxx gcc-c++ gcc-c++.`uname -m`
py_need "setuptools" "dl http://peak.telecommunity.com/dist/ez_setup.py | super python"
py_need "virtualenv" "easy_install virtualenv"

echo -n "Checking for blast+: " | tee -a $log
mkdir bin 2>/dev/null
PATH=$PATH:./bin/
if [ "`which makeblastdb 2>/dev/null`" == "" ] || [ "`which blastdbcmd 2>/dev/null`" == "" ]; then
	_blast="no"
	if [ "`uname`" == "Linux" ]; then
		_blast="yes"
		echo "installing" | tee -a $log
		if [ "`uname -m`" = "x86_64" ]; then
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
			echo "can't find a suitable package" | tee -a $log
		fi
	elif [ "`uname`" == "Darwin" ]; then
		echo "installing" | tee -a $log
		ver=2.2.25
		dl ftp://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/$ver/ncbi-blast-$ver+.dmg > ncbi-blast-$ver+-$arch-linux.tar.gz
		if [ $? -eq 0 ]; then
			_blast="yes"
			tar xf ncbi-blast-$ver+-$arch-linux.tar.gz
			rm ncbi-blast-$ver+-$arch-linux.tar.gz 2>/dev/null
			mv ncbi-blast-$ver+/bin/makeblastdb ncbi-blast-$ver+/bin/blastdbcmd bin/
			rm -rf ncbi-blast-$ver+ 2>/dev/null
		else
			echo "can't find a suitable package" | tee -a $log
		fi
	else
		echo "unrecognised OS" | tee -a $log
	fi
	if [ $_blast = "no" ]; then
		echo "" | tee -a $log
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

if [ $compile -ne 0 ]; then
	echo "Configuring C++ bindings" | tee -a $log
	cd C
	if [ $allow_install -ge 1 ]; then
		./configure --auto-install
	else
		./configure
	fi
	if [ $? -eq 0 ]; then
		echo "Compiling C++ bindings" | tee -a $log
		make -s
		if [ $? -eq 0 ]; then
			echo ""
			echo "You can now run protvis by typing ./run" | tee -a $log
			exit 0
		fi
	fi
	echo "" | tee -a $log
	echo "There was an error while compiling the C bindings." | tee -a $log
	echo "You can still run the server without them, but mzML files will not display" | tee -a $log
	echo "" | tee -a $log
	echo "You can now run protvis by typing ./run" | tee -a $log
	exit 1
else
	echo ""
	echo "You can now run protvis by typing ./run" | tee -a $log
	exit 0
fi
