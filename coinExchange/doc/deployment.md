# Ubuntu WSGI Deployment 

## Reference doc:
Follow the django document: How to deploy with WSGI¶
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/

## Install Apache, MySQL, PHP module on ubuntu 16-04
https://www.digitalocean.com/community/tutorials/how-to-install-linux-apache-mysql-php-lamp-stack-on-ubuntu-16-04 

```
sudo apt-get update
sudo apt-get install apache2
sudo apt-get install apache2-dev
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
First you need to use dev variant of python3.  To install, run
sudo apt-get install python3-dev
then under coinExchange/deploy/mod_wsgi-4.5.24$ run
sudo make install
```

You will see below message if installation is correct.
----------------------------------------------------------------------
Libraries have been installed in:
   /usr/lib/apache2/modules

4) Load wsgi module in apache

```
// Add below line to apache config: /etc/apache2/apache2.conf
LoadModule wsgi_module /usr/lib/apache2/modules/mod_wsgi.so

ServerName server_domain_or_IP (ex: 192.168.1.252)
```

5) Verify wsgi module:
https://code.google.com/archive/p/modwsgi/wikis/CheckingYourInstallation.wiki
https://stackoverflow.com/questions/8660896/mod-wsgi-isnt-honoring-wsgipythonhome

Verify configuration and restart
```
sudo apache2ctl configtest
sudo apache2ctl restart apache2
or: 
sudo apache2ctl stop
sudo apache2ctl start
Ubuntu:
/etc/init.d/apache2 stop
/etc/init.d/apache2 start
systemctl start apache2.service
systemctl stop apache2.service
systemctl restart apache2.service
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
    Alias /media/ /var/www/coinexchange/media/

    <Directory /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange>
    <Files wsgi.py>
    Require all granted
    </Files>
    </Directory>

    <Directory /home/chi/workspace/python/projects/xwjy/coinExchange/coinExchange>
    Order allow,deny
    Allow from all
    </Directory>

    <Directory /var/www/coinexchange/media>
    Require all granted
    </Directory>

    <Directory /var/www/coinexchange/static>
    Require all granted
    </Directory>

    <Directory /home/chi/workspace/python/projects/xwjy/coinExchange/static>
    Require all granted
    </Directory>

</VirtualHost>
```
## Additional Manual Fix
For whatever reason the latest python won't run django with mysqlclient correctly (this is 2019-08-11). So, I have to follow this doc to manually change the django mysql driver code for latest django version
https://stackoverflow.com/questions/55657752/django-installing-mysqlclient-error-mysqlclient-1-3-13-or-newer-is-required
This is very annoying

## Prepare static files

Collect static files to a common place.
```
sudo mkdir -p /var/www/coinexchange/static  (STATIC_ROOT)
sudo chown -R {user}:{usergroup} (ex: chi:chi) /var/www/coinexchange/static
python manage.py collectstatic --settings=coinExchange.settings.production
sudo chown -R root:root /var/www/coinexchange/static
```

## Prepare media folders

```
sudo mkdir -p /var/www/coinexchange/media/qrcode  (MEDIA_ROOT)
sudo chown -R www-data:www-data /var/www/coinexchange/media
sudo chmod 755 -R /var/www/coinexchange/media
```

## Prepare logging
Grant access for apache to write logs.
```
chmod 777 -R /home/chi/workspace/python/projects/xwjy/coinExchange/logs
```

## Config environment variables

Follow this doc to write env variables, currently we don't have any environment variables. https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/modwsgi/#serving-files

/etc/apache2/envvars

## How to test wsgi config before deploying?

Leverage mod_wsgi-express:
doc: 
http://blog.dscpl.com.au/2015/04/introducing-modwsgi-express.html 
https://pypi.python.org/pypi/mod_wsgi 

mod_wsgi-express start-server coinExchange/wsgi.py
## Other Little Things

1. Donot forget to change the ALLOWED_HOST list in the production.py to match your machine
2. Donot forget to add Listen <port> to /etc/apache2/apache2.conf if you not just listen to 80 and 443
3. Donot forget to change 000-default.conf and your site's .conf file to put right server name in it
4. Donot forget to run sudo a2ensite <your site>.conf to enable the site, and probably you need run sudo a2dissite 000-default.conf to add default site node
5. Donot forget to add /var/log/coinexchange, and /var/www/... for media and static and make www-data:www-data as owner and group for them
   <??? it seems the python manager run will have different permission, maybe when we run them we can't use the same production settings)

