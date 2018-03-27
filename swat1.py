# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#!/usr/bin/env python

#Python Module Imports
import sys
import os
import time
import string
import argparse
import socket
import subprocess
from random import randint
import re
import collections

#Non-SWAT and non-default Python libraries that are additionally needed by this script
import graphviz
from graphviz import Source #Make a topology graph

#SWAT Module Imports
from proxyLib import Proxy, checkProxySession
#from labLib import findDuts   #Doesn't work due to oauth2client version issue...using proxylib to run Art command directly
from clientLib import sendEmail
from initToolLib import connectDevices
from eosLldp import EosLldp
from eosIntf import EosIntf

def fileDutList(username,filePath):
	try:

		listofdutsasperfile=[]
		temp=[]

		file = open(filePath)
		listofdutsasperfile = file.readlines()

		for i,data in enumerate(listofdutsasperfile):
			if '#' in data[0] or '\n' in data[0]:
				listofdutsasperfile[i]=None
		#print listofdutsasperfile

		for i,data in enumerate(listofdutsasperfile):
			if data!=None:
				temp.append(data.strip())
		#print temp

		print "\n > List of DUTS as per the file provided is:"
		print "\t * "+str(temp)
		return temp
	except IOError:
		print "\n[ERROR]: File does not exist in "+filePath+" . Please ensure correct file location to proceed \n"
		sys.exit(1)

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

"""
# Below function will be used when oauth2Client version mis-match issue is fixed on arst1/arst2 server

#The below function uses SWAT tool to get duts list from Art
def userDutList(username,poolname):

	print "----------------------------------------------------------------------------------"
	#print "[WARNING] If you haven't setup the SSH Keys for Syscon (required by SWAT tool libraries), you will be prompted to type 'YES' and provide your Syscon password. If you do not wish for the Swat script to do that for you, fix it yourself when prompted! \n "
	#print '''[MESSAGE] If you are getting any "Exception raised in 'python /usr/bin/Art list --pool=systest '", then, it is due to Art commands are failing from the server in which you are running this script... Contact @syscon-maintainers '''
	print "[MESSAGE] SWAT library to read from rdam takes time sometimes...Please be patient"
	print "----------------------------------------------------------------------------------"
	alldevices=findDuts(pool=poolname, all=True)

	devices=alldevices.items()

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
"""

def excludedFromList(finalListOfDuts,excludeDuts):
	#Removing the matches using intersections
	ss= set(finalListOfDuts)
	fs =set(excludeDuts)

	finallist= list(ss.union(ss)  - ss.intersection(fs))
	
	print "\n > Excluding specified devices from topology. Topology will be generated for: "
	print "\t * "+str(finallist)

	return finallist

def warningMessage():
	print"\n !!! INFORMATIONAL WARNING !!! "
	print "This script will not include interfaces that are shut or errdisabled. If you need to include even those, make sure they are Up."
	print"\n !!! LLDP WARNING !!! "
	print "This script assumes that all lldp devices are shown in typical format of 'hostname.sjc.aristanetworks.com'. Untypical lldp info such as mac address will give out unsupported error, please address it if you are shown that error."
	print"\n !!! OUTPUT WARNING !!! "
	print "This script will consider all non-LLDP supported neighbors (such as linux servers) as Ixia connections only. \n"

def lldpInfo(dutslist):
	
