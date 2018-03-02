# Project Title

Automatic Topology Generator esp. for Arista Internal Users

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Installation

1. In terminal/bash shell, navigate to the directory where you have downloaded this script
2. Then, do a "sudo pip install -r requirements.txt" from that directory
3. Then, run the script using ./AutomatedTopologyGenerator.py username@server::password [user]

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
