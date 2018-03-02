# Project Title

Automatic Topology Generator esp. for Arista Internal Users

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Installation

--> In terminal/bash shell, navigate to the directory where you have downloaded this script
--> Then, do a "sudo pip install -r requirements.txt" from that directory
--> Then, run the script using ./AutomatedTopologyGenerator.py username@server::password [user]

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

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system


## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