#************************************************************************
#The below code will grab lldp info from all DUTs in json format and refine it and
#it will consolidate all the lldp information into a single dictionary

	tempDictOfConnections=[]

  	#The below try and except block will handle errors due to eAPI not enabled on one of the DUT
	for i in xrange(0,len(dutslist)):
		
		#Getting LLDP info using SWAT library function
		print "[MESSAGE]: Getting LLDP info from "+dutslist[i]
		a=connectDevices(dutslist[i])
		a,=a
		temp = a.getLldpInfo()
		#print temp

		allneighbors =temp['neighbors']
		#print allneighbors

		for j in xrange(0,len(allneighbors)):
			temp_diction = allneighbors[j]
			temp_diction['myDevice']=str(dutslist[i]) #+'.sjc.aristanetworks.com'
			tempDictOfConnections.append(temp_diction)
			#print temp_diction

		tempDictOfConnections = tempDictOfConnections[:-1]
		#print tempDictOfConnections	

	#************************************************************************
	#The below code will remove the duplicates from the grand dictionary such that one connection shows up only once. The duplicates are marked as key=temp and value=NULL

	for i in xrange(0,len(tempDictOfConnections)):
		tempvar= tempDictOfConnections[i] #Storing each dictionary in one temp variable
		#print tempvar
		#print '\n'
		instantaneoustempvar= []
		instantaneoustempvar=[tempvar['neighbor'],tempvar['neighbor-port']]
		tempvar['neighbor']= tempvar['myDevice']
		tempvar['neighbor-port']= tempvar['port']
		tempvar['myDevice']=instantaneoustempvar[0]
		tempvar['port']=instantaneoustempvar[1]
		#print tempvar

		count=0
		for j in xrange(0,len(tempDictOfConnections)):
			if tempvar == tempDictOfConnections[j]:
				count=count+1

		if count==2:
			tempDictOfConnections[i]={'temp':'Null'}

	#print tempDictOfConnections
	
	#************************************************************************
	#The below code will remove the duplicates completely by removing dictionaries with key as temp. ALso, removing the '.sjc.aristanetworks.com' in DUT name

	dictionaryOfConnections=[] #This list will have only non-duplicate values

	for i in xrange(0,len(tempDictOfConnections)):
		if tempDictOfConnections[i].get('temp')== None:
			tempDictOfConnections[i]['neighbor']=tempDictOfConnections[i]['neighbor'].split('.')[0]
			tempDictOfConnections[i]['myDevice']=tempDictOfConnections[i]['myDevice'].split('.')[0]
			try:
				tempDictOfConnections[i]['port']='Et'+(tempDictOfConnections[i]['port'].split('Et')[1])
			except:
				print "[ERROR]: One of your lldp neighbors is not in typical format. Read above LLDP Warning on how to fix it and then rerun the script"
				print "* Script Complete!"
				sys.exit(1)
			tempDictOfConnections[i]['neighbor-port']='Et'+(tempDictOfConnections[i]['neighbor-port'].split('Et')[1])
			dictionaryOfConnections.append(tempDictOfConnections[i])

	return dictionaryOfConnections

def ixiaConnectionDetailGrabber(dutslist,finalConnectionDetails):
	
#************************************************************************
#The below code will grab lldp info from all DUTs in json format and refine it and
#it will consolidate all the lldp information into a single dictionary

	#print finalConnectionDetails

	ixialist=[]

	for i in xrange(0,len(dutslist)):
	
		try:	
			#Getting Connected Interfaces info using SWAT library function
			a=connectDevices(dutslist[i])
			a,=a
			a.setAccessMethod('api')
			temp = a.getConnectedIntfs()
			#print temp

			allconnections =temp
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
			   	if finalConnectionDetails[j]['neighbor'] or finalConnectionDetails[j]['myDevice']==dutslist[i]:
			   		if finalConnectionDetails[j]['neighbor']==dutslist[i]:
			   			for k in xrange(0,len(listofconnections)):
			   				if listofconnections[k]==('Ethernet'+finalConnectionDetails[j]['neighbor-port'].split('Et')[1]):
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
					ixiadict['neighbor']=dutslist[i]
					ixiadict['neighbor-port']=('Et'+listofconnections[k].split('Ethernet')[1])
					#print listofconnections[k]
					ixiadict['myDevice']='Ixia' #+'_'+str(randint(0,100))
					ixiadict['port']='unknown'
					ixialist.append(ixiadict)
					#print onlyixiaconnections
		except:
			print "[MESSAGE]: Skipping "+dutslist[i] +" from Ixia connection calculation due to some error"
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

	#print connections

	finallist=[]

	for value in connections.values():
		finallist.append(value)

	#print finallist

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

	#print finallist
	return finallist

def printConnectionsToScreen(dictionaryOfConnections):
	#************************************************************************
	#The below code will print the output in neat format

	try:
		f= open("TopologyGenerated.txt","w+")

		print "\n> The topology in text format is: "
		f.write("\n> The topology in text format is: \n")

		for i in xrange(0,len(dictionaryOfConnections)):
			output= dictionaryOfConnections[i]['neighbor'] + '\t(' + dictionaryOfConnections[i]['neighbor-port'] + ')' + '\t--------------------'  + '\t(' + dictionaryOfConnections[i]['port'] + ')' + dictionaryOfConnections[i]['myDevice']
			f.write(output)
			f.write('\n')
			print output

                f.write('\n \n ---Script Generated by topoGen.py SWAT Tool----\n')
		f.close()

	except IOError:
		print "[ERROR]: Permission Denied for generating files in this directory. Please fix it to proceed..."
		print "* Finished!"
		sys.exit(1)

	print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
	#print "Presented to you by anandgokul. Ping me if any errors/ exceptions are encountered that I missed handling...Sayonara! :D \n \n"


