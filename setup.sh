#!/bin/sh

echo "Checking for python setuptools package"
python 2>&1 >/dev/null <<%%%
import setuptools
%%%
if [ $? -eq 1 ]; then
	echo "setuptools is not installed. Grabbing it now."
	scr=`mktemp ez_setup.XXXXX.py`
	wget http://peak.telecommunity.com/dist/ez_setup.py -O$scr
	sudo python $scr
	rm $scr
else
	echo "setuptools is already installed"
fi

echo "Checking for virtualenv package"
python 2>&1 >/dev/null <<%%%
import virtualenv
%%%
if [ $? -eq 1 ]; then
	echo "virtualenv is not installed. Installing it now"
	sudo easy_install virtualenv
else
	echo "virtualenv is already installed"
fi

echo "Building the virtual environment"
virtualenv --no-site-packages env

echo "Installing pyramid into the virtual environment"
echo "This could take a while"
cd env
bin/easy_install pyramid

echo "The environment has been set up"
echo "You can now run the program by typing ./run"
