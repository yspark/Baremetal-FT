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

import getopt
import os
import sys


possible_topdir = os.path.normpath(os.path.join(os.path.abspath(
        sys.argv[0]), os.pardir, os.pardir))
if os.path.exists(os.path.join(possible_topdir, "nova", "__init__.py")):
    sys.path.insert(0, possible_topdir)


from nova import exception
from nova import utils
from os.path import exists
from subprocess import Popen, PIPE


def usage():
	print """
usage:
  bm_db_ft MODE [OPTION] [OPTION]... 

  <MODE>
  master
  slave

  <required options>
  --master_ip=<IP address of master server of baremetal fault-tolerance cluster>
  --master_name=<Host name of master server of baremetal fault-tolerance cluster>
  --slave_ip=<IP address of slave server of baremetal fault-tolerance cluster>
  --slave_name=<Host name of slave server of baremetal fault-tolerance cluster>
  
  <Fault-tolerant BM Compute: Optional options>
  --nova_compute_service=<Nova compute service. Default:None>

  <Fault-tolerant BM Database: Optional options>
  --common_ip=<IP address to be used for baremetal DB server or baremetal compute node. Default:None>
  --bm_db=<Baremetal database to be replicated. Default:None>
  --mysql_user=<MySQL user ID, Default:root>
  --mysql_pass=<MySQL password for user ID, Default:nova>
  --master_id=<ID of baremetal database master, Default:1>
  --slave_id=<ID of baremetal database slave, Default:2>
  --mysql_logbin=<MySQL binary log name, Default:mysql-bin>
  --mysql_cnf=<MySQL Configuration file, Default:/etc/my.cnf>
  --mysql_snapshot=<MySQL Snapshot file, Default:/tmp/snapshot.db>  
  
  <Heartbeat: Optional options>
  --eth=<Ethernet port to be used for heartbeat messages. Default:eth0>
  --port=<UDP Port number to be used for heartbeat messages. Default: 694>
  --keep_alive=<Time interval of keep-alive messages. Default: 2(sec)>
  --warn_time=<Period of time after which a warning message is generated. Default: 8>
  --dead_time=<Period of time after which a node is considered dead. Default: 16>
  --init_dead=<Identical to ft_deadtime but applied only when initializing. Default: 32>
  --auto_failback=<on/off. Default:on>
  --auth_pass=<Authentication key/password used in heartbeat message encryption. Default:ha_password>
  --heartbeat_dir=<Heartbeat directory. Default: /etc/ha.d>
  --heartbeat_log_dir=<Heartbeat log directory. Default: /var/log>
	"""
#end def usage():
	

def check_required_opts(values):
	ret = False

	for opt, value in values.items():
		if opt == 'master_ip' or opt == 'master_name' or opt == 'slave_ip' or opt == 'slave_name':
			if value == None:
				print "'%s' should be specified" % opt
				ret = True
	#end for

	if ret == True:
		usage()
		sys.exit(2)
#end def check_values(valeus):


def config_db_duplication(setup_mode, values):
	print "Configuring DB Duplication..."

	output = utils.execute('python', 'bm_db_dual_replication.py',
				setup_mode,
				'--db_master=%s' % values['master_ip'],
				'--db_slave=%s' % values['slave_ip'],
				'--db_name=%s' % values['bm_db'],
				'--mysql_user=%s' % values['mysql_user'],
				'--mysql_pass=%s' % values['mysql_pass'],
				'--master_id=%s' % values['master_id'],
				'--slave_id=%s' % values['slave_id'],
				'--mysql_logbin=%s' % values['mysql_logbin'],
				'--mysql_cnf=%s' % values['mysql_cnf'],
				'--mysql_snapshot=%s' % values['mysql_snapshot'],
				check_exit_code=[0])	

	print output[0]
#end def config_db()


def config_ha_cf(setup_mode, values):
	print "Configuring ha.cf ..."

	if setup_mode == 'master':
		dest_ip = values['slave_ip']
	else:
		dest_ip = values['master_ip']

	cf_file = open('%s/ha.cf' % values['heartbeat_dir'], 'w')
	
	cf_file.write("udpport %s\n" % values['port'])
	cf_file.write("ucast %s %s\n" % (values['eth'], dest_ip))
	
	cf_file.write("keepalive %s\n" % values['keep_alive'])
	cf_file.write("warntime %s\n" % values['warn_time'])
	cf_file.write("deadtime %s\n" % values['dead_time'])
	cf_file.write("initdead %s\n" % values['init_dead'])
	
	cf_file.write("auto_failback %s\n" % values['auto_failback'])
	cf_file.write("node %s\n" % values['master_name'])
	cf_file.write("node %s\n" % values['slave_name'])
	
	cf_file.write("debugfile %s/ha-debug\n" % values['heartbeat_log_dir'])
	cf_file.write("logfile %s/ha-log\n" % values['heartbeat_log_dir'])
	cf_file.write("use_logd yes\n")

	cf_file.close()	