def automaticGraphGenerator(dictionaryOfConnections, intfInfo):

	print "[MESSAGE] Ignore on Linux. On macOS, ignore unless prompted for Xcode tools installation:"
	print "----------------------------------------------------------------------------"
	var1= os.system("xcode-select --install")
	var= os.system("brew install graphviz")
	print "----------------------------------------------------------------------------"

	os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash

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
	
	#The below block is for handling '-' and '.' being present in DUT name
	for i in xrange(0,len(dictionaryOfConnections)):
		if '-' in dictionaryOfConnections[i]['neighbor'] or '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['neighbor'] or '.' in dictionaryOfConnections[i]['myDevice']:
			if '-' in dictionaryOfConnections[i]['neighbor'] or '.' in dictionaryOfConnections[i]['neighbor']:
				new_str=string.replace(dictionaryOfConnections[i]['neighbor'], '-', '_')
				dictionaryOfConnections[i]['neighbor']=new_str
			if '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['myDevice']:
				new_str=string.replace(dictionaryOfConnections[i]['myDevice'], '-', '_')
				dictionaryOfConnections[i]['myDevice']=new_str

	#The below block is for converting the topology to graphviz format
	for i in xrange(0,len(dictionaryOfConnections)):
		if intfInfo=='yes':
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice'] + ' [ label = "' + dictionaryOfConnections[i]['neighbor-port'] + '<------>' + dictionaryOfConnections[i]['port'] + '" ]'
		else:
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice']
		graph_string=graph_string+tempvar+'\n'

	graph_string=graph_string+'}'
	#print graph_string

	print "----------------------------------------------------------------------------"
	print "[MESSAGE] If your device names contains either '.' or '-', it will be replaced by '_' to avoid conflict with other packages\n \n"

	print "> Completed Successfully: "
	#print "There is both a readily-available pdf file as well as a .gv file which can be imported to graphing tools like OmniGraffle for further editing(get license for Omnigraffle from helpdesk..:/\n"
	try:
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()
	except Exception as e:
		print e
		print"\n ---------------------------------------------------------------------------------------------------------------------- "
		print "[ERROR] Looks like we encountered an error. We'll see if installing a package fixes it. Please provide your mac password if prompted"
		print"---------------------------------------------------------------------------------------------------------------------- "
		var=os.system('''/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"''')
		var= os.system("brew install graphviz")
		os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()
		
	try:
		installationcheckcmd="ls /Applications/ | grep -i OmniGraffle"
		returned_value = subprocess.call(installationcheckcmd, shell=True)

		if returned_value==1: #That means OmniGraffle is NOT present
			print "\n [MESSAGE] * The PDF file (graphic topology) and txt file (text) have been generated in current directory! " #Instead of OmniGraffle not installed message
			print "* Script Completed!"

		elif returned_value==0: #That means OmniGraffle is present
			print "\t * The PDF file (graphic topology) and txt file (text) have been generated in current directory. Also, OmniGraffle has been opened to edit the GV file (graphic topology). Please choose 'Hierarchial' in OmniGraffle to edit it."
			subprocess.call(
    			["/usr/bin/open", "-W", "-n", "-a", "/Applications/OmniGraffle.app","Topology.gv"]
    		)

	except:
		print "* Script Complete!"
		sys.exit(1)

