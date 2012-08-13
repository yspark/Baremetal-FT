Fault-tolerant Baremetal
========================

Fault-tolerance support for Baremetal consists of two functionalities.

    1. Fault-tolerance support for Baremetal Compute node
    2. Fault-tolerance support for Baremetal Database node

Main goal of this program is builiding a backup node(slave node) of baremetal 
compute/database node(master node) so that whole openstak system can be 
protected from a single point of failure problem. 

For both functionalities, Heartbeat, a part of Linux High-Availability
(http://linux-ha.org), should be installed in both master and slave nodes. 
If you are running RHEL6, you can get Heartbeat from below repositories.::

    [epel]
    name=Extra Packages for Enterprise Linux 6 - $basearch
    mirrorlist=https://mirrors.fedoraproject.org/metalink?repo=epel-6&arch=$basearch
    enabled=0
    gpgcheck=0

    [scientific-linux]
    name=Scientific Linux
    baseurl=http://ftp.scientificlinux.org/linux/scientific/6/x86_64/os/
    enabled=0
    gpgcheck=0

Then you can install Heartbeat.::
    
    yum --enablerepo=epel,scientific-linux install heartbeat

In our testbest, a list of necessary programs are shown below::

    ==================================================================================================================================
     Package                           Arch                   Version                          Repository                        Size
    ==================================================================================================================================
    Installing:
     heartbeat                         x86_64                 3.0.4-1.el6                      epel                             161 k
    Installing for dependencies:
     cluster-glue                      x86_64                 1.0.5-6.el6                      scientific-linux                  70 k
     cluster-glue-libs                 x86_64                 1.0.5-6.el6                      scientific-linux                 115 k
     heartbeat-libs                    x86_64                 3.0.4-1.el6                      epel                             263 k
     perl-TimeDate                     noarch                 1:1.16-11.1.el6                  scientific-linux                  33 k
     resource-agents                   x86_64                 3.9.2-12.el6                     scientific-linux                 473 k
    
    Transaction Summary
    ==================================================================================================================================


Fault-tolerance support for Baremetal Compute Node
--------------------------------------------------
In order to support fault-tolerant baremetal compute node, two baremetal compute 
nodes should be set up properly.  
That means, both master and slave node should be able to operate as a standalone 
compute node.
Then you can execute the script as show below::
    
    ./bm_ft.py [master|slave] \
        --master_ip=<IP address of master node> \
        --master_name=<Host name of master node> \
        --slave_ip=<IP address of slave node> \
        --slave_name=<Host name of slave node> \
        --eth=<Ethernet interface to be used for communication betweeen \
                master node and slave node> \
        --nova_compute=<Service script for openstck nova compute> \

A host name should be identical to the output of 'uname -n'. 
Example of the command is shown as below::

    ./bm_ft.py master \
            --master_ip=10.99.0.3 \
            --master_name=alchemist03 \
            --slave_ip=10.99.0.2 \
            --slave_name=alchemist02 \
            --eth=br100 \
            --nova_compute=openstack-nova-compute 

There are many other optional parameter so please refer to the usage output 
of the command.

When heartbeat is configured properly using this script, either one of master 
or slave node is able to run [nova-compute] service. 
Therefore the scheduelr is see only one running baremetal compute node 
at the moment. 
Once the node which was running [nova-compute] service fails, 
the other node will take over [nova-compute] service. 
Also it's possible to give the preference to the master node by using 
[auto_failback] parameter.


Fault-tolerance support for Baremetal Database Node
--------------------------------------------------
In order to support fault-tolerant baremetal database node, two baremetal database 
nodes should be set up properly.  
Then you can execute the script as show below::
    
    ./bm_ft.py [master|slave] \
        --master_ip=<IP address of master node> \
        --master_name=<Host name of master node> \
        --slave_ip=<IP address of slave node> \
        --slave_name=<Host name of slave node> \
        --eth=<Ethernet interface to be used for communication among 
                master, slave and other openstack nodes> \
        --common_ip=<IP address for baremetal database node>
        --bm_db=<The name of database to be replicated>
    
A host name should be identical to the output of 'uname -n'. 
Example of the command is shown as below::

    ./bm_ft.py master \
            --master_ip=10.99.0.3 \
            --master_name=alchemist03 \
            --slave_ip=10.99.0.2 \
            --slave_name=alchemist02 \
            --eth=br100 \ 
            --common_ip=10.99.0.101 \
            --bm_db=nova_bm

There are many other optional parameter so please refer to the usage output 
of the command.

The script should be executed in the master node first.
Then please copy a snapshot file of [bm_db] to the slave node.
The default location of the snapshot file is '/tmp/snapshot.db' 
and it can be changed using [mysql_snapshot] parameter.

After running the scirpt in the slave node, please run the command below in 
the master node::

    mysql -u[mysql_user] -p[mysql_pass] -e "SLAVE START;"

When heartbeat is configured properly using this script, either one of master 
or slave node owns [common_ip]. 
The head node or any other openstck nodes are able to access baremetal database
through [common_ip]. 
Once the node which owns [common_ip] fails, the other node will take over 
[common_ip].
Also it's possible to give the preference to the master node by using 
[auto_failback] parameter.


Fault-tolerance support for Baremetal Compute/Database Node
-----------------------------------------------------------
This script also support fault-tolerance when both baremetal compute node and 
baremetal database are running in the same machine.
Please put all the necessary parameters in order to exploit this functionality.
Then you can execute the script as show below::
    
    ./bm_ft.py [master|slave] \
        --master_ip=<IP address of master node> \
        --master_name=<Host name of master node> \
        --slave_ip=<IP address of slave node> \
        --slave_name=<Host name of slave node> \
        --eth=<Ethernet interface to be used for communication among 
                master, slave and other openstack nodes> \
        --common_ip=<IP address for baremetal database node>
        --bm_db=<The name of database to be replicated> \
        --nova_compute=<Service script for openstck nova compute>

Example of the command is shown as below::

    ./bm_ft.py master \
            --master_ip=10.99.0.3 \
            --master_name=alchemist03 \
            --slave_ip=10.99.0.2 \
            --slave_name=alchemist02 \
            --eth=br100 \ 
            --common_ip=10.99.0.101 \
            --bm_db=nova_bm \
            --nova_compute=openstack-nova-compute