#end def config_ha_cf(setup_mode):


def config_haresource(values):
	print "Configuring haresource ..."

	# Configure haresources
	cf_file = open('%s/haresources' % values['heartbeat_dir'], 'w')
	
	rsc = "%s" % values['master_name']

	if values['common_ip'] != None:
		rsc += " IPaddr::%s" % values['common_ip']
	
	if values['nova_compute'] != None:
		rsc += " %s" % values['nova_compute'] 
	
	rsc += "\n"

	cf_file.write(rsc)
	cf_file.close()
	
# def config_haresource(values):


def config_authkeys(values):
	print "Configuring authkeys ..."

	cf_file = open('%s/authkeys' % values['heartbeat_dir'], 'w')
	cf_file.write("auth 1\n")
	cf_file.write("1 md5 %s\n" % values['auth_pass'])
	cf_file.close()
	
	os.chmod("%s/authkeys" % values['heartbeat_dir'], 0600)		
# def config_authkeys(values):

	
def main():
	if len(sys.argv) < 2:
		usage()
		sys.exit(2)

	if sys.argv[1] == 'master':
		ft_mode = 'master'
	elif sys.argv[1] == 'slave':
		ft_mode = 'slave'
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
			'master_ip=',
			'master_name=',
			'slave_ip=',
			'slave_name=',
			'common_ip=',
			'nova_compute=',
			'bm_db=',
			'mysql_user=',
			'mysql_pass=',
			'master_id=',
			'slave_id=',
			'mysql_logbin=',
			'mysql_cnf=',
			'mysql_snapshot=',
			'eth=',
			'port=',
			'keep_alive=',
			'warn_time=',
			'dead_time=',
			'init_dead=',
			'auto_failback=',
			'auth_pass=',
			'heartbeat_dir=',
			'heartbeat_log_dir=',
			])
	except getopt.GetoptError as err:
		print err
		usage()
		sys.exit(2)
	#end try:
	
	values = {
		'master_ip': None,
		'master_name': None,
		'slave_ip': None,
		'slave_name': None,
		'common_ip': None,
		'nova_compute': None,
		'bm_db': None,
		'mysql_user': 'root',
		'mysql_pass': 'nova',
		'master_id': '1',
		'slave_id': '2',
		'mysql_logbin': 'mysql-bin',
		'mysql_cnf': '/etc/my.cnf',
		'mysql_snapshot': '/tmp/snapshot.db',
		'eth': 'eth0',
		'port': '694',
		'keep_alive': '2',
		'warn_time': '8',
		'dead_time': '16',
		'init_dead': '32',
		'auto_failback': 'on',
		'auth_pass': 'ha_password',
		'heartbeat_dir': '/etc/ha.d',
		'heartbeat_log_dir': '/var/log',
	}

	for opt, arg in opts:
		opt = opt[2:]
		if values.has_key(opt):
			values[opt] = arg
		else:
			print "unrecognized option '%s'" % opt
			print usage
			sys.exit(2)
	#end for	
	
	# Check if required values are specified
	check_required_opts(values)

	print "\n"
	for opt in values:
		print "%s: %s" % (opt, values[opt])
	print "\n"

	# Setup master or slave 
	if ft_mode == 'master':
		print "\n==========================="
		print "Setup fault-tolerant baremetal master"
		print "============================"
	else:
		print "\n==========================="
		print "Setup fault-tolerant baremetal slave"
		print "============================"
	#end if

	# Stop heartbest service	
	utils.execute('service','heartbeat','stop',check_exit_code=[0])	

	# ha.cf configuration
	config_ha_cf(ft_mode, values)

	# haresource configuration
	config_haresource(values)
	
	# authkeys configuration
	config_authkeys(values)

	# Firewall setup
	utils.execute('iptables', '-I', 'INPUT', '1',
					'-p', 'udp', '--dport', '694',
					'-j', 'ACCEPT')

	# setup DB Duplication
	if values['bm_db'] != None:
		config_db_duplication(ft_mode, values)

	# Start heartbest service
	print "Starting heartbeat service"	
	utils.execute('service','heartbeat','restart',check_exit_code=[0])	

	sys.exit(0)
#end def main():


if __name__ == '__main__':
	main()
	
