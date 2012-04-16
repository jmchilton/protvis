conf_apache2() {
	cat >protvis.conf <<%%%
#This is a sample configuration file. You may need to change some settings provided
#Verify the username and user group values for WSGIDaemonProcess are set to who you want to run the scripts as (default is you)
#if you get the error "(13)Permission denied: mod_wsgi (pid=26962): Unable to connect to WSGI" try uncommenting the following, changing /tmp/wsgi yo a directory that has write permission for the user specified in WSGIDaemonProcess
#WSGISocketPrefix /tmp/wsgi

WSGIApplicationGroup %{GLOBAL}
WSGIPassAuthorization On
WSGIDaemonProcess pyramid user=`id -un` group=`id -gn` processes=1 threads=4 python-path=`env/bin/python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())"`
WSGIScriptAlias / `pwd`/apache.wsgi
Alias /res `pwd`/res

<Directory `pwd`>
	WSGIProcessGroup pyramid
	Order allow,deny
	Allow from all
</Directory>

<Directory `pwd`/res/>
	Order allow,deny
	Allow from all
</Directory>
%%%
	cat >apache.wsgi <<%%%
from pyramid.paster import get_app
application = get_app("`pwd`/production.ini", "main")
%%%
	chmod +x apache.wsgi
	cat <<%%%
You need to make sure that mod_wsgi is installed and enabled, usually with:
  The command "a2enmod wsgi"   OR
  adding "LoadModule wsgi modules/mod_wsgi.so" to the apache2.conf
If mod_wsgi cannot be found you can find it in the package manager, often
under the name libapache2-mod-wsgi
  
You also need to enable this site, usually done with
  Copy protvis.conf to /etc/apache2/sites-available and change the name to
    remove the .conf extension, then run "a2ensite protvis"   OR
  Copy protvis.conf to /etc/apache2/conf.d

Then reload or restart the server:
	service apache2 reload   OR
	/etc/init.d/apache2 reload

NOTE:
  apache2 is often called httpd.
  You will probably need root (sudo) permission to make these changes
%%%
}

conf_apache2
