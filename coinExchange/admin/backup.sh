#!/bin/bash

usage(){
  echo "usage: backup setting_style [label]"
  echo "  setting_style: production | dev"
  echo "  label: the suffix for the backfiles, if omitted, system will use yyyy_mm_dd_HH_MM_SS"
  exit 1
}

FULLBACKUPWALLET=0
if [ $(date +%u) -eq 6 ]; then
  FULLBACKUPWALLET=1
fi

DATESTR=$(date '+%Y-%m-%d')
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
CNYWALLETBACKUPFILE=cnycoin_$LABEL.tgz
AXFUNDBACKUPFILE=axf_$LABEL.tgz

echo "will create data backup $BACKUPDATAFILE"
echo "will create schema backup $SCHEMABACKUPFILE"
echo "will create log backup $LOGBACKUPFILE"
echo "backup will use $SETTING config"

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
BACKUPDIR=$WORKHOME/site-backup/$DATESTR
CNYDIR=.cnycoin
AXFDIR=qb
CNYROOT=/home/ubuntu
AXFROOT=/home/ubuntu/workspace/xwjy/
AXFBIN=/home/ubuntu/workspace/xwjy/smwy/src/axfd
AXFDATADIR=/home/ubuntu/workspace/xwjy/qb
AXFWALLETBACKUP=axf_wallet_$LABEL.dat
AXFSRC=/home/ubuntu/workspace/xwjy/smwy/src

echo "Backup wallet file of AXF only"
#$AXFBIN --datadir=$AXFDATADIR walletpassphrase $1 30
$AXFBIN --datadir=$AXFDATADIR backupwallet $AXFWALLETBACKUP
mv $AXFSRC/$AXFWALLETBACKUP $BACKUPDIR/$AXFWALLETBACKUP


echo "cd $WORKHOME"
cd $WORKHOME

if [ ! -d "$BACKUPDIR" ]; then
  echo "create site back dir  $BACKUPDIR"
  mkdir -p $BACKUPDIR
fi

echo "source dj2env/bin/activate"
source dj2env/bin/activate

echo "dump database data"
if [ -d "$WORKHOME/tradeex" ]; then
echo "python manage.py dumpdata auth.user trading tradeex --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE"
python manage.py dumpdata auth.user trading tradeex --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE
else
echo "python manage.py dumpdata auth.user trading --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE"
python manage.py dumpdata auth.user trading --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE
fi

echo "backup db schema data"
if [ -d "tradeex/migrations" ]; then
echo "/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE tradeex/migrations trading/migrations"
/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE tradeex/migrations trading/migrations
else
echo "/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE trading/migrations"
/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE trading/migrations
fi

echo "backup log files"
echo "/bin/tar cvzf $BACKUPDIR/$LOGBACKUPFILE logs"
/bin/tar cvzf $BACKUPDIR/$LOGBACKUPFILE logs

if [ -d "$CNYROOT/$CNYDIR" ]; then 
  echo "backup cnywallet files"
  echo "cd $CNYROOT"
  cd $CNYROOT
  echo "/bin/tar cvzf $BACKUPDIR/$CNYWALLETBACKUPFILE $CNYDIR"
  /bin/tar cvzf $BACKUPDIR/$CNYWALLETBACKUPFILE $CNYDIR
fi

cd $AXFROOT
if [ $FULLBACKUPWALLET -eq 1 ]; then
   echo "Do FULLBACKUP of axf wallet folder $FULLBACKUPWALLET"
   exit 0
   echo "/bin/tar cvzf $BACKUPDIR/$AXFUNDBACKUPFILE $AXFDIR"
   /bin/tar cvzf $BACKUPDIR/$AXFUNDBACKUPFILE $AXFDIR
else
   echo "Backup wallet file of AXF only"
   $AXFBIN --datadir=$AXFDATADIR backupwallet $AXFWALLETBACKUP
   mv $AXFSRC/$AXFWALLETBACKUP $BACKUPDIR/$AXFWALLETBACKUP
fi

echo "Done."
exit 0
