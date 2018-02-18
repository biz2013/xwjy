## Reference doc:
Follow the django document: How to deploy with WSGI¶
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/

## Install Apache, MySQL, PHP module on ubuntu 16-04
https://www.digitalocean.com/community/tutorials/how-to-install-linux-apache-mysql-php-lamp-stack-on-ubuntu-16-04 

## Install wsgi module
http://modwsgi.readthedocs.io/en/develop/user-guides/quick-installation-guide.html

## Install Current Trading Machine
Before WSGI is finished, you need to do the following
Assume you git clone under ~/workspace.
1. sudo copy ~/workspace/xwjy/coinExchange/setup/axfund* /etc/systemd/system
2. sudo service start axfund-django.service.  This start the website
3. cd ~/workspace/xwjy/smwy/src/
4. tar xvzf axfd.tar.gz .
5. ./axfd -datadir=../../qb & <-- run at background
6. create following cronjob:
