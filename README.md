# findTestbedTopology.py

Testbed Topology Generator for Arista Internal Users. 
This script will generate a topology of connections based on the devices given by utilising the LLDP output of those devices.

### Installation and Requirements

1. In terminal/bash shell, navigate to the directory where you have downloaded this script
2. Do a 'sudo easy_install pip' to install pip. Skip this step if already installed.
2. Then, do a "sudo pip install -r requirements.txt" from that directory
3. Then, run the script using 'python findTestbedTopology.py [flags]'

### Information Transfer

ONE THING which users need to ensure is to verify that their DUTs ahve management connectivity from their laptops. If not, please add a route to your Mac on the DUTs. You can verify the connectivity by pinging the devices from your laptop initially.

The below example shows how to verify if you have connectivity...I know, duh, what is he thinking...but this is one major reason why the code fails and I haven't handled the exception due to non-reachability YET!
```
anandgokul:~ anandgokul$ ping co546
PING co546.sjc.aristanetworks.com (172.24.78.209): 56 data bytes
64 bytes from 172.24.78.209: icmp_seq=0 ttl=57 time=306.911 ms
64 bytes from 172.24.78.209: icmp_seq=1 ttl=57 time=329.736 ms
^C
--- co546.sjc.aristanetworks.com ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 306.911/318.323/329.736/11.413 ms
anandgokul:~ anandgokul$
```
