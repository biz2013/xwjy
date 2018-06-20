#!/bin/bash
echo "we have $# args"

if [ $# -ne 3 ]; then
   echo "usage: backup  datadumpfile db_schemabackup setting_style"
   echo " backupdatafile: full path of the dumped data file"
   echo " setting_style: test, product, dev?"
   exit -1
fi

BACKUPDATAFILE=$1
SCHEMABACKUPFILE=$2
SETTING_STYLE=$3

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
echo "cd $WORKHOME"
cd $WORKHOME


echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "dump database data"
echo "python manage.py dumpdata auth.user trading tradeex | python -mjson.tool >  $BACKUPDATAFILE"
python manage.py dumpdata auth.user trading tradeex | python -mjson.tool > $BACKUPDATAFILE

echo "backup migration data"
echo "/bin/tar cvzf $WORKHOME/$SCHEMABACKUPFILE tradeex/migrations trading/migrations"
/bin/tar cvzf $WORKHOME/$SCHEMABACKUPFILE tradeex/migrations trading/migrations

echo "Done."