6. Donot forget to download the backup upload images and untar to /, it will extended into the images folder otherwise the QRCODE images are gone.
7. Donot forget to set wallet setting json for axfund and cnyfund
8. Donot forget to encrypt wallet (and not forget password) and restart wallet, otherwise when program send money it will fail to unlock wallet

## Other useful commands
```
sudo apt-get update
sudo apt-get install apache2
sudo ufw app list
sudo ufw status
sudo ufw allow 'Apache Full'
sudo ufw status
sudo systemctl status apache2

vi /etc/apache2/apache2.conf 
apachectl restart
ls /etc/apache2/mods-available/
sudo apt-get install apache2-utils libexpat1 ssl-cert
sudo apt-get install libapache2-mod-wsgi

less /etc/apache2/sites-available/000-default.conf 
sudo vi /etc/apache2/sites-available/000-default.conf 
sudo apache2ctl configtest
sudo systemctl restart apache2

less /etc/apache2/ports.conf
less /var/log/apache2/access.log 
less /var/log/apache2/other_vhosts_access.log 

```

## Start Wallet

1. sudo copy ~/workspace/xwjy/coinExchange/setup/axfund* /etc/systemd/system
2. sudo service start axfund-django.service.  This start the website
3. cd ~/workspace/xwjy/smwy/src/
4. tar xvzf axfd.tar.gz .
5. ./axfd -datadir=../../qb & <-- run at background
6. create following cronjob:

*/3 * * * * curl -v http://localhost/trading/account/cron/update_receive/
*/5 * * * * curl -v http://localhost/trading/account/cron/order_batch_process/
* 8 * * * curl -v http://localhost/trading/account/cron/generate_address/

sudo systemctl stop axfund-django.service
/etc/systemd/system/axfund-django_start.sh
``` 
cd /home/ubuntu/workspace/xwjy/coinExchange/     # Working dir
source dj2env/bin/activate
sudo dj2env/bin/python manage.py runserver --settings=coinExchange.settings.dev 0.0.0.0:80

```

### Set up Nginx and Gunicorn
doc: config nginx, gunicorn, django on ubuntu16: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04


sudo apt install aptitude  
// get latest default version of default application.  
aptitude update  
aptitude install python-dev  
pip install gunicorn  

sudo service apache2 stop  
sudo aptitude install nginx  
// sudo service nginx (start|stop|restart) to control Nginx service  

sudo ufw allow 8000  

// activate virutalenv  
// cd xwjy/coinExchange  
// test gunicorn works  
gunicorn --bind 127.0.0.1:8000 coinExchange.wsgi  

// deploy coinexchange+gunicorn service 
sudo cp deploy/gunicorn/coinexchange.service /etc/systemd/system  
sudo systemctl start coinexchange  
sudo systemctl enable coinexchange  
// check status
sudo systemctl status coinexchange
// check socket file
ls {coinexchange work directory} -> coinExchange_nginx.sock

// config nginx
sudo cp deploy/gunicorn/coinexchange_nginx /etc/nginx/sites-available/coinexchange
sudo ln -s /etc/nginx/sites-available/coinexchange /etc/nginx/sites-enabled
// test nginx config syntax
sudo nginx -t
sudo systemctl restart nginx

### Troubleshooting

Check the Nginx process logs by typing: `sudo journalctl -u nginx`
Check the Nginx access logs by typing: `sudo less /var/log/nginx/access.log`
Check the Nginx error logs by typing: `sudo less /var/log/nginx/error.log`
Check the Gunicorn application logs by typing: `sudo journalctl -u gunicorn`
Check port number occupied by process: `netstat -tulpn`


For more troubleshooting: look at https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04

### Change code and redeploy with Gunicorn systemd service
sudo systemctl daemon-reload
sudo systemctl restart coinexchange

### Update Nginx config
sudo cp deploy/gunicorn/coinexchange_nginx /etc/nginx/sites-available/coinexchange
sudo nginx -t
sudo systemctl restart nginx
