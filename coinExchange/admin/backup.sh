#!/bin/bash
echo "we have $# args"

if [ $# -ne 2 ]; then
   echo "usage: backup  datadumpfile db_schemabackup setting_style"
   echo " backupdatafile: full path of the dumped data file"
   echo " setting_style: test, product, dev?"
   exit -1
fi

BACKUPDATAFILE=$1
SETTING_STYLE=$2

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
echo "cd $WORKHOME"
cd $WORKHOME


echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "dump database data"
echo "python manage.py dumpdata auth.user trading tradeex $BACKUPDATAFILE --settings=coinExchange.settings.$SETTING_STYLE"
python manage.py dumpdata auth.user trading tradeex $BACKUPDATAFILE --settings=coinExchange.settings.$SETTING_STYLE

echo "backup migration data"
tar cvxf $WORKHOME/migration

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
 



