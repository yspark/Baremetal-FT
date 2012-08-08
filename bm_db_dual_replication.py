#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 University of Southern California / ISI
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import sys
import getopt

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
        sys.argv[0]), os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "nova", "__init__.py")):
    sys.path.insert(0, possible_topdir)

from nova import utils
from nova import exception
from os.path import exists
from subprocess import Popen, PIPE


def usage():
	print """
usage:
  bm_db_replication MODE [OPTION]... 
  <MODE>
  master
  slave

  <required options>
  --db_master=<IP address of baremetal database master>
  --db_slave=<IP address of baremetal database slave>
  --db_name=<Baremetal Database to be replicated> 

  <optional options>
  --master_id=<ID of baremetal database master, Default:1>
  --slave_id=<ID of baremetal database slave, Default:2>
  --mysql_user=<MySQL user ID, Default:root>
  --mysql_pass=<MySQL password for user ID, Default:nova>
  --mysql_logbin=<MySQL binary log name, Default:mysql-bin>
  --mysql_cnf=<MySQL Configuration file, Default:/etc/my.cnf>
  --mysql_snapshot=<MySQL Snapshot file, Default:/tmp/snapshot.db>	
	"""
#end def usage():
	

def check_required_opts(values):
	ret = False

	for opt, value in values.items():
		if opt == 'db_master' or opt == 'db_slave' or opt == 'db_name':
			if value == None:
				print "'%s' should be specified" % opt
				ret = True
	#end for

	if ret == True:
		usage()
		sys.exit(2)
#end def check_values(valeus):


def setup_master(values):

	print "============================"
	print "MySQL Replication - Master Setup"
	print "============================"
	
	##############################################
	# MySQL Congiguration
	##############################################
	print "============================"
	print "MySQL configuration"
	print "============================"

	mysql_cnf_file= open(values['mysql_cnf'], 'rw+')
	buf = mysql_cnf_file.read()

	# server-id
	if "server-id" in buf:
		if "server-id=%s" % values['master_id'] not in buf:
			print "server-id already exists in '%s'." % values['mysql_cnf']
			print "Please make sure that the server-id is different from the slave-id" 	
	else:
		print "Inserting server-id=%s" % values['master_id']
		mysql_cnf_file.write("[mysqld]\nserver-id=%s\n" % values['master_id'])
	#end if

	# log-bin
	if "log-bin=%s" % values['mysql_logbin'] not in buf:
		print "Inserting log-bin=%s" % values['mysql_logbin']
		mysql_cnf_file.write("[mysqld]\nlog-bin=%s\n" % values['mysql_logbin'])

	# binlog-do-db
	if "binlog-do-db=%s" % values['db_name'] not in buf:
		print "Inserting binlog-do-db=%s" % values['db_name']
		mysql_cnf_file.write("[mysqld]\nbinlog-do-db=%s\n" % values['db_name'])

	# report-host
	if "report-host" not in buf:
		print "Inserting report-host=%s" % values['db_master']
		mysql_cnf_file.write("[mysqld]\nreport-host=%s\n" % values['db_master'])

	# auto_increment
	mysql_cnf_file.write("[mysqld]")
	mysql_cnf_file.write("auto_increment_increment=2\n")
	mysql_cnf_file.write("auto_increment_offset=1\n")
	
	mysql_cnf_file.close()

	
	##############################################
	# MySQL Manipulation 
	##############################################
	print "\n==========================="
	print "Setup replication master"
	print "============================"

	# Stop the current slave service if there is
	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 'SLAVE STOP;',
				check_exit_code=[0])
		

	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 'RESET SLAVE;',
				check_exit_code=[0])
	
	# mysql restart
	print "Restarting mysql..."	
	if exists("/etc/init.d/mysqld"):	
		utils.execute('service', 'mysqld', 'restart',
					run_as_root=True, 
					check_exit_code=[0])
	elif exists("/etc/init.d/mysql"):
		utils.execute('service', 'mysql', 'restart',
					run_as_root=True, 
					check_exit_code=[0])
	#end if


	# Grant connection from replication slave
	print "Granting replication to the slave '%s'" % values['db_slave']
	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 
				"GRANT REPLICATION SLAVE ON *.* TO '%s'@'%s' IDENTIFIED BY '%s'" 
					% (values['mysql_user'], values['db_slave'], values['mysql_pass']),
				check_exit_code=[0])

	# Make a DB snapshot
	print "Making snapshot file '%s'..." % values['mysql_snapshot'] 
	buf = utils.execute('mysqldump', 
				'--databases', values['db_name'],
				'--lock-all-tables', '--add-drop-table', '--add-drop-database',
				'--master-data=1',
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				check_exit_code=[0])

	mysql_snapshot_file= open(values['mysql_snapshot'], 'w')
	mysql_snapshot_file.write(buf[0])
	mysql_snapshot_file.close()


	# Initiate Dual Slave Mode
	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 
				"CHANGE MASTER TO MASTER_HOST='%s', MASTER_USER='%s', MASTER_PASSWORD='%s';" 
					% (values['db_slave'], values['mysql_user'], values['mysql_pass']),
				check_exit_code=[0])

	print "\n============================"
	print "Setup Complete"
	print "============================"
	print "Please copy '%s' to the replication slave server" % values['mysql_snapshot']
	print "and run this script with slave mode in the replication slave server.\n"	
	
