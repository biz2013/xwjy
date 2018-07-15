WORKDIR=/home/osboxes/workspace/xwjy/stakingsvc
SETUPDIR=$WORKDIR/admin
cmd='help'
if [ $# -eq 1 ]; then
   cmd=$1
fi


setup() {

echo "copy service file"
echo "cp $SETUPDIR/files/cnycoin.service /etc/systemd/system/"
cp $SETUPDIR/files/cnycoin.service /etc/systemd/system/

echo "cp $SETUPDIR/files/axf.service /etc/systemd/system/"
cp $SETUPDIR/files/axf.service /etc/systemd/system/

echo "cp $SETUPDIR/files/stakingsvc.service /etc/systemd/system/"
cp $SETUPDIR/files/stakingsvc.service /etc/systemd/system/

echo "systemctl daemon-reload"
systemctl daemon-reload
}

start() {
echo "systemctl start cnycoin.service"
systemctl start cnycoin.service

echo "sleep 1"
sleep 1

echo "systemctl start axf.service"
systemctl start axf.service

echo "sleep 1"
sleep 1

echo "systemctl start stakingsvc.service"
systemctl start stakingsvc.service

}


setup
echo "command is $cmd"

case $cmd in
  start)
    echo "start all stakingsvc service"
    start
    ;; 
  *)
    echo $"Usage: $0 start"
    exit 1
esac