def graphGeneratorwithLeafSpine(dictionaryOfConnections,intfInfo):

	print "[MESSAGE] Ignore on Linux. On macOS, ignore unless prompted for Xcode tools installation:"
	print "----------------------------------------------------------------------------"
	var1= os.system("xcode-select --install")
	var= os.system("brew install graphviz")
	print "----------------------------------------------------------------------------"

	os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash

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

	for i in xrange(1,(int(nooflevels)+1)):
		dictoflevels[i]=[]
	#print dictoflevels

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
			#print alreadyadded
		
	except KeyError as e:
		print '[ERROR] The entered value is outside the range of total levels. Please rerun again...'
		print '* Script Complete'
		sys.exit(1)
	#print dictoflevels


	#The below block is for handling '-' and '.' being present in DUT name
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

		#Adding the devices to each level
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

	#print graph_string

	#The below is generic connector code
	graph_string=graph_string+'''
	subgraph connector{
	'''	

	#The below block is for converting the topology to graphviz format
	for i in xrange(0,len(dictionaryOfConnections)):
		if intfInfo=='yes':
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice'] + ' [ label = "' + dictionaryOfConnections[i]['neighbor-port'] + '<------>' + dictionaryOfConnections[i]['port'] + '",labelfontsize=0.5 ]'
		else:
			tempvar=dictionaryOfConnections[i]['neighbor'] + ' -> ' + dictionaryOfConnections[i]['myDevice']		
		graph_string=graph_string+tempvar+'\n'

	graph_string=graph_string+'}}'
	#print graph_string

	print "----------------------------------------------------------------------------"
	print "[MESSAGE] If your device names contains either '.' or '-', it will be replaced by '_' to avoid conflict with other packages"
	print "[MESSAGE] If you get a blank file as output, please verify your includeIxiaPorts for device levels. Your includeIxiaPorts may have given impossible to comprehend/design for our tool \n \n"

	print "> Completed successfully: \n"

	#print "There is both a readily-available pdf file as well as a .gv file which can be imported to graphing tools like OmniGraffle for further editing(get license for Omnigraffle from helpdesk..:/\n"
	try:
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()

	except:
		print"\n ---------------------------------------------------------------------------------------------------------------------- "
		print "[ERROR] Looks like we encountered an error. We'll see if installing a package fixes it. Please provide your mac password if prompted"
		print"---------------------------------------------------------------------------------------------------------------------- "
		var=os.system('''/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"''')
		var= os.system("brew install graphviz")
		os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()

		#Send Email with the script
		sendEmailSwatExtension()
		
	try:
		installationcheckcmd="ls /Applications/ | grep -i OmniGraffle"
		returned_value = subprocess.call(installationcheckcmd, shell=True)

		if returned_value==1: #That means OmniGraffle is NOT present
			print "[MESSAGE] The PDF file (graphic topology) and txt file (text) have been generated in current directory! " #Instead of OmniGraffle not installed message
			print "* Script Completed! "

		elif returned_value==0: #That means OmniGraffle is present
			print "\t * The PDF file (graphic topology) and txt file (text) have been generated in current directory. Also, OmniGraffle has been opened to edit the GV file (graphic topology). Please choose 'Hierarchial' in OmniGraffle to edit it."
			subprocess.call(
    			["/usr/bin/open", "-W", "-n", "-a", "/Applications/OmniGraffle.app","Topology.gv"]
    		)

	except:
		print "* Script Complete!"
		sys.exit(1)

def sendEmailSwatExtension():
	emailChoice=raw_input("Do you need to send the generated files to your email? (yes/no). Unless you want to scp the files out, it is Recommended to type 'yes': " )
	if emailChoice=='no' or emailChoice=='n' or emailChoice=='N':
		return
	else:
		try:
			#Compressing the 3 files into a zip file
			print "---------------------------------------------------------"
			print "[MESSAGE] Compressing the files into zip: "
			os.system('zip topology_generated.zip TopologyGenerated.txt Topology.gv.pdf Topology.gv')
			print "---------------------------------------------------------\n"

			emailTo=raw_input("Enter your Arista email address (To address): ")
			emailSubj= "Topology generation files- Graphic PDF, Graphic GV and Text"
			emailBody='TopologyGenerated.txt'
			emailAttachment='topology_generated.zip'
			
			#SWAT function to send email...did not support attachment...hence commenting this
			sendEmail(emailTo=emailTo, emailSubj=emailSubj, emailBody=emailBody, attachments=emailAttachment)
			print "--------------------------------------------------------------------------------------------"
			print "[MESSAGE] Email has been sent successfully if no error is shown above\n"
			print "--------------------------------------------------------------------------------------------\n \n"
			
			#Sending Email using this script instead of SWAT tool
			#mailCmd='''mutt -s "%s" -a %s < %s -- %s'''%(emailSubj, emailAttachment, emailBody, emailTo)
            #            os.system(mailCmd)
			#print "--------------------------------------------------------------------------------------------"
			#print "[MESSAGE] Email will be sent if mutt had been setup correctly. If you haven't done this, run this from arst or syscon servers since thay are already configured with mutt.\n"
			#print "--------------------------------------------------------------------------------------------\n \n"
			
			return

		except Exception as e:
			print "-------------------------------"
			print "[ERROR]: Error in sending Email. Reason:"
			print e
			print "[MESSAGE]: Maybe 'mutt' has not been configured on this device. Skipping sending email and proceeding...\n"
			print "-------------------------------"
			return

