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
  bm_compute_ft MODE [OPTION]... 

  <MODE>
  master
  slave

  <required options>
  --master_ip=<IP address of master server of baremetal fault-tolerance cluster>
  --master_name=<Host name of master server of baremetal fault-tolerance cluster>
  --slave_ip=<IP address of slave server of baremetal fault-tolerance cluster>
  --slave_name=<Host name of slave server of baremetal fault-tolerance cluster>
  
  <optional options>
  --mysql_user=<MySQL user ID, Default:root>
  --mysql_pass=<MySQL password for user ID, Default:nova>
  --eth=<Ethernet port to be used for heartbeat messages. Default:eth0>
  --port=<UDP Port number to be used for heartbeat messages. Default: 694>
  --keep_alive=<Time interval of keep-alive messages. Default: 2(sec)>
  --warn_time=<Period of time after which a warning message is generated. Default: 8>
  --dead_time=<Period of time after which a node is considered dead. Default: 16>
  --init_dead=<Identical to ft_deadtime but applied only when initializing. Default: 32>
  --auth_pass=<Authentication key/password used in heartbeat message encryption. Default:ha_password>
  --heartbeat_dir=<Heartbeat directory. Default: /etc/ha.d>
  --heartbeat_log_dir=<Heartbeat log directory. Default: /var/log>
	"""
#end def usage():
	

def check_required_opts(values):
	ret = False

	for opt, value in values.items():
		if opt == 'ft_master_ip' or opt == 'ft_master_name' or opt == 'ft_slave_ip' or opt == 'ft_slave_name':
			if value == None:
				print "'%s' should be specified" % opt
				ret = True
	#end for

	if ret == True:
		usage()
		sys.exit(2)
#end def check_values(valeus):

	
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
			'mysql_user=',
			'mysql_pass=',
			'eth=',
			'port=',
			'keep_alive=',
			'warn_time=',
			'dead_time=',
			'init_dead=',
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
		'mysql_user': 'root',
		'mysql_pass': 'nova',
		'eth': 'eth0',
		'port': '694',
		'keep_alive': '2',
		'warn_time': '8',
		'dead_time': '16',
		'init_dead': '32',
		'auth_pass': 'ha_password'
		'heartbeat_dir': '/etc/ha.d'
		'heartbeat_log_dir': '/var/log'
	}

	for opt, arg in opts:
		opt = opt[2:]
		if values.has_key(opt):
			values[opt] = arg
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
	if ft_mode == 'master':
		print "\n==========================="
	    print "Setup fault-tolerant baremetal master"
		print "============================"
		dest_ip = slave_ip
	else:
		print "\n==========================="
	    print "Setup fault-tolerant baremetal slave"
		print "============================"
		dest_ip = master_ip
	#end if

	# Stop heartbest service	
    utils.execute('service','heartbeat','stop',check_exit_code=[0])	

	# ha.cf configuration




	sys.exit(1)
#end def main():

if __name__ == '__main__':
	main()
	
