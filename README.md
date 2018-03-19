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
-i, --interface               Specify whether interface names are needed in topology- yes/no. (default=yes)
-x, --exclude                 Specify devices to be excluded in the topology from the given list if devices in username or file
```

### Outputs

Example using all the flags (except file since username is provided). In actual case, we may not need to use all of them:

```
anandgokul:scripts anandgokul$ <b>python generateTestbedTopology.py -u anandgokul </b> -p systest -x do303 -g yes -i yes

 > Neighbor Details of DUTS in Art list output for user 'anandgokul':
	 * The DUTs owned by anandgokul are:  ['ck338', 'co546', 'do303', 'fm210', 'fm367', 'lf218']

 > Excluding specified devices from topology. Topology will be generated for:
	 * ['co546', 'fm210', 'lf218', 'fm367', 'ck338']

 !!! INFORMATIONAL WARNING !!!
This script will not include interfaces that are shut or errdisabled. If you need to include even those, make sure they are Up.

 !!! LLDP WARNING !!!
This script assumes that all lldp devices are shown in typical format of 'hostname' or 'hostname.sjc.aristanetworks.com'. Untypical lldp info such as mac address will give out unsupported error, please address it if you are shown that error.

 !!! OUTPUT WARNING !!!
This script will consider all non-LLDP supported neighbors (such as linux servers) as Ixia connections only.

Do you want to include even ports connected to ixia (this is best effort)? (Y/n) y

> The topology in text format is:
fm210	(Et27)	--------------------	(Et1)co546
fm210	(Et28)	--------------------	(Et2)co546
lf218	(Et22)	--------------------	(Et22)fm210
lf218	(Et23)	--------------------	(Et23)fm210
fm367	(Et18)	--------------------	(Et18)lf218
fm367	(Et19)	--------------------	(Et19)lf218
fm367	(Et41)	--------------------	(Et41)fm210
fm367	(Et42)	--------------------	(Et42)fm210
ck338	(Et10/1)	--------------------	(Et27)lf218
ck338	(Et10/2)	--------------------	(Et28)lf218
ck338	(Et10/3)	--------------------	(Et25)fm210
ck338	(Et10/4)	--------------------	(Et26)fm210
lf218	(Et3)	--------------------	(unknown)Ixia_54
lf218	(Et1)	--------------------	(unknown)Ixia_83
ck338	(Et16/1)	--------------------	(unknown)Ixia_13
ck338	(Et16/3)	--------------------	(unknown)Ixia_36
ck338	(Et16/2)	--------------------	(unknown)Ixia_87

 ----------------------------------------------------------------------------------------------------------------------

Do you have a preference for location of DUTs (leaf/spine),...? (Y/n) n

----------------------------------------------------------------------------
[MESSAGE] If your device names contains either '.' or '-', it will be replaced by '_' to avoid conflict with other packages

> Completed Successfully:
	* The PDF file has been generated in current directory and OmniGraffle has been opened to edit it. Please choose 	   'Hierarchial' in OmniGraffle to edit it.
	* Script Complete!
```

### Examples
```
generateTestbedTopology.py   <---Generates topology based on file in ~/setup.txt. Will generate a graph and include interfaces.
generateTestbedTopology.py -f ~/home/anandgokul/newfile.txt <---Generates topology based on file on devices mentioned in this file. Will generate a graph and include interfaces.

```
