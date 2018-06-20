#!/bin/bash
echo "we have $# args"

if [ $# -ne 3 ]; then
   echo "usage: reset_app.sh backupdatafile setting_style starting_style"
   echo " backupdatafile: full path of the backup file"
   echo " setting_style: test, product, dev?"
   echo " starting_style: apache systemctl"
   exit -1
fi

BACKUPDATAFILE=$1
SETTING_STYLE=$2
STARTING_STYLE=$3

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
echo "cd $WORKHOME"
cd $WORKHOME

echo "stop apache"
sudo apachectl stop
sudo /bin/systemctl stop axfund-django.service

echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "delete database"
/usr/bin/mysql -h localhost -u root -p < $WORKHOME/setup/reset_db.sql

echo "create database tables"
echo "python manage.py migrate --settings=coinExchange.settings.$SETTING_STYLE"
python manage.py migrate --settings=coinExchange.settings.$SETTING_STYLE

echo "recover data"
python manage.py loaddata $BACKUPDATAFILE --settings=coinExchange.settings.$SETTING_STYLE


echo "delete logs"
rm -rf $WORKHOME/logs/site.log*

echo "start service using $STARTING_STYLE"
if [ "$STARTING_STYLE" = "apache" ]; then
   sudo apachectl start 
elif [ "$STARTING_STYLE" = "systemctl" ]; then
   sudo /bin/systemctl start axfund-django.service
else
   echo "Unknown service control style $STARTING_STYLE"
   exit -1
fi

echo "sleep 5 seconds"
sleep 5

echo "setup test"
/usr/bin/curl -L -v http://localhost/setuptest/

echo "Done."
 



