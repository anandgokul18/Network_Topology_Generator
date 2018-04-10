#!/usr/bin/env python
# coding=utf8

'''
This script creates a topology 
based on the DUTs specified by you in a file 
or based on your Arista username

This tool also gives you the option to include Ixia ports
'''


#Python Module Imports
import argparse
import collections
import logging
import os
import re
import string
import socket
import subprocess
import time
from random import randint

#Non-SWAT and non-default Python libraries that are additionally needed by this script
import graphviz
from graphviz import Source 

#SWAT Module Imports
import logLib
from clientLib import sendEmail
from eosLldp import EosLldp
from eosIntf import EosIntf
from initToolLib import connectDevices
from scriptLib import abort
try:
	from proxyLib import Proxy, checkProxySession
	#from labLib import findDuts   #Doesn't work due to oauth2client version issue...using proxylib to run Art command directly
except ImportError as e:
	message='''
	If you get import error above, then, you have 2 options to fix it:

	Option A: Run this SWAT tool from your mac and update the oauth2client using "sudo pip install oauth2client==4.1.2" on your mac
	Option B: Run this SWAT tool from a VIRTUALENV on arst or syscon servers using "source /opt/venv/bin/activate" and then update oauth2client using "pip install oauth2client==4.1.2" and then run this script

	WARNING: DO NOT UPDATE oauthclient using 'sudo' on syscon or arst servers since installing this version breaks Art tools..Install it on virtualenv without using 'sudo'
	'''
	print("ERROR: "+ str(e))
	print(message)
	abort('')




#Internal Functions to massage data provided by SWAT and generate graphs

#The below function gets DUTlist from a file
def fileDutList(username,filePath):
	try:

		listofdutsasperfile=[]
		temp=[]

		file = open(filePath)
		listofdutsasperfile = file.readlines()

		for i,data in enumerate(listofdutsasperfile):
			if '#' in data[0] or '\n' in data[0]:
				listofdutsasperfile[i]=None

		for i,data in enumerate(listofdutsasperfile):
			if data!=None:
				temp.append(data.strip())

		logging.info("\n > List of DUTS as per the file provided is:")
		logging.info("\t * "+str(temp))
		return temp
	except IOError:
		logging.info("\n[ERROR]: File does not exist in "+filePath+" . Please ensure correct file location to proceed \n")
		abort()

#The below function uses SWAT library to find the list of DUTs owned by user
@checkProxySession
def userDutList(username,poolname):

	print "----------------------------------------------------------------------------------"
	#print "[WARNING] If you haven't setup the SSH Keys for Syscon (required by SWAT tool libraries), you will be prompted to type 'YES' and provide your Syscon password. If you do not wish for the Swat script to do that for you, fix it yourself when prompted! \n "
	#print '''[MESSAGE] If you are getting any "Exception raised in 'python /usr/bin/Art list --pool=systest '", then, it is due to Art commands are failing from the server in which you are running this script... Contact @syscon-maintainers '''
	print "[MESSAGE] SWAT library to read from rdam takes time sometimes...Please be patient"
	print "----------------------------------------------------------------------------------"
	#alldevices=findDuts(pool=poolname, all=True)
	cmd = "Art list --pool=%s" % poolname
	output = Proxy.session.cliSend(cmd)
	#print output


	# Parse Output
	retVal = {}
	prefixes=None
	chipsets=None
	category='all'
	for line in output[2:]:
        # Initialize DUT Variables
		dut = line[0]
		match = re.search('^([a-z]{2,3})\d+$', dut)

        # Skip Unexpected DUT Names (e.g CVP nodes)
		if not match: continue

        # DUT Data
		dutPrefix = match.group(1)

    	# RDAM Info
		location = line[1]
		owner = line[2] if line[2] != '+' else line[4]

        # Create dictionary with duts as keys & dut information as values
		retVal[dut] = { 'owner': owner}

		retVal = collections.OrderedDict(retVal)




	devices=retVal.items()

	dictOfDevicesbyuser=[]
	listofDevicesbyuser=[]

	for i,data in enumerate(devices):
		if data[1]['owner']==username:
			dictOfDevicesbyuser.append(data)
			listofDevicesbyuser.append(data[0])

	#print dictOfDevicesbyuser
	#print listofDevicesbyuser

	print "\n > The DUTs owned by " + username +" are:  \n\t *  " + str(listofDevicesbyuser)

	return listofDevicesbyuser

'''	
#The below function uses SWAT library to find the list of DUTs owned by user...has oauth2client version issue...The above commented code fixes this
def userDutList(username,poolname):

	alldevices=findDuts(pool=poolname, all=True)

	devices=alldevices.items()

	dictOfDevicesbyuser=[]
	listofDevicesbyuser=[]

	for i,data in enumerate(devices):
		if data[1]['owner']==username:
			dictOfDevicesbyuser.append(data)
			listofDevicesbyuser.append(data[0])

	logging.info("\n > The DUTs owned by " + username +" are:  \n\t *  " + str(listofDevicesbyuser))
	return listofDevicesbyuser
'''
def excludedFromList(finalListOfDuts,excludeDuts):
	#Removing the matches using intersections
	ss= set(finalListOfDuts)
	fs =set(excludeDuts)

	finallist= list(ss.union(ss)  - ss.intersection(fs))
	
	logging.info("\n > Excluding specified devices from topology. Topology will be generated for: ")
	logging.info("\t * "+str(finallist))

	return finallist

def warningMessage():
	message='''
	\n !!! INFORMATIONAL WARNING !!! 
	This script will not include interfaces that are shut or errdisabled. If you need to include even those, make sure they are Up.
	\n !!! LLDP WARNING !!!
	This script assumes that all lldp devices are shown in typical format of 'hostname.sjc.aristanetworks.com'. Untypical lldp info such as mac address will give out unsupported error, please address it if you are shown that error.
	\n !!! OUTPUT WARNING !!!
	This script will consider all non-LLDP supported neighbors (such as linux servers) as Ixia connections only. \n
	'''
	logging.info(message)

def lldpInfo(dutslist):
	
#The below code will grab lldp info from all DUTs in json format using SWAT library 
	tempDictOfConnections=[]

	for i in xrange(0,len(dutslist)):
		
		#Getting LLDP info using SWAT library function
		a=connectDevices(dutslist[i])
		logging.info("[MESSAGE]: Getting LLDP info from "+dutslist[i])
		a,=a
		temp = a.getLldpInfo()

		allneighbors =temp['neighbors']

		for j in xrange(0,len(allneighbors)):
			temp_diction = allneighbors[j]
			temp_diction['myDevice']=str(dutslist[i]) #+'.sjc.aristanetworks.com'
			tempDictOfConnections.append(temp_diction)

		tempDictOfConnections = tempDictOfConnections[:-1]

	#************************************************************************
	#The below code will use regular expresions to get only the DUT name (and not hostname) since some people use naming schemes like ck221_leaf (OR) s1_ckp355

	regex = r"(?:[^\-_\+\|\.]*)[a-z][a-z][0-9][0-9][0-9](?:[^\-_\+\|\.]*)"

	for i in xrange(0,len(tempDictOfConnections)):
		#For neighbor names
		test_str = tempDictOfConnections[i]['neighbor']
		matches = re.search(regex, test_str, re.IGNORECASE)
		tempDictOfConnections[i]['neighbor']= matches.group()

		#For my device names
		test_str = tempDictOfConnections[i]['myDevice']
		matches = re.search(regex, test_str, re.IGNORECASE)
		tempDictOfConnections[i]['myDevice']= matches.group()

	#************************************************************************
	#The below code will remove the duplicates from the grand dictionary such that one connection shows up only once. The duplicates are marked as key=temp and value=NULL

	for i in xrange(0,len(tempDictOfConnections)):
		tempvar= tempDictOfConnections[i] #Storing each dictionary in one temp variable
		instantaneoustempvar= []
		instantaneoustempvar=[tempvar['neighbor'],tempvar['neighbor-port']]
		tempvar['neighbor']= tempvar['myDevice']
		tempvar['neighbor-port']= tempvar['port']
		tempvar['myDevice']=instantaneoustempvar[0]
		tempvar['port']=instantaneoustempvar[1]

		count=0
		for j in xrange(0,len(tempDictOfConnections)):
			if tempvar == tempDictOfConnections[j]:
				count=count+1

		if count==2:
			tempDictOfConnections[i]={'temp':'Null'}


	#************************************************************************
	#The below code will remove the duplicates completely by removing dictionaries with key as temp. ALso, removing the '.sjc.aristanetworks.com' in DUT name

	dictionaryOfConnections=[] #This list will have only non-duplicate values

	for i in xrange(0,len(tempDictOfConnections)):
		if tempDictOfConnections[i].get('temp')== None:
			tempDictOfConnections[i]['neighbor']=tempDictOfConnections[i]['neighbor'].split('.')[0]
			tempDictOfConnections[i]['myDevice']=tempDictOfConnections[i]['myDevice'].split('.')[0]
			try:
				tempDictOfConnections[i]['port']='Et'+(tempDictOfConnections[i]['port'].split('Et')[1])
				tempDictOfConnections[i]['neighbor-port']='Et'+(tempDictOfConnections[i]['neighbor-port'].split('Et')[1])
			except:
				#This block will not make any changes to non-Arista devices
				continue

			dictionaryOfConnections.append(tempDictOfConnections[i])

	return dictionaryOfConnections


#THE BELOW BLOCK HAS BEEN COMMENTED DUE TO THIS LIBRARY NOT PRESENT IN SWAT TOOL
'''
#The below function get ixia details (by finding diff of connected and lldp interfaces)
def ixiaConnectionDetailGrabber(dutslist,finalConnectionDetails):
	
	ixialist=[]

	for i in xrange(0,len(dutslist)):
	
		try:	
			#Getting Connected Interfaces info using SWAT library function
			a=connectDevices(dutslist[i])
			logging.info("[MESSAGE]: Getting Ixia Details info from "+dutslist[i])
			a,=a
			a.setAccessMethod('api')
			temp = a.getConnectedIntfs()

			allconnections =temp
			listofconnections= allconnections.keys()

			#Removing management and port-channel interfaces from list
			for k in xrange(0,len(listofconnections)):
				if 'Management' in listofconnections[k] or 'Port-Channel' in listofconnections[k] or '.' in listofconnections[k]:
					listofconnections[k]=None

			#Removing lldp interfaces from ixia interfaces
			for j in xrange(0,len(finalConnectionDetails)):
			   	if finalConnectionDetails[j]['neighbor'] or finalConnectionDetails[j]['myDevice']==dutslist[i]:
			   		if finalConnectionDetails[j]['neighbor']==dutslist[i]:
			   			for k in xrange(0,len(listofconnections)):
			   				if listofconnections[k]==('Ethernet'+finalConnectionDetails[j]['neighbor-port'].split('Et')[1]):
			   					listofconnections[k]=None
			   		if finalConnectionDetails[j]['myDevice']==dutslist[i]:
			   			for k in xrange(0,len(listofconnections)):
			   				if listofconnections[k]==('Ethernet'+finalConnectionDetails[j]['port'].split('Et')[1]):
			   					listofconnections[k]=None
			
			#Makes a dictionary containing the DUT name and the Ixia ports
			onlyixiaconnections=[]
			for k in xrange(0,len(listofconnections)):
				ixiadict={}
				if listofconnections[k]!=None:
					onlyixiaconnections.append(listofconnections[k])
					ixiadict['neighbor']=dutslist[i]
					ixiadict['neighbor-port']=('Et'+listofconnections[k].split('Ethernet')[1])
					ixiadict['myDevice']='Ixia' 
					ixiadict['port']='unknown'
					ixialist.append(ixiadict)
		except:
			logging.info("[MESSAGE]: Skipping "+dutslist[i] +" from Ixia connection calculation due to some error")
			continue
	
	return ixialist
'''

def ixiaConnectionDetailGrabber(dutslist,finalConnectionDetails):
	
#************************************************************************
#The below code will grab lldp info from all DUTs in json format and refine it and
#it will consolidate all the lldp information into a single dictionary

	#print finalConnectionDetails

	ixialist=[]

	for i in xrange(0,len(dutslist)):
	
		try:	
			#Using Python eAPi for getting outputs in json format
			conn = pyeapi.connect(host=dutslist[i], transport='https')
			temp = conn.execute(['show interfaces status connected'])
			#print temp

			allconnections =temp['result'][0]['interfaceStatuses']
			#print allconnections

			listofconnections= allconnections.keys()
			#print listofconnections

			#Removing management and port-channel interfaces from list
			for k in xrange(0,len(listofconnections)):
				#print listofconnections[k]
				if 'Management' in listofconnections[k] or 'Port-Channel' in listofconnections[k] or '.' in listofconnections[k]:
					listofconnections[k]=None
				#print listofconnections[k]

			#Removing lldp interfaces from ixia interfaces
			for j in xrange(0,len(finalConnectionDetails)):
				#print finalConnectionDetails[i]
			   	if finalConnectionDetails[j]['neighborDevice'] or finalConnectionDetails[j]['myDevice']==dutslist[i]:
			   		if finalConnectionDetails[j]['neighborDevice']==dutslist[i]:
			   			for k in xrange(0,len(listofconnections)):
			   				if listofconnections[k]==('Ethernet'+finalConnectionDetails[j]['neighborPort'].split('Et')[1]):
			   					listofconnections[k]=None
			   		if finalConnectionDetails[j]['myDevice']==dutslist[i]:
			   			for k in xrange(0,len(listofconnections)):
			   				if listofconnections[k]==('Ethernet'+finalConnectionDetails[j]['port'].split('Et')[1]):
			   					listofconnections[k]=None
			
			#print listofconnections

			#Makes a dictionary containing the DUT name and the Ixia ports
			onlyixiaconnections=[]
			for k in xrange(0,len(listofconnections)):
				ixiadict={}
				if listofconnections[k]!=None:
					onlyixiaconnections.append(listofconnections[k])
					ixiadict['neighborDevice']=dutslist[i]
					ixiadict['neighborPort']=('Et'+listofconnections[k].split('Ethernet')[1])
					#print listofconnections[k]
					ixiadict['myDevice']='Ixia' #+'_'+str(randint(0,100))
					ixiadict['port']='unknown'
					ixialist.append(ixiadict)
					#print onlyixiaconnections
		except:
			print "[MESSAGE]: Skipping "+dutslist[i] +" from Ixia connection calculation as well since it is unreachable"
			continue
	
	#print ixialist
	return ixialist

def connectionConsolidator(test):
	connections = {}

	for t in test:
		b = t['myDevice']
		a = t['neighbor']
		p2 = t['port']
		p1 = t['neighbor-port']

		if a+'_'+b not in connections:
		    connections[a+'_'+b] = {'myDevice':a, 'neighbor':b, 'port':[p1], 'neighbor-port':[p2]}
		else:
			connections[a+'_'+b]['port'].append(p1)
			connections[a+'_'+b]['neighbor-port'].append(p2)

	finallist=[]

	for value in connections.values():
		finallist.append(value)

	for i,data in enumerate(finallist):
		data['neighbor-port'].sort()
		startneighborport=data['neighbor-port'][0]
		endneighborport=data['neighbor-port'][-1]

		data['port'].sort()
		startport=data['port'][0]
		endport=data['port'][-1]

		if startneighborport!=endneighborport:
			data['neighbor-port']=startneighborport+'-'+endneighborport.split('Et')[1]
		else:
			data['neighbor-port']=startneighborport
		if startport!=endport:
			data['port']=startport+'-'+endport.split('Et')[1]
		else:
			data['port']=startport

	return finallist

#The below function will print the output in neat format to screen as well as write to a text file
def printConnectionsToScreen(dictionaryOfConnections):

	try:
		f= open("TopologyGenerated.txt","w+")

		logging.info("\n> The topology in text format is: ")
		f.write("\n> The topology in text format is: \n")

		for i in xrange(0,len(dictionaryOfConnections)):
			output= dictionaryOfConnections[i]['neighbor'] + '\t(' + dictionaryOfConnections[i]['neighbor-port'] + ')' + '\t--------------------'  + '\t(' + dictionaryOfConnections[i]['port'] + ')' + dictionaryOfConnections[i]['myDevice']
			f.write(output)
			f.write('\n')
			logging.info(output)

                f.write('\n \n ---Script Generated by topoGen.py SWAT Tool----\n')
		f.close()

	except IOError:
		logging.info("[ERROR]: Permission Denied for generating files in this directory. Please fix it to proceed...")
		abort("* Finished!")
		

	logging.info("\n ---------------------------------------------------------------------------------------------------------------------- \n ")


def automaticGraphGenerator(dictionaryOfConnections, intfInfo):

	# This part below checks the number of DUTs and connections and based on it, it creates containers for the graphviz code
	if len(dictionaryOfConnections)>20:
		graph_string='''
		digraph finite_state_machine {	
		size="8,5"
		node [shape = box];
		rankdir="LR"

		'''
	if len(dictionaryOfConnections)<=20:
		graph_string='''
		digraph finite_state_machine {	
		size="8,5"
		node [shape = box];

		'''	
	
	#The below block is for handling '-' and '.' being present in DUT name since it causes error in graphviz
	for i in xrange(0,len(dictionaryOfConnections)):
		if '-' in dictionaryOfConnections[i]['neighbor'] or '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['neighbor'] or '.' in dictionaryOfConnections[i]['myDevice']:
			if '-' in dictionaryOfConnections[i]['neighbor'] or '.' in dictionaryOfConnections[i]['neighbor']:
				new_str=string.replace(dictionaryOfConnections[i]['neighbor'], '-', '_')
				dictionaryOfConnections[i]['neighbor']=new_str
			if '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['myDevice']:
				new_str=string.replace(dictionaryOfConnections[i]['myDevice'], '-', '_')
				dictionaryOfConnections[i]['myDevice']=new_str

	#The below block is for converting the topology to graphviz format. Adding the connection details to the graphviz container created above
	for i in xrange(0,len(dictionaryOfConnections)):
		if intfInfo:
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice'] + ' [ label = "' + dictionaryOfConnections[i]['neighbor-port'] + '<------>' + dictionaryOfConnections[i]['port'] + '" ]'
		#The below else block is for case when user chose not to include interface labels in topology
		else:
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice']
		graph_string=graph_string+tempvar+'\n'

	graph_string=graph_string+'}'

	logging.info("----------------------------------------------------------------------------")
	logging.info("[MESSAGE] If your device names contains either '.' or '-', it will be replaced by '_' to avoid conflict with other packages\n \n")

	logging.info("> Completed:")

	# The below try-except block is for handling errors in graphviz installation due to all the above dependencies on Mac (linux doesn't have much), I try to install brew and then 'brew install graphviz' since brew (unlike apt-get) is not installed by default.
	try:
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()


	#The below except block is used to install Xcode-Cli tools, brew and graphviz since Mac requires additional dependencies (if not present already)
	except Exception as e:
		logging.info("\n ---------------------------------------------------------------------------------------------------------------------- ")
		logging.info("[ERROR] Looks like we encountered an error. ERROR is:")
		logging.info(e)
		logging.info(" We'll see if installing a few packages fixes it. Please provide your device (Mac/server) password if prompted.")
		logging.info("---------------------------------------------------------------------------------------------------------------------- ")
		#Installing Xcode command-line tools for Mac
		var1= os.system("xcode-select --install")
		#Installing Brew
		var=os.system('''/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"''')
		#Installing Graphviz using brew
		var= os.system("brew install graphviz")
		#This is used to clear the screen ...similar to Ctrl+L in bash
		os.system('tput reset') 


		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()
	

	#The below code block if for opening the editable .gv file using Omnigraffle if it is installed on the user's Mac. Else, skip and print 'Script Complete'	
	try:
		installationcheckcmd="ls /Applications/ | grep -i OmniGraffle"
		returned_value = subprocess.call(installationcheckcmd, shell=True)

		if returned_value==1: #That means OmniGraffle is NOT present
			logging.info("\n [MESSAGE] * The PDF file (graphic topology) and txt file (text) have been generated in current directory! ") #Instead of OmniGraffle not installed message
			abort("* Script Completed!")

		elif returned_value==0: #That means OmniGraffle is present
			logging.info("\t * The PDF file (graphic topology) and txt file (text) have been generated in current directory. Also, OmniGraffle has been opened to edit the GV file (graphic topology). Please choose 'Hierarchial' in OmniGraffle to edit it.")
			subprocess.call(
    			["/usr/bin/open", "-W", "-n", "-a", "/Applications/OmniGraffle.app","Topology.gv"]
    		)

	except:
		abort("* Script Complete!")
		

def graphGeneratorwithLeafSpine(dictionaryOfConnections,intfInfo):

	# This part below checks the number of DUTs and connections and based on it, it creates containers for the graphviz code
	if len(dictionaryOfConnections)>20:
		graph_string='''
		digraph finite_state_machine {	
		node [shape = box];
		rankdir="LR"
		'''

	if len(dictionaryOfConnections)<=20:
		graph_string='''
		digraph finite_state_machine {	
		node [shape = box];
		'''

	nooflevels=raw_input("Please enter the number of levels in your topology. Eg) Leaf-Spine is 2 levels and Leaf-Spine-Superspine is 3 levels. (Enter a integer:) ")

	alreadyadded=[]
	dictoflevels={}

	#The below block is used for getting the levels of DUTs (.ie. whether leaf/spine/super-spine/...) from user
	for i in xrange(1,(int(nooflevels)+1)):
		dictoflevels[i]=[]
	try:
		for i in xrange(0,len(dictionaryOfConnections)):
			if dictionaryOfConnections[i]['neighbor']==dictionaryOfConnections[i]['myDevice']:
				if dictionaryOfConnections[i]['neighbor'] not in alreadyadded:
					alreadyadded.append(dictionaryOfConnections[i]['neighbor'])
					value=raw_input ("Enter the level/hierarchy in range of 1 to "+nooflevels+" (with 1 being lowest) of "+dictionaryOfConnections[i]['neighbor'] +": ")
					dictoflevels[int(value)].append(dictionaryOfConnections[i]['neighbor'])
			else:
				if dictionaryOfConnections[i]['neighbor'] not in alreadyadded:
					alreadyadded.append(dictionaryOfConnections[i]['neighbor'])
					value=raw_input ("Enter the level/hierarchy in range of 1 to "+nooflevels+" (with 1 being lowest) of "+dictionaryOfConnections[i]['neighbor'] +": ")
					dictoflevels[int(value)].append(dictionaryOfConnections[i]['neighbor'])
				if dictionaryOfConnections[i]['myDevice'] not in alreadyadded:
					alreadyadded.append(dictionaryOfConnections[i]['myDevice'])
					value=raw_input ("Enter the level/hierarchy in range of 1 to "+nooflevels+" (with 1 being lowest) of "+dictionaryOfConnections[i]['myDevice'] +": ")
					dictoflevels[int(value)].append(dictionaryOfConnections[i]['myDevice'])		
	except KeyError as e:
		logging.info('[ERROR] The entered value is outside the range of total levels. Please rerun again...')
		abort('* Script Complete')
		

	#The below block is for handling '-' and '.' being present in DUT name since it causes error in graphviz
	for i in xrange(0,len(dictionaryOfConnections)):
		if '-' in dictionaryOfConnections[i]['neighbor'] or '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['neighbor'] or '.' in dictionaryOfConnections[i]['myDevice']:
			if '-' in dictionaryOfConnections[i]['neighbor'] or '.' in dictionaryOfConnections[i]['neighbor']:
				if '-' in dictionaryOfConnections[i]['neighbor']:
					new_str=string.replace(dictionaryOfConnections[i]['neighbor'], '-', '_')
				if '.' in dictionaryOfConnections[i]['neighbor']:
					new_str=string.replace(dictionaryOfConnections[i]['neighbor'], '.', '_')
				dictionaryOfConnections[i]['neighbor']=new_str
			if '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['myDevice']:
				if '-' in dictionaryOfConnections[i]['myDevice']:
					new_str=string.replace(dictionaryOfConnections[i]['myDevice'], '-', '_')
				if '.' in dictionaryOfConnections[i]['myDevice']:
					new_str=string.replace(dictionaryOfConnections[i]['myDevice'], '.', '_')
				dictionaryOfConnections[i]['myDevice']=new_str


	#The below block is for creating containers in Dot language for all the levels 
	for j in reversed(xrange(1,(int(nooflevels)+1))):
		graph_string=graph_string+"\n\nsubgraph level"+str(j) +" {"
		if j==1:
			graph_string=graph_string+'''
			rank=max;
			node[style=filled, shape=box,color=green, fontsize=8];

			'''
		elif j==2:
			if int(nooflevels)==2:
				graph_string=graph_string+'''
				rank=min;
				node[style=filled, shape=box,color=red, fontsize=8];
				'''
			else:
				graph_string=graph_string+'''
				rank=same;
				node[style=filled, shape=box,color=red, fontsize=8];
				'''				
		else:
			graph_string=graph_string+'''
			rank=min;
			node[style=filled, shape=box,color=yellow, fontsize=8];
			'''

		#Adding the devices to each level created above
		for k in xrange(0,len(dictoflevels[j])):

			#Handling '-' or '.' present in the name
			if '-' in dictoflevels[j][k] or '.' in dictoflevels[j][k]: 
				if '-' in dictoflevels[j][k]:
					new_str=string.replace(dictoflevels[j][k], '-', '_')
					dictoflevels[j][k]=new_str
				if '.' in dictoflevels[j][k]:
					new_str=string.replace(dictoflevels[j][k], '.', '_')
					dictoflevels[j][k]=new_str

			graph_string=graph_string+dictoflevels[j][k]+";\n"


		graph_string=graph_string+"}"


	#The below block is used for adding the connections to DUTs for graph generation

	graph_string=graph_string+'''
	subgraph connector{
	'''	
	#The below loop is for converting the topology to graphviz format. Adding the connection details to the graphviz container created above
	for i in xrange(0,len(dictionaryOfConnections)):
		if intfInfo:
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice'] + ' [ label = "' + dictionaryOfConnections[i]['neighbor-port'] + '<------>' + dictionaryOfConnections[i]['port'] + '",labelfontsize=0.5 ]'
		#The below else block is for case when user chose not to include interface labels in topology		
		else:
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice']		
		graph_string=graph_string+tempvar+'\n'

	graph_string=graph_string+'}}'

	logging.info("----------------------------------------------------------------------------")
	logging.info("[MESSAGE] If your device names contains either '.' or '-', it will be replaced by '_' to avoid conflict with other packages")
	logging.info("[MESSAGE] If you get a blank file as output, please verify your choice for device levels. Your choice may have given impossible to comprehend/design for our tool \n \n")

	logging.info("> Completed: \n")

	# The below try-except block is for handling errors in graphviz installation due to all the above dependencies on Mac (linux doesn't have much), I try to install brew and then 'brew install graphviz' since brew (unlike apt-get) is not installed by default.
	try:
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()

	#The below except block is used to install Xcode-Cli tools, brew and graphviz since Mac requires additional dependencies (if not present already)
	except Exception as e:
		logging.info("\n ---------------------------------------------------------------------------------------------------------------------- ")
		logging.info("[ERROR] Looks like we encountered an error. ERROR is:")
		logging.info(e)
		logging.info(" We'll see if installing a few packages fixes it. Please provide your device (Mac/server) password if prompted.")
		logging.info("---------------------------------------------------------------------------------------------------------------------- ")
		#Installing Xcode command-line tools for Mac
		var1= os.system("xcode-select --install")
		#Installing Brew
		var=os.system('''/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"''')
		#Installing Graphviz using brew
		var= os.system("brew install graphviz")
		#This is used to clear the screen ...similar to Ctrl+L in bash
		os.system('tput reset') 


		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()

	#The below code block if for opening the editable .gv file using Omnigraffle if it is installed on the user's Mac. Else, skip and print 'Script Complete'			
	try:
		installationcheckcmd="ls /Applications/ | grep -i OmniGraffle"
		returned_value = subprocess.call(installationcheckcmd, shell=True)

		if returned_value==1: #That means OmniGraffle is NOT present
			logging.info("[MESSAGE] The PDF file (graphic topology) and txt file (text) have been generated in current directory! ") #Instead of OmniGraffle not installed message
			abort("* Script Completed! ")

		elif returned_value==0: #That means OmniGraffle is present
			logging.info("\t * The PDF file (graphic topology) and txt file (text) have been generated in current directory. Also, OmniGraffle has been opened to edit the GV file (graphic topology). Please choose 'Hierarchial' in OmniGraffle to edit it.")
			subprocess.call(
    			["/usr/bin/open", "-W", "-n", "-a", "/Applications/OmniGraffle.app","Topology.gv"]
    		)

	except:
		abort("* Script Complete!")
		

def sendEmailSwatExtension():
	emailChoice=raw_input("Do you need to send the generated files to your email? (yes/no). Unless you want to scp the files out, it is Recommended to type 'yes': " )
	if emailChoice=='no' or emailChoice=='n' or emailChoice=='N':
		return
	else:
		try:
			#Compressing the 3 files into a zip file
			logging.info("---------------------------------------------------------")
			logging.info("[MESSAGE] Compressing the files into zip: ")
			os.system('zip topology_generated.zip TopologyGenerated.txt Topology.gv.pdf Topology.gv')
			logging.info("---------------------------------------------------------\n")

			emailTo=raw_input("Enter your Arista email address (To address): ")
			emailSubj= "Topology generation files- Graphic PDF, Graphic GV and Text"
			emailBody='TopologyGenerated.txt'
			emailAttachment='topology_generated.zip'
			
			#Calling SWAT function to send email
			sendEmail(emailTo=emailTo, emailSubj=emailSubj, emailBody=emailBody, attachments=emailAttachment)
			logging.info("--------------------------------------------------------------------------------------------")
			logging.info("[MESSAGE] Email has been sent successfully if no error is shown above\n")
			logging.info("--------------------------------------------------------------------------------------------\n \n")
			
			return

		except Exception as e:
			logging.info("-------------------------------")
			logging.info("[ERROR]: Error in sending Email. Reason:")
			logging.info(e)
			logging.info("[MESSAGE]: Maybe 'mutt' has not been configured on this device. Skipping sending email and proceeding...\n")
			logging.info("-------------------------------")
			return

#The main function
def mainFunc(username, poolname, filePath, graphrequired, intfInfo, excludeDuts, includeIxiaPorts, consolidateInterfaces):

	#The below part is used to handle cases of username and/or filePathation provided
	if not username and not filePath:
		logging.info("\n \n ----------------------------------------------------------------------------------------------------------------------  \n")
		logging.info(('[MESSAGE]: Username has not been provided. Using file for Topology generation'))
		filePath = os.path.expanduser('~/setup.txt') #Default File location
		logging.info(('[MESSAGE]: Default file at ~/setup.txt is used since custom file locaton as not been provided using -f flag'))
		finalListOfDuts= fileDutList(username, filePath)

	elif not username and filePath:
		logging.info("\n \n ----------------------------------------------------------------------------------------------------------------------  \n")
		logging.info(('[MESSAGE]: Username has not been provided. Using file for Topology generation'))
		finalListOfDuts= fileDutList(username, filePath)
	
	else:
		if filePath:
			logging.info("\n \n ----------------------------------------------------------------------------------------------------------------------  \n")
			logging.info(('[WARNING]: You have provided both a DUTS list file as well as username. Username has higher priority for Topology generation and will be considered. Ignoring the DUT file info...'))

		finalListOfDuts= userDutList(username, poolname) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs


	#This is used to remove the excludeDuts DUTs from the topology generation
	if excludeDuts:
		finalListOfDuts=excludedFromList(finalListOfDuts,excludeDuts)	

	warningMessage() #Will warn users about the list of reasons why the script could fail
	  	
	finalConnectionDetails= lldpInfo(finalListOfDuts) #does the work of grabbing lldp info from all the DUTs, and removing duplicates 

  	#This is used to include Ixia Connections as well based on user flag for ixia
	if not includeIxiaPorts:
		finalConnectionDetails=finalConnectionDetails	
	else:
		listOfIxiaConnections= ixiaConnectionDetailGrabber(finalListOfDuts, finalConnectionDetails) 
		finalConnectionDetails=finalConnectionDetails+listOfIxiaConnections

	#This is used to consolidate the links between same two devices
	if consolidateInterfaces:
		finalConnectionDetails=connectionConsolidator(finalConnectionDetails)		

	printConnectionsToScreen(finalConnectionDetails)

	if not graphrequired:
		logging.info('[MESSAGE]: Graph not generated due to user choice')
		logging.info("* Text file named 'TopologyGenerated.txt' has been created on the same directory containing LLDP info")
		abort('* Script Complete!')
	else:
		while True:
			userchoice = raw_input("Do you have a preference of Leaf-Spine for the DUTs (yes/no)? Type 'no' if you have no clue it means:  ")
			if userchoice=='n' or userchoice=='no' or userchoice=='N':
				automaticGraphGenerator(finalConnectionDetails, intfInfo) #generates a graphical representation with random location of DUTs
				break
			elif userchoice=='y' or userchoice=='yes' or userchoice=='Y':
				graphGeneratorwithLeafSpine(finalConnectionDetails, intfInfo) #generates a graphical representation with location levels chosen by user
				break
			else:
				print ("Please choose one of the above Choices")


if __name__== "__main__":

	#Initialize Variables
	logFile          = os.path.expanduser('~/logs/topoGen.log')
	logOptions       = {'logFile': logFile,
                        'logLevel': 'INFO',
                        'filterList': 'default'}

	# Parsing Options
	parser = argparse.ArgumentParser(description='Used to generate topology incl. ixia connection by taking username as input',formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('-u', '--user', help="Username of user who's topology is needed")
	parser.add_argument('-p', '--pool', default='systest', help='Specify the pool for the above user (default = systest)')
	parser.add_argument('-f', '--file', help='Setup File / DUT List to Load (default = ~/setup.txt)')
	parser.add_argument('-g', '--graph', action='store_false', help= "Add this flag if you DON'T want graph to be generated(default = generated)")
	parser.add_argument('-i', '--ixia', action='store_false', help='Add this flag to exclude Ixia Ports from topology(default = included)')
	parser.add_argument('-c', '--consolidation', action='store_false', help="Add this flag if you DON'T want interfaces between two devices to be grouped/consolidated (default = consolidated)")
	parser.add_argument('-n', '--ifNames', action='store_false', help="Add this flag if you DON'T want interface names to show up in graph (default = interface names are shown)")
	parser.add_argument('-x', '--exclude',nargs='+', help='Exclude the following DUTs during topology formation')
	options = parser.parse_args()

    # Logging
	logOptions['logLevel'] = logOptions['logLevel']
	logLib.Config(**logOptions)

	mainFunc(options.user, options.pool, options.file, options.graph, options.ifNames, options.exclude, options.ixia, options.consolidation)
