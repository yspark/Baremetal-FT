#!/bin/bash

MYSQL_MASTER_IP=65.114.169.241
MYSQL_MASTER_ID=1

MYSQL_SLAVE_IP=65.114.169.144
MYSQL_SLAVE_ID=2

MYSQL_CNF=/etc/my.cnf
MYSQL_USER=root
MYSQL_PASS=nova
MYSQL_LOG_BIN=mysql-bin

# Can add additional databases after a blank space, like "baremetal db1 db2 db3"
MYSQL_DATABASES="baremetal test"
MYSQL_SNAPSHOT_FILE=snapshot.db


setup_master() {
	# Configure my.cnf file
	grep -q "server-id" $MYSQL_CNF
	if [ "$?" == "1" ]; then
    	echo "Inserting server-id into $MYSQL_CNF"
		echo "[mysqld]" >> $MYSQL_CNF
    	echo "server-id=$MYSQL_MASTER_ID" >> $MYSQL_CNF
	else
		echo "================================="
		echo "server-id already exists in $MYSQL_CNF. Please make sure it's different from slave's server-id."
		grep "server-id" $MYSQL_CNF
		echo "================================="
	fi

	grep -q "log-bin" $MYSQL_CNF
	if [ "$?" == "1" ]; then
  		echo "Inserting log-bin into $MYSQL_CNF"
		echo "[mysqld]" >> $MYSQL_CNF
    	echo "log-bin=$MYSQL_LOG_BIN" >> $MYSQL_CNF
	else
		echo "================================="
		echo "log-bin already exists in $MYSQL_CNF. Please make sure $MYSQL_CNF has log-gin=$MYSQL_LOG_BIN."
		grep "log-bin" $MYSQL_CNF
		echo "================================="
	fi

	grep -q "binlog-do-db" $MYSQL_CNF
	if [ "$?" == "1" ]; then
   		echo "Inserting binlog-do-db into $MYSQL_CNF"
  	 	echo "[mysqld]" >> $MYSQL_CNF
   		for DATABASE in $MYSQL_DATABASES; do 
			echo "binlog-do-db=$DATABASE" >> $MYSQL_CNF
		done
	else
		echo "================================="
		echo "binlog-do-db already exists in $MYSQL_CNF. Please make sure $MYSQL_CNF has proper list of databases."
		grep "binlog-do-db" $MYSQL_CNF	
		echo "================================="
	fi

	# Restart MySQL service
	service mysqld restart
	
	# Stop the current slave service if there is
	mysql -u$MYSQL_USER -p$MYSQL_PASS -e "STOP SLAVE;"
	mysql -u$MYSQL_USER -p$MYSQL_PASS -e "RESET SLAVE;"

	# Allow connection from slave
	mysql -u$MYSQL_USER -p$MYSQL_PASS -e "GRANT REPLICATION SLAVE ON *.* TO '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASS';"

	# Make a snapshot and copy to slave
	echo "Creating DB Snapshot..."
	mysqldump --databases $MYSQL_DATABASES --lock-all-tables --add-drop-table --add-drop-database --master-data=1 -u$MYSQL_USER -p$MYSQL_PASS > $MYSQL_SNAPSHOT_FILE

	echo "Transferring Snapshot to Slave..."
	mysql -h$MYSQL_SLAVE_IP -u$MYSQL_USER -p$MYSQL_PASS -e "SLAVE STOP;"
	mysql -h$MYSQL_SLAVE_IP -u$MYSQL_USER -p$MYSQL_PASS -e "CHANGE MASTER TO MASTER_HOST='$MYSQL_MASTER_IP', MASTER_USER='$MYSQL_USER', MASTER_PASSWORD='$MYSQL_PASS';"
	mysql -h$MYSQL_SLAVE_IP -u$MYSQL_USER -p$MYSQL_PASS < $MYSQL_SNAPSHOT_FILE
	mysql -h$MYSQL_SLAVE_IP -u$MYSQL_USER -p$MYSQL_PASS -e "SLAVE START;"

	# Verify the whole master/slave setup
	echo "Verify the result"
	mysql -u$MYSQL_USER -p$MYSQL_PASS -e "SHOW MASTER STATUS;"
	mysql -h$MYSQL_SLAVE_IP -u$MYSQL_USER -p$MYSQL_PASS -e "SHOW SLAVE STATUS;"
}

setup_slave() {

	#configure my.cnf file
	grep -q server-id $MYSQL_CNF
	if [ "$?" == "1"  ]; then
		echo Inserting server-id into $MYSQL_CNF
		echo '[mysqld]' >> $MYSQL_CNF
		echo server-id=$MYSQL_SLAVE_ID >> $MYSQL_CNF
	else
		echo "server-id already exists in $MYSQL_CNF. Please make sure it's different from master's server-id."
		grep server-id $MYSQL_CNF
	fi

	grep -q report-host $MYSQL_CNF
	if [ "$?" == "1" ]; then
		echo Inserting report-host into $MYSQL_CNF
		echo '[mysqld]' >> $MYSQL_CNF
		echo report-host=$MYSQL_SLAVE_IP >> $MYSQL_CNF
	fi

	# Stop slave 
	echo Terminating current slave status
	mysql -u$MYSQL_USER -p$MYSQL_PASS -e "STOP SLAVE;"
	mysql -u$MYSQL_USER -p$MYSQL_PASS -e "RESET SLAVE;"

	# Restart MySQL service
	service mysqld restart
}


usage() {
	echo "Usage: $0 [master|slave]"
	exit 1
}	

###############################################################################
#
# Main procedure
#
###############################################################################
# Call usage() function if master or slave is not provided
[[ $# -eq 0 ]] && usage


if [ "$1" ==  "master" ]; then
	echo "MySQL duplication - Master setup"
	setup_master
elif [ "$1" == "slave" ]; then
	echo "MySQL duplication - Slave setup"
	setup_slave
else
	usage
fi





