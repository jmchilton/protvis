#!/bin/sh

super() {
	if [ "`which sudo`" != "" ]; then
		sudo $@
	elif [ "`which su`" != "" ]; then
		su -c "$@" `whoami`
	else
		$@
	fi
	return
}

get() {
	if [ "`which apt-get`" != "" ]; then
		super "apt-get install $1"
	elif [ "`which yum`" != "" ]; then
		super "yum install $1"
	else
		if [ "$2" = "" ]; then 
			echo "Failed to install $1."
			echo "The following packages are required before running: python java python-setuptools python-virtualenv"
			echo "Exiting."
			exit
		else
			super "$2"
		fi
	fi
	return
}

bin_need() {
	echo "Checking for $1"
	if [ "`which $1`" = "" ]; then
		echo "$1 is not installed. Installing it now."
		get $1
	else
		echo "$1 is already installed"
	fi
}

py_need() {
	echo "Checking for $1 package"
	python 2>&1 >/dev/null <<%%%
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
bin_need nodejs
bin_need java
py_need "setuptools" "wget http://peak.telecommunity.com/dist/ez_setup.py -O- | super python"
py_need "virtualenv" "easy_install virtualenv"

echo "Building the virtual environment"
virtualenv --no-site-packages env

echo "Installing pyramid into the virtual environment"
echo "This could take a while"
cd env
bin/easy_install pyramid

echo "The environment has been set up"

echo "Now installing dojo"
./dojo_build release

echo "You can now run the program by typing ./run"
