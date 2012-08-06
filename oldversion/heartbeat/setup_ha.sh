#!/bin/bash

HA_DIR=/etc/ha.d
HA_LOG_DIR=/var/log

# DB account
MYSQL_USER=root
MYSQL_PASS=nova

# HA Master 
HA_MASTER_IP=65.114.169.241
HA_MASTER_HOST=bespin241.east.isi.edu
HA_MASTER_ETH=eth0

# HA Slave
HA_SLAVE_IP=65.114.169.144
HA_SLAVE_HOST=cst144.east.isi.edu
HA_SLAVE_ETH=eth0

# HA UDP PORT
HA_PORT=694

# HA settings
HA_KEEP_ALIVE=2
HA_WARN_TIME=8
HA_DEAD_TIME=16
HA_INIT_DEAD=32
HA_AUTH_PASS=ha_password

HA_DEST_IP=""
HA_MY_ETH=""


# Input argument
case "$1" in
master)
	echo "High Availability - Master Setup"
	HA_MY_ETH=$HA_MASTER_ETH
	HA_DEST_IP=$HA_SLAVE_IP
	;;
slave)
	echo "High Availability - Slave Setup"
	HA_MY_ETH=$HA_SLAVE_ETH
	HA_DEST_IP=$HA_MASTER_IP
	;;
*)
   	echo "Usage: $0 [master|slave]"
	exit 1
	;;
esac

# Stop heartbeat service
service heartbeat stop

# HA ha.cf configuration
echo "Configuring ha.cf..."
cat > $HA_DIR/ha.cf << HA_CF_EOF
udpport $HA_PORT
ucast $HA_MY_ETH $HA_DEST_IP

keepalive $HA_KEEP_ALIVE
deadtime $HA_DEAD_TIME
warntime $HA_WARN_TIME
initdead $HA_INIT_DEAD

auto_failback on
node $HA_MASTER_HOST
node $HA_SLAVE_HOST

debugfile $HA_LOG_DIR/ha-debug
logfile $HA_LOG_DIR/ha-log
use_logd yes
HA_CF_EOF

# HA haresource configuration
echo "Configuring haresources..."
if [ "$1" == "master" ]; then
	cp ./BaremetalMaster $HA_DIR/resource.d/
	cat > $HA_DIR/haresources << HA_RSC_EOF
$HA_MASTER_HOST BaremetalMaster
HA_RSC_EOF
	chmod 744 $HA_DIR/resource.d/BaremetalMaster

else
	cp ./BaremetalSlave $HA_DIR/resource.d/
	cat > $HA_DIR/haresources << HA_RSC_EOF
$HA_MASTER_HOST BaremetalSlave
HA_RSC_EOF
	chmod 744 $HA_DIR/resource.d/BaremetalSlave
fi

# HA auth configuration
echo "Configuring authkeys..."
cat > $HA_DIR/authkeys << HA_AUTH_EOF
auth 1
1 md5 $HA_AUTH_PASS
HA_AUTH_EOF
chmod 600 $HA_DIR/authkeys 


# DB Setup
echo "Set up database for ha..."
mysqladmin -u$MYSQL_USER -p$MYSQL_PASS DROP -fs heartbeat
echo "Creating database heartbeat..."
mysqladmin -u$MYSQL_USER -p$MYSQL_PASS CREATE heartbeat
mysql -u$MYSQL_USER -p$MYSQL_PASS heartbeat -e "CREATE TABLE status (master INT, init_conn INT, state INT);"
if [ "$1" == "master" ]; then
	mysql -u$MYSQL_USER -p$MYSQL_PASS heartbeat -e "INSERT INTO status SET master=1, init_conn=0, state=0;"
else
	mysql -u$MYSQL_USER -p$MYSQL_PASS heartbeat -e "INSERT INTO status SET master=0, init_conn=0, state=0;"
fi

# Start heartbeat service
echo "Starting heartbeat service..."
service heartbeat start