#end def setup_master(values):


	
def setup_slave(values):

	print "============================"
	print "MySQL Replication - Slave Setup"
	print "============================"
	
	##############################################
	# MySQL Configuration 
	##############################################
	print "============================"
	print "MySQL configuration"
	print "============================"

	mysql_cnf_file= open(values['mysql_cnf'], 'rw+')
	buf = mysql_cnf_file.read()

	# server-id
	if "server-id" in buf:
		if "server-id=%s" % values['slave_id'] not in buf:
			print "server-id already exists in '%s'." % values['mysql_cnf']
			print "Please make sure that the server-id is different from the master-id" 	
	else:
		print "Inserting server-id=%s" % values['slave_id']
		mysql_cnf_file.write("[mysqld]\nserver-id=%s\n" % values['slave_id'])
	#end if

	# log-bin
	if "log-bin=%s" % values['mysql_logbin'] not in buf:
		print "Inserting log-bin=%s" % values['mysql_logbin']
		mysql_cnf_file.write("[mysqld]\nlog-bin=%s\n" % values['mysql_logbin'])

	# binlog-do-db
	if "binlog-do-db=%s" % values['db_name'] not in buf:
		print "Inserting binlog-do-db=%s" % values['db_name']
		mysql_cnf_file.write("[mysqld]\nbinlog-do-db=%s\n" % values['db_name'])

	# report-host
	if "report-host" not in buf:
		print "Inserting report-host=%s" % values['db_slave']
		mysql_cnf_file.write("[mysqld]\nreport-host=%s\n" % values['db_slave'])

	# auto_increment
	mysql_cnf_file.write("[mysqld]")
	mysql_cnf_file.write("auto_increment_increment=2\n")
	mysql_cnf_file.write("auto_increment_offset=2\n")
	

	mysql_cnf_file.close()

	##############################################
	# MySQL Manipulation 
	##############################################
	print "\n==========================="
	print "Setup replication slave"
	print "============================"

	# Stop the current slave service if there is
	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 'SLAVE STOP;',
				check_exit_code=[0])
		

	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 'RESET SLAVE;',
				check_exit_code=[0])
	
	# mysql restart
	print "Restarting mysql..."	
	if exists("/etc/init.d/mysqld"):	
		utils.execute('service', 'mysqld', 'restart',
					run_as_root=True, 
					check_exit_code=[0])
	elif exists("/etc/init.d/mysql"):
		utils.execute('service', 'mysql', 'restart',
					run_as_root=True, 
					check_exit_code=[0])
	#end if


	# Initiate Slave Mode using snapshot file
	print "Initiate slave mode..."
	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 
				"SLAVE STOP;", 
				check_exit_code=[0])

	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 
				"CHANGE MASTER TO MASTER_HOST='%s', MASTER_USER='%s', MASTER_PASSWORD='%s';" 
					% (values['db_master'], values['mysql_user'], values['mysql_pass']),
				check_exit_code=[0])

	print "Reading in snapshot file '%s'" % values['mysql_snapshot']
	p = Popen(['mysql', '-u%s' % values['mysql_user'], '-p%s' % values['mysql_pass']], stdin=PIPE)
	p.communicate(input='%s' % open(values['mysql_snapshot']).read())[0]

	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 
				"SLAVE START;", 
				check_exit_code=[0])

	# Grant connection from replication slave
	print "Granting replication to the slave '%s'" % values['db_master']
	utils.execute('mysql', 
				'-u%s' % values['mysql_user'],
				'-p%s' % values['mysql_pass'],
				'-e', 
				"GRANT REPLICATION SLAVE ON *.* TO '%s'@'%s' IDENTIFIED BY '%s'" 
					% (values['mysql_user'], values['db_master'], values['mysql_pass']),
				check_exit_code=[0])

	print "\n============================"
	print "Setup Complete"
	print "============================"
	


#end def setup_slave(values):

	
def main():
	if len(sys.argv) < 2:
		usage()
		sys.exit(2)

	if sys.argv[1] == 'master':
		replication_mode = 'master'
	elif sys.argv[1] == 'slave':
		replication_mode = 'slave'
	else:
		print "master|slave should be specified"
		usage()
		sys.exit(2)
	#end if

	try:
		opts, args = getopt.getopt(
			sys.argv[2:],
			"",
			[
			'db_master=',
			'db_slave=',
			'db_name=',
			'master_id=',
			'slave_id=',
			'mysql_user=',
			'mysql_pass=',
			'mysql_logbin=',
			'mysql_cnf=',
			'mysql_snapshot=',
			])
	except getopt.GetoptError as err:
		print err
		usage()
		sys.exit(2)
	#end try:
	
	values = {
		'db_master': None,
		'db_slave': None,
		'db_name': None,
		'master_id': '1',
		'slave_id': '2',
		'mysql_user': 'root',
		'mysql_pass': 'nova',
		'mysql_logbin': 'mysql-bin',
		'mysql_cnf': '/etc/my.cnf',
		'mysql_snapshot': '/tmp/snapshot.db'
	}

	for opt, arg in opts:
		if opt == '--db_master':
			values['db_master'] = arg
		elif opt == '--db_slave':
			values['db_slave'] = arg
		elif opt == '--db_slave':
			values['db_slave'] = arg
		elif opt == '--db_slave':
			values['db_slave'] = arg
		elif opt == '--db_name':
			values['db_name'] = arg
		elif opt == '--master_id':
			values['master_id'] = arg
		elif opt == '--slave_id':
			values['slave_id'] = arg
		elif opt == '--mysql_user':
			values['mysql_user'] = arg
		elif opt == '--mysql_pass':
			values['mysql_pass'] = arg
		else:
			print "unrecognized option '%s'" % opt
			print usage
			sys.exit(1)	
	#end for

	# Check if required values are specified
	check_required_opts(values)

	print "\n"
	for opt in values:
		print "%s: %s" % (opt, values[opt])
	print "\n"

	# Setup master or slave 
	if replication_mode == 'master':
		setup_master(values)
	else:
		setup_slave(values)
	
	sys.exit(1)


#end def main():

if __name__ == '__main__':
	main()
	
