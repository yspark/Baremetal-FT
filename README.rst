Fault-tolerant Baremetal
========================

Fault-tolerance support for Baremetal consists of two functionalities.

    Fault-tolerance support for Baremetal Compute node
    Fault-tolerance support for Baremetal Database node

Main goal of this program is builiding a backup node(slave node) of baremetal 
compute/database node(master node) so that whole openstak system can be 
protected from a single point of failure problem. 

For both functionalities, Heartbeat, a part of Linux High-Availability
(http://linux-ha.org), should be installed in both master and slave nodes. 


Fault-tolerance support for Baremetal Compute Node
--------------------------------------------------
In order to support fault-tolerant baremetal compute node, two baremetal compute 
nodes should be set up properly.  
That means, both master and slave node should be able to operate as a standalone 
compute node.
Then we can execute the script as show below::
    
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
Then we can execute the script as show below::
    
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

When heartbeat is configured properly using this script, either one of master 
or slave node owns [common_ip]. 
The head node or any other openstck nodes are able to access baremetal database
through [common_ip]. 
Once the node which owns [common_ip] fails, the other node will take over 
[common_ip].
Also it's possible to give the preference to the master node by using 
[auto_failback] parameter.