#The main function
def mainFunc(username, poolname, filePath, graphrequired, intfInfo, excludeDuts, includeIxiaPorts, consolidateInterfaces):

	#The below part is used to handle cases of username and/or filePathation provided
	if not username and not filePath:
		print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
		print ('[MESSAGE]: Username has not been provided. Using file for Topology generation')
		filePath = os.path.expanduser('~/setup.txt') #Default File location
		print ('[MESSAGE]: Default file at ~/setup.txt is used since custom file locaton as not been provided using -f flag')
		finalListOfDuts= fileDutList(username, filePath)

	elif not username and filePath:
		print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
		print ('[MESSAGE]: Username has not been provided. Using file for Topology generation')
		finalListOfDuts= fileDutList(username, filePath)
	
	else:
		if filePath:
			print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
			print ('[WARNING]: You have provided both a DUTS list file as well as username. Username has higher priority for Topology generation and will be considered. Ignoring the DUT file info...')

		finalListOfDuts= userDutList(username, poolname) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs

		

	#This is used to remove the excludeDuts DUTs from the topology generation
	if excludeDuts:
		finalListOfDuts=excludedFromList(finalListOfDuts,excludeDuts)

	

	warningMessage() #Will warn users about the list of reasons why the script could fail
	  	
	
	finalConnectionDetails= lldpInfo(finalListOfDuts) #does the work of grabbing lldp info from all the DUTs, and removing duplicates 
  	#print finalConnectionDetails
	

  	#This is used to include Ixia Connections as well based on user flag for ixia
	if includeIxiaPorts=='n' or includeIxiaPorts=='N' or includeIxiaPorts=='no':
		finalConnectionDetails=finalConnectionDetails	
	else:
		listOfIxiaConnections= ixiaConnectionDetailGrabber(finalListOfDuts, finalConnectionDetails) 
		finalConnectionDetails=finalConnectionDetails+listOfIxiaConnections
		#print finalConnectionDetails 
	#print finalConnectionDetails

	#This is used to consolidate the links between same two devices
	if consolidateInterfaces=='yes':
		finalConnectionDetails=connectionConsolidator(finalConnectionDetails)		

	printConnectionsToScreen(finalConnectionDetails)


	if graphrequired=='no' or graphrequired=='n':
		print '[MESSAGE]: Graph not generated due to user choice'
		print "* Text file named 'TopologyGenerated.txt' has been created on the same directory containing LLDP info"
		print '* Script Complete!'
	else:
		while True:
			includeIxiaPorts = raw_input("Do you have a preference of Leaf-Spine for the DUTs (yes/no)? Type 'no' if you have no clue it means:  ")
			if includeIxiaPorts=='n' or includeIxiaPorts=='N' or includeIxiaPorts=='no':
				automaticGraphGenerator(finalConnectionDetails, intfInfo) #generates a graphical representation with random location of DUTs
				break
			elif includeIxiaPorts=='y' or includeIxiaPorts=='Y' or includeIxiaPorts=='yes':
				graphGeneratorwithLeafSpine(finalConnectionDetails, intfInfo) #generates a graphical representation with location levels chosen by user
				break
			else:
				print ("Please choose one of the above includeIxiaPortss")


if __name__== "__main__":

	# Parsing Options
    parser = argparse.ArgumentParser(description='Used to generate topology incl. ixia connection by taking username as input',formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-u', '--user', help="Username of user who's topology is needed")
    parser.add_argument('-p', '--pool', default='systest', help='Specify the pool for the above user (default = systest)')
    parser.add_argument('-f', '--file', help='Setup File / DUT List to Load (default = ~/setup.txt)')
    parser.add_argument('-g', '--graph', help='mention (yes/no) for graph generation (default = yes)')
    parser.add_argument('-i', '--ixia', default='yes', help='mention (yes/no) whether to include even ports connected to ixia (this is best effort)(default = yes)')
    parser.add_argument('-c', '--consolidation', default='yes', help='mention (yes/no) whether to group interfaces between two devices together (default = yes)')
    parser.add_argument('-n', '--ifNames', default='yes', help='mention (yes/no) whether you need the interface names in topology(default = yes)')
    parser.add_argument('-x', '--exclude',nargs='+', help='Exclude the following DUTs during topology formation')
    options = parser.parse_args()

mainFunc(options.user, options.pool, options.file, options.graph, options.ifNames, options.exclude, options.ixia, options.consolidation)
