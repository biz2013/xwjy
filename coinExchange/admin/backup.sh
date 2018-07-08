#!/bin/bash

usage(){
  echo "usage: backup setting_style [label]"
  echo "  setting_style: production | dev"
  echo "  label: the suffix for the backfiles, if omitted, system will use yyyy_mm_dd_HH_MM_SS"
  exit 1
}


LABEL=$(date '+%Y_%m_%d_%H_%M_%S')
SETTING=production
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  usage
fi

if [ $# -le 1 ]; then
  SETTING=$1
fi

if [ $# -eq 2 ]; then
  LABEL=$2
fi


BACKUPDATAFILE=datadump_$LABEL.json
SCHEMABACKUPFILE=schema_$LABEL.tgz
LOGBACKUPFILE=logs_$LABEL.tgz

echo "will create data backup $BACKUPDATAFILE"
echo "will create schema backup $SCHEMABACKUPFILE"
echo "will create log backup $LOGBACKUPFILE"
echo "backup will use $SETTING config"

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
BACKUPDIR=$WORKHOME/site-backup

echo "cd $WORKHOME"
cd $WORKHOME

if [ ! -d "$BACKUPDIR" ]; then
  echo "create site back dir  $BACKUPDIR"
  mkdir $BACKUPDIR
fi

echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "dump database data"
echo "python manage.py dumpdata auth.user trading tradeex --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE"
python manage.py dumpdata auth.user trading tradeex --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE

echo "backup db schema data"
echo "/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE tradeex/migrations trading/migrations"
/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE tradeex/migrations trading/migrations

echo "backup log files"
echo "/bin/tar cvzf $BACKUPDIR/$LOGBACKUPFILE logs"
/bin/tar cvzf $BACKUPDIR/$LOGBACKUPFILE logs

echo "Done."
exit 0
