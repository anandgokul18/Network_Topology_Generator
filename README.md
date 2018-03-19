# generateTestbedTopology.py

Testbed Topology Generator for Arista Internal Users. 
This script will generate a topology of connections based on the devices given by utilising the LLDP output of those devices. The user need to have a route to the DUTs from the device on which they are running this script.

By default, the topology will be generated for devices specified in ~/setup.txt. If user needs to generate topology based on username or other file, he/she needs to use the flags.

### Installation and Requirements

1. In terminal/bash shell, navigate to the directory where you have downloaded this script
2. Do a 'sudo easy_install pip' to install pip. Skip this step if already installed.
2. Then, do a "sudo pip install -r requirements.txt" from that directory
3. Then, run the script using 'python generateTestbedTopology.py [flags]'

### Inputs

```
arguments:

-f, --file                    Specify a Setup File / DUT List to Load (default = ~/setup.txt)'
-u, --user                    Specify a Arista username for finding the topology based on rdam info of that user. Note. If both username and file is provided, username will be taken
-p, --pool                    Specify the pool of the username, if specifying username for getting topology. (default= systest)
-g, --graph                   Choice for graph generation- yes/no. (default= yes)
-i, --interface
-x, --exclude
```

### Outputs

### Examples
