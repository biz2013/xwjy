# Ubuntu WSGI Deployment 

## Reference doc:
Follow the django document: How to deploy with WSGI¶
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/

## Install Apache, MySQL, PHP module on ubuntu 16-04
https://www.digitalocean.com/community/tutorials/how-to-install-linux-apache-mysql-php-lamp-stack-on-ubuntu-16-04 

```
sudo apt-get update
sudo apt-get install apache2
sudo ufw app list   (check and adjust UFW firewall to allow web traffic)
sudo ufw status
sudo ufw allow 'Apache Full'
```

## Install wsgi module
Installation steps below come from the following doc: http://modwsgi.readthedocs.io/en/develop/user-guides/quick-installation-guide.html

1) Get modwsgi source code from: https://github.com/GrahamDumpleton/mod_wsgi/releases
```
tar xvfz mod_wsgi-4.5.24.tar.gz
```

2) To setup the package ready for building run the “configure” script from within the source code directory, this command will create makefile.
```
coinExchange/deploy/mod_wsgi-4.5.24$ ./configure --with-python=/usr/bin/python3
```

3) Build
```
sudo make install
```

You will see below message if installation is correct.
----------------------------------------------------------------------
Libraries have been installed in:
   /usr/lib/apache2/modules

4) Load wsgi module in apache

```
// Add below line to apache config: /etc/apache2/apache2.conf
LoadModule wsgi_module modules/mod_wsgi.so

ServerName server_domain_or_IP (ex: 192.168.1.252)
```

Verify configuration and restart
```
sudo apache2ctl configtest
sudo apache2ctl restart apache2
or: 
sudo apache2ctl stop
sudo apache2ctl start
```

Check /var/log/apache2/error.log, verify the wsgi mod are loaded correctly. Looking for "mod_wsgi/4.5.24 Python/3.5 configured".

Current thread 0x00007fcc67cdc780 (most recent call first):
[Mon Feb 19 00:50:31.349310 2018] [mpm_event:notice] [pid 7679:tid 140515891595136] AH00491: caught SIGTERM, shutting down
[Mon Feb 19 00:50:34.921362 2018] [mpm_event:notice] [pid 12205:tid 140587031373696] AH00489: Apache/2.4.18 (Ubuntu) mod_wsgi/4.5.24 Python/3.5 configured -- resuming normal operations
[Mon Feb 19 00:50:34.921426 2018] [core:notice] [pid 12205:tid 140587031373696] AH00094: Command line: '/usr/sbin/apache2'

Also, test http://{IP}/ (ex:192.168.1.252), ensure apache is on.


## Config WSGI for coinExchange

Add below section to /etc/apache2/apache2.conf if we intend to run as embed mode. This is by default, we acctually want to run as daemon mode.

```
WSGIScriptAlias / /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange/wsgi.py
WSGIPythonHome /home/chi/workspace/python/projects/xwjy/dj2env
WSGIPythonPath /home/chi/workspace/python/projects/xwjy/coinExchange/

Alias /static/ /var/www/coinexchange/static/

<Directory /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange>
<Files wsgi.py>
Require all granted
</Files>
</Directory>

<Directory /var/www/coinexchange/static>
Require all granted
</Directory>

<Directory /home/chi/workspace/python/projects/xwjy/coinExchange/static>
Require all granted
</Directory>

```

Run as Daemon mode, by this way we only need to update wsgi.py file to reload whole site, without the need of restart apache process.

Two docs for who to config wsgi demon:
https://modwsgi.readthedocs.io/en/develop/user-guides/quick-configuration-guide.html#delegation-to-daemon-process 
https://modwsgi.readthedocs.io/en/develop/configuration-directives/WSGIDaemonProcess.html?highlight=wsgidaemonprocess

