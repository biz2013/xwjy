#!/bin/bash
echo "we have $# args"

if [ $# -ne 1 ]; then
   echo "usage: reset_app.sh setting_style"
   echo " setting_style: test, product, dev?"
   exit -1
fi

SETTING_STYLE=$1

WORKHOME=/home/osboxes/workspace/xwjy/stakingsvc
DATAFILE=$WORKHOME/admin/files/initdata_staking.json

echo "cd $WORKHOME"
cd $WORKHOME

echo "stop site"
sudo /bin/systemctl stop stakingsvc.service

echo "run backup"
sudo ./admin/backup_vm.sh

echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "delete database"
rm -rf db
mkdir db

echo "create database tables"
echo "python manage.py makemigrations --settings=stakingsvc.settings.$SETTING_STYLE"
python manage.py makemigrations --settings=stakingsvc.settings.$SETTING_STYLE

echo "python manage.py migrate --settings=stakingsvc.settings.$SETTING_STYLE"
python manage.py migrate --settings=stakingsvc.settings.$SETTING_STYLE

echo "initialize data: python manage.py loaddata $DATAFILE --settings=coinExchange.settings.$SETTING_STYLE"
python manage.py loaddata $DATAFILE --settings=stakingsvc.settings.$SETTING_STYLE

echo "delete logs"
rm -rf $WORKHOME/logs/site.log*

echo "start service"
sudo /bin/systemctl start stakingsvc.service

echo "sleep 5 seconds"
sleep 5

echo "setup test"
/usr/bin/curl -L -v -X POST -H "Content-Type: application/json" http://localhost:8080/walletgui/setup_staking_user/ --data @./admin/files/userprofile.json

echo "Done."

