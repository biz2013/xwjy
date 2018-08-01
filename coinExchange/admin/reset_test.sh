#!/bin/bash
echo "we have $# args"

if [ $# -ne 2 ]; then
   echo "usage: reset_app.sh backupdatafile setting_style"
   echo " backupdatafile: full path of the backup file"
   echo " setting_style: test, product, dev?"
   exit -1
fi

BACKUPDATAFILE=$1
SETTING_STYLE=$2

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
echo "cd $WORKHOME"
cd $WORKHOME

echo "stop site"
sudo /bin/systemctl stop coinexchange.service

echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "delete database"
/usr/bin/mysql -h localhost -u root -p < $WORKHOME/admin/reset_db.sql

echo "create database tables"
echo "python manage.py migrate --settings=coinExchange.settings.$SETTING_STYLE"
python manage.py migrate --settings=coinExchange.settings.$SETTING_STYLE

echo "recover data: python manage.py loaddata $BACKUPDATAFILE --settings=coinExchange.settings.$SETTING_STYLE"
python manage.py loaddata $BACKUPDATAFILE --settings=coinExchange.settings.$SETTING_STYLE


echo "delete logs"
rm -rf $WORKHOME/logs/site.log*

echo "start service"
sudo /bin/systemctl start coinexchange.service

echo "sleep 5 seconds"
sleep 5

echo "setup test"
/usr/bin/curl -L -v http://54.203.195.52/setuptest/

echo "Done."

