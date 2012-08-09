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
nodes should be set up properly.  Then we can execute the script as show below::
    
    ./bm_ft.py [master|slave]
        --master_ip=<IP address of master node>  
        --master_name=<Host name of master node> 
        --slave_ip=<IP address of slave node>
        --slave_name=<Host name of slave node>
        --eth=<Ethernet interface to be used for communication betweeen 
            master node and slave node>
        --nova_compute=<Service script for openstck nova compute>



./bm_ft.py slave --master_ip=10.99.0.3 --master_name=alchemist03 --slave_ip=10.99.0.2 --slave_name=alchemist02 --eth=br100 --nova_compute=openstack-nova-compute --common_ip=10.99.0.100 --bm_db=nova_bm


./bm_ft.py slave --master_ip=10.99.0.3 --master_name=alchemist03 --slave_ip=10.99.0.2 --slave_name=alchemist02 --eth=br100 --nova_compute=openstack-nova-compute --common_ip=10.99.0.100 --bm_db=nova_bm
