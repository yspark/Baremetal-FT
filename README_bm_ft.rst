Fault-tolerant Baremetal
========================

Fault-tolerance support for Baremetal consists of two functionalities.

    1. Fault-tolerance support for Baremetal Compute node
    2. Fault-tolerance support for Baremetal Database node

Main goal of this program is builiding a backup node of baremetal 
compute/database node so that whole openstak system can prevent
a single point of failure problem. 

For both functionalities, Heartbeat, a part of Linux High-Availability (http://linux-ha.org),  should be installed 