```
sudo vi /etc/apache2/sites-available/000-default.conf

<VirtualHost *:80>

    #ServerName 192.168.1.252 (ex: www.example.com)
    #ServerAlias 192.168.1.252 (ex: example.com)
    #ServerAdmin webmaster@example.com

    LogLevel warn
    WSGIDaemonProcess coinExchange python-home=/home/chi/workspace/python/projects/xwjy/dj2env python-path=/home/chi/workspace/python/projects/xwjy/coinExchange threads=15 display-name=%{GROUP}

    WSGIProcessGroup coinExchange

    WSGIScriptAlias / /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange/wsgi.py
    
    Alias /static/ /var/www/coinexchange/static/

    <Directory /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange>
    <Files wsgi.py>
    Require all granted
    </Files>
    </Directory>

    <Directory /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange>
    Order allow,deny
    Allow from all
    </Directory>

    <Directory /var/www/coinexchange/static>
    Require all granted
    </Directory>

    <Directory /home/chi/workspace/python/projects/xwjy/coinExchange/static>
    Require all granted
    </Directory>

</VirtualHost>
```


## Prepare static files

Collect static files to a common place.
```
mkdir -p /var/www/coinexchange/static  (STATIC_ROOT)
sudo chown -R {user}:{usergroup} (ex: chi:chi) /var/www/coinexchange/static
python manage.py collectstatic
sudo chown -R root:root /var/www/coinexchange/static
```

## Prepare logging
Grant access for apache to write logs.
```
chmod 777 /home/chi/workspace/python/projects/xwjy/coinExchange/logs
```

## Config environment variables

Follow this doc to write env variables, currently we don't have any environment variables. https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/modwsgi/#serving-files

/etc/apache2/envvars

# How to test wsgi config before deploying?

Leverage mod_wsgi-express:
doc: 
http://blog.dscpl.com.au/2015/04/introducing-modwsgi-express.html 
https://pypi.python.org/pypi/mod_wsgi 

mod_wsgi-express start-server coinExchange/wsgi.py

```
sudo apt-get update
sudo apt-get install apache2
sudo ufw app list
sudo ufw status
sudo ufw allow 'Apache Full'
sudo ufw status
sudo systemctl status apache2
hostname -I
  668  ls
  669  cd workspace/
  670  ls
  671  mkdir tmp
  672  cd tmp/
  673  tar xvfz ~/Downloads/mod_wsgi-4.5.24.tar.gz 
  674  cd mod_wsgi-4.5.24/
  675  ls
  676  ./configure 
  677  make
  678  sudo make install
  679  vi /etc/apache2/apache2.conf 
  680  sudo vi /etc/apache2/apache2.conf 
  681  apachectl restart
  682  ls /etc/apache2/mods-available/
  683  sudo apt-get install apache2-utils libexpat1 ssl-cert
  684  sudo apt-get install libapache2-mod-wsgi
  685  sudo /etc/init.d/apache2 restart
  686  sudo nano /etc/apache2/conf-available/wsgi.conf
  687  ls /etc/apache2/conf-available/
  688  sudo nano  /var/www/html/test_wsgi.py
  689  sudo a2enconf wsgi
  690  service apache2 reload
  691  cd ..
  692  less /etc/apache2/sites-available/000-default.conf 
  693  sudo vi /etc/apache2/sites-available/000-default.conf 
  694  sudo apache2ctl configtest
  695  sudo systemctl restart apache2
  696  hostname -I
  697  sudo vi /etc/apache2/sites-available/000-default.conf 
  698  sudo apache2ctl configtest
  699  sudo systemctl restart apache2
  700  ls /etc/apache2/
  701  less /etc/apache2/ports.conf 
  702  less /etc/apache2/apache2.conf 
  703  ls /var/log/apache2/
  704  less /var/log/apache2/error.log 
  705  less /var/log/apache2/access.log 
  706  less /var/log/apache2/other_vhosts_access.log 
  707  ls -al
  708  ls -al /var/log/apache2/
  709  less /var/log/apache2/error.log 
  710  tail /var/log/apache2/error.log 
  711  sudo chmod 755 /var/www/site.log
  712  touch /var/www/site.log
  713  sudo touch /var/www/site.log
  714  sudo chmod 755 /var/www/site.log
  715  tail -f /var/log/apache2/error.log 
  716  sudo ls -al /var/www/
  717  sudo ls -al /var/www/html/
  718  tail -f /var/log/apache2/error.log 
  719  sudo chmod 777 /var/www/site.log
  720  tail -f /var/log/apache2/error.log 

```