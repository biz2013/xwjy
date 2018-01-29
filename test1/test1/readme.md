#Deployment steps:

1. Install Apache
sudo apt-get update
sudo apt-get install apache2

install Apache on Ubuntu. (include manage command, way of verification and others commands)
https://www.digitalocean.com/community/tutorials/how-to-install-the-apache-web-server-on-ubuntu-16-04

2. Install mod_wsgi

Follow installation steps
https://devops.profitbricks.com/tutorials/install-and-configure-mod_wsgi-on-ubuntu-1604-1/ 


3. Config Apache, mod_wsgi with our app
modify this file /etc/apache2/sites-available/000-default.conf

Reference:
https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-16-04 
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/modwsgi/

Add below section.

        Alias /static/ /home/chi/workspace/python/projects/xwjy/test1/static/

        <Directory /home/chi/workspace/python/projects/xwjy/test1/static>
            Require all granted
        </Directory>

        <Directory /home/chi/workspace/python/projects/xwjy/test1/test1>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>

        WSGIDaemonProcess test1 python-home=/home/chi/workspace/python/envs2/axfundTrading python-path=/home/chi/workspace/python/projects/xwjy/test1
        WSGIProcessGroup test1

        WSGIScriptAlias / /home/chi/workspace/python/projects/xwjy/test1/test1/wsgi.py


Test config and reload.
sudo apache2ctl configtest
sudo systemctl restart apache2


Current issues:

(1) template not found:
https://stackoverflow.com/questions/30740700/django-templatedoesnotexist-at-home-html 
(2) static file is not permitted.

try: http://{host_ip}/admin, it works. try http://{host_ip} show errors.

4. Authenticating against Django’s user database from Apache
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/apache-auth/ (doing nothing at this point)

5. Future work: SSL Security
https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-16-04 
