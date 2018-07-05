WORKDIR=/home/osboxes/workspace/xwjy/stakingsvc
SETUPDIR=$WORKDIR/setup
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

echo "systemctl daemon-reload"
systemctl daemon-reload
}

start() {
echo "systemctl start cnycoin.service"
systemctl start cnycoin.service

echo "systemctl daemon-reload"
systemctl daemon-reload

echo "sleep 1"
sleep 1

echo "systemctl start axf.service"
systemctl start axf.service
}

setup
echo "command is $cmd"

case $cmd in
  start)
    echo "start all stakingsvc service"
    start
    ;; 
  restart)
    echo "restart all stakingsvc service"
    ;;
  stop)
    echo "stop all stakingsvc service"
    ;;
  *)
    echo $"Usage: $0 {start | restart | stop }"
    exit 1
esac
