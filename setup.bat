@ECHO OFF
ECHO. >setup.log

IF [%1]==[] (
	ECHO No python specified. Searching for it...
	ECHO No python specified. Searching for it... >>setup.log
	IF EXIST C:\Python27\python.exe (
		SET PYDIR=C:\Python27
	) ELSE (
		IF EXIST C:\Python\python.exe (
			SET PYDIR=C:\Python
		) ELSE (
			IF EXIST C:\Program^ Files\Python27\python.exe (
				SET PYDIR=C:\Program^ Files\Python27
			) ELSE (
				IF EXIST C:\Program^ Files\Python\python.exe (
					SET PYDIR=C:\Program^ Files\Python
				) ELSE (
					IF EXIST C:\Program^ Files^ ^(x86^)\Python27\python.exe (
						SET PYDIR=C:\Program^ Files^ ^(x86^)\Python27
					) ELSE (
						IF EXIST C:\Program^ Files^ ^(x86^)\Python\python.exe (
							SET PYDIR=C:\Program^ Files^ ^(x86^)\Python
						) ELSE (
							ECHO Usage %0 C:\python\install\folder
							ECHO Usage %0 C:\python\install\folder >>setup.log
							GOTO :end
						)
					)
				)
			)
		)
	)
	ECHO Found python at "%PYDIR%"
	ECHO Found python at "%PYDIR%" >>setup.log
) ELSE (
	SET PYDIR=%1
)

ECHO Checking for setuptools
ECHO Checking for setuptools >>setup.log
"%PYDIR%\python.exe" -c "import setuptools" 2>>setup.log
IF %ERRORLEVEL% EQU 0 (
	ECHO Found
	ECHO Found >>setup.log
	GOTO :have_setuptools
)

ECHO Not found
ECHO Not found >>setup.log

IF EXISTS ez_setup.py (
	ECHO Already have install script
	ECHO Already have install script >>setup.log
	GOTO :have_setuptools_file
)

ECHO Downloading
ECHO Downloading >>setup.log
"%PYDIR%\python.exe" -c "import urllib, sys; s=urllib.urlopen('http://peak.telecommunity.com/dist/ez_setup.py').read(); sys.stdout.write(s); exit(len(s) == 0)" > ez_setup.py
IF %ERRORLEVEL% EQU 0 GOTO :have_setuptools_file

ECHO Failed to download http://peak.telecommunity.com/dist/ez_setup.py
ECHO Failed to download http://peak.telecommunity.com/dist/ez_setup.py >>setup.log
ECHO Please download the file and place it in %~dp0 then run this script again
ECHO Please download the file and place it in %~dp0 then run this script again >>setup.log
GOTO :end

:have_setuptools_file
	ECHO Installing
	ECHO Installing >>setup.log
	"%PYDIR%\python.exe" ez_setup.py
	IF %ERRORLEVEL% NEQ 0 (
		ECHO Failed to install setuptools
		ECHO Failed to install setuptools >>setup.log
		GOTO :end
	)
	del ez_setup.py

:have_setuptools
	ECHO Checking for virtualenv
	ECHO Checking for virtualenv >>setup.log
	"%PYDIR%\python.exe" -c "import virtualenv" 2>>setup.log
	IF %ERRORLEVEL% EQU 0 (
		ECHO Found
		ECHO Found >>setup.log
		GOTO :have_virtualenv
	)
	ECHO Installing
	ECHO Installing >>setup.log
	"%PYDIR%\Scripts\easy_install.exe" virtualenv
	IF %ERRORLEVEL% NEQ 0 (
		ECHO Failed to install virtualenv
		ECHO Failed to install virtualenv >>setup.log
		GOTO :end
	)

:have_virtualenv
	ECHO Installing a virtual environment
	ECHO Installing a virtual environment >>setup.log
	"%PYDIR%\Scripts\virtualenv.exe" env 2>&1 >>setup.log
	ECHO Configuring the virtual environment
	ECHO Configuring the virtual environment >>setup.log
	env\Scripts\easy_install.exe https://github.com/Pylons/pyramid/archive/1.4.5.tar.gz 2>&1 >>setup.log
	env\Scripts\easy_install.exe PasteScript 2>&1 >>setup.log
	env\Scripts\easy_install.exe WebError 2>&1 >>setup.log
	env\Scripts\pip.exe install cherrypy 2>&1 >>setup.log
	mklink /D res\dojo dojo_mini
	ECHO Done
	ECHO Done >>setup.log
	ECHO.
	ECHO You can now run the server by running run.bat
:end
	SET PYDIR=
	ECHO.
	PAUSE
