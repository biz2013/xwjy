#!/usr/bin/env bash

# go to virtualenv

sudo apt install aptitude  
#get latest default version of default application.  
aptitude update  
aptitude install python-dev  
pip install gunicorn  

sudo service apache2 stop  
sudo aptitude install nginx  

sudo service nginx start  

sudo ufw allow 8000  

# // activate virutalenv  
# // cd xwjy/coinExchange  
# // test gunicorn works  
# gunicorn --bind 127.0.0.1:8000 coinExchange.wsgi  

#deploy coinexchange+gunicorn service 
sudo cp coinexchange.service /etc/systemd/system  
sudo systemctl start coinexchange  
sudo systemctl enable coinexchange  
# check status
sudo systemctl status coinexchange
# // check socket file
# ls {coinexchange work directory} -> coinExchange_nginx.sock

#config nginx
sudo cp coinexchange_nginx /etc/nginx/sites-available/coinexchange
sudo ln -s /etc/nginx/sites-available/coinexchange /etc/nginx/sites-enabled
#test nginx config syntax
sudo nginx -t
sudo systemctl restart nginx
