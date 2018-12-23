#!/bin/bash

usage(){
  echo "usage: backup setting_style [label]"
  echo "  setting_style: production | dev | admin"
  echo "  label: the suffix for the backfiles, if omitted, system will use yyyy_mm_dd_HH_MM_SS"
  exit 1
}

FULLBACKUPWALLET=0
if [ $(date +%u) -eq 6 ]; then
  FULLBACKUPWALLET=1
fi

DATESTR=$(date '+%Y-%m-%d')
LABEL=$(date '+%Y_%m_%d_%H_%M_%S')
SETTING=admin
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

echo "`date -u` will create data backup $BACKUPDATAFILE"
echo "`date -u` will create schema backup $SCHEMABACKUPFILE"
echo "`date -u` will create log backup $LOGBACKUPFILE"
echo "`date -u` backup will use $SETTING config"

WORKHOME=/home/ubuntu/workspace/xwjy/coinExchange
BACKUPROOT=$WORKHOME/site-backup
BACKUPDIR=$BACKUPROOT/$DATESTR
CNYDIR=.cnyfund
CNYROOT=/home/ubuntu
CNYBIN=/usr/local/bin/cnyfund
CNYDATA=/home/ubuntu/.cnyfund
CNYWALLETBACKUP=cnyfund_wallet_$LABEL.dat
AXFROOT=/home/ubuntu/
AXFBIN=/usr/local/bin/axfd
AXFDATADIR=/home/ubuntu/.axf
AXFWALLETBACKUP=axf_wallet_$LABEL.dat
AXFSRC=/home/ubuntu/workspace/xwjy/smwy/src
AWS=/home/ubuntu/.local/bin/aws

echo "`date -u` cd $WORKHOME"
cd $WORKHOME

if [ ! -d "$BACKUPDIR" ]; then
  echo "`date -u` create site back dir  $BACKUPDIR"
  mkdir -p $BACKUPDIR
fi

echo "`date -u` source dj2env/bin/activate"
source dj2env/bin/activate

echo "`date -u` dump database data"
if [ -d "$WORKHOME/tradeex" ]; then
echo "`date -u` python manage.py dumpdata auth.user trading tradeex --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE"
python manage.py dumpdata auth.user trading tradeex --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE
else
echo "`date -u` python manage.py dumpdata auth.user trading --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE"
python manage.py dumpdata auth.user trading --settings=coinExchange.settings.$SETTING | python -mjson.tool > $BACKUPDIR/$BACKUPDATAFILE
fi

echo "`date -u` backup db schema data"
if [ -d "tradeex/migrations" ]; then
echo "`date -u` /bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE tradeex/migrations trading/migrations"
/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE tradeex/migrations trading/migrations
else
echo "`date -u` /bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE trading/migrations"
/bin/tar cvzf $BACKUPDIR/$SCHEMABACKUPFILE trading/migrations
fi

echo "`date -u` backup log files"
echo "`date -u` /bin/tar cvzf $BACKUPDIR/$LOGBACKUPFILE /var/log/coinexchange/coinexchange*"
/bin/tar cvzf $BACKUPDIR/$LOGBACKUPFILE /var/log/coinexchange/coinexchange*

if [ -d "$CNYROOT/$CNYDIR" ]; then 
  echo "`date -u` backup cnywallet files"
  echo "`date -u` cd $CNYROOT"
  cd $CNYROOT
  echo "`date -u` $CNYBIN -datadir=$CNYDATA backupwallet $BACKUPDIR/$CNYWALLETBACKUP"
  $CNYBIN -datadir=$CNYDATA backupwallet $CNYDATA/$CNYWALLETBACKUP
  mv $CNYDATA/$CNYWALLETBACKUP $BACKUPDIR/
fi

cd $AXFROOT
if [ $FULLBACKUPWALLET -eq 1 ]; then
   echo "`date -u` Do FULLBACKUP of axf wallet folder $FULLBACKUPWALLET"
   echo "`date -u` /bin/tar cvzf $BACKUPDIR/$AXFUNDBACKUPFILE $AXFDATADIR"
   /bin/tar cvzf $BACKUPDIR/$AXFUNDBACKUPFILE $AXFDATADIR
else
   echo "`date -u` Backup wallet file of AXF only"
   $AXFBIN --datadir=$AXFDATADIR backupwallet $AXFDATADIR/$AXFWALLETBACKUP
   mv $AXFDATADIR/$AXFWALLETBACKUP $BACKUPDIR/
fi

echo "`date -u` remove any backup that is 5 days old"
echo "`date -u` cd $BACKUPROOT"
cd $BACKUPROOT
echo "`date -u` find . -type d -ctime +5 -exec rm -rf {} \;"
find . -type d -ctime +5 -exec rm -rf {} \;

echo "`date -u` copy to s3..."
echo "`date -u` aws copy: $AWS s3 cp $BACKUPDIR/$SCHEMABACKUPFILE s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/"
$AWS s3 cp $BACKUPDIR/$SCHEMABACKUPFILE s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/

echo "`date -u` aws copy: $AWS s3 cp $BACKUPDIR/$BACKUPDATAFILE s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/"
$AWS s3 cp $BACKUPDIR/$BACKUPDATAFILE s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/

echo "`date -u` aws copy: $AWS s3 cp $BACKUPDIR/$AXFWALLETBACKUP s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/"
$AWS s3 cp $BACKUPDIR/$AXFWALLETBACKUP s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/

echo "`date -u` aws copy: $AWS s3 cp $BACKUPDIR/$CNYWALLETBACKUP s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/"
$AWS s3 cp $BACKUPDIR/$CNYWALLETBACKUP s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/

echo "`date -u` aws copy: $AWS s3 cp $BACKUPDIR/$LOGBACKUPFILE s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/"
$AWS s3 cp $BACKUPDIR/$LOGBACKUPFILE s3://elasticbeanstalk-us-west-2-551441213847/AXFundBackup/


echo "`date -u` Done."

exit 0
