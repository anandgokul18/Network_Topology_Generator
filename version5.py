# Copyright (c) 2015 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#!/usr/bin/python

'''
THIS IS A HACK TO OVERCOME THE CATCH-22 SITUATION IN SERVERS WHEREIN ART TOOLS REQUIRES oauth2client AS V1.5.1, BUT, SWAT LIBRARIES REQUIRES V4.1.2
'''
import os
os.system("virtualenv . --system-site-package") #Creating a virtual environment *R1
os.system("source ./bin/activate")
print "--------------------------------------------------------------"
print "[MESSAGE] We need to install a few packages and setup virtualenv for this script...Hold on. Provide your current device/server password if prompted to install the packages"
print "--------------------------------------------------------------"

#Python Module Imports
import pexpect #SSH library with expect support
import sys
import os
import time
import string
import argparse
import socket
import subprocess
from random import randint

#Non-SWAT and non-default Python libraries that are additionally needed by this script
try:
	import paramiko
	from graphviz import Source #Make a topology graph
	import pyeapi #eApi support
except ImportError:
	print "[ERROR] Some packages are missing/ out-of-date...Please provide the password (if prompted) for running install using sudo"
	print "--------------------------------------------------------------"
	#Installing these packages globally since they will not break any other existing function
	os.system('sudo pip install paramiko')
	os.system('sudo pip install graphviz')
	os.system('sudo pip install pyeapi')
	print "--------------------------------------------------------------"
	import paramiko
	from graphviz import Source #Make a topology graph
	import pyeapi #eApi support



#SWAT Module Imports

os.system("sudo pip install oauth2client==4.1.2")  #hack for fulfilling import requirements of labLib *R1
import labLib
from labLib import findDuts
import clientLib
from clientLib import sendEmail
os.system("sudo pip install oauth2client==1.5.1")  #hack for fulfilling import requirements of labLib.findDuts *R1


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
def userDutList(username,poolname):

	print "----------------------------------------------------------------------------------"
	print "[WARNING] If you haven't setup the SSH Keys for Syscon (required by SWAT tool libraries), you will be prompted to type 'YES' and provide your Syscon password. If you do not wish for the Swat script to do that for you, fix it yourself when prompted! \n "
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
		try:
		   #Using Python eAPi for getting outputs in json format
		   conn = pyeapi.connect(host=dutslist[i], transport='https')
		   temp = conn.execute(['show lldp neighbors'])
		   #print temp

		   allneighbors =temp['result'][0]['lldpNeighbors']
		   #print allneighbors

		   for j in xrange(0,len(allneighbors)):
		   	temp_diction = allneighbors[j]
		   	temp_diction['myDevice']=str(dutslist[i])+'.sjc.aristanetworks.com'
		   	tempDictOfConnections.append(temp_diction)
		   	#print temp_diction

		   tempDictOfConnections = tempDictOfConnections[:-1]
		   #print tempDictOfConnections	

		except pyeapi.eapilib.ConnectionError as e:
	  		print "\n[Please Wait]: eApi is not enabled on one of your devices namely:<-- "+dutslist[i]+"-->. Hold on while we do that for you \n"
	  		
	  		reachabilityFlag=func_eapi_enabler(dutslist[i]) #The return flag '1' is used to skip that device since it was not reachable in first place. If flag=0, then, we can do the below

	  		if reachabilityFlag==1:
	  			continue
	  		else:
		  		try:
					#Same as above: Using Python eAPi for getting outputs in json format
					conn = pyeapi.connect(host=dutslist[i], transport='https')
					temp = conn.execute(['show lldp neighbors'])
					#print temp

					allneighbors =temp['result'][0]['lldpNeighbors']
					#print allneighbors

					for j in xrange(0,len(allneighbors)):
						temp_diction = allneighbors[j]
						temp_diction['myDevice']=str(dutslist[i])+'.sjc.aristanetworks.com'
						tempDictOfConnections.append(temp_diction)
					#print temp_diction

					tempDictOfConnections = tempDictOfConnections[:-1]

					#print tempDictOfConnections

				except:
					print "[ERROR] Enabling eApi automatically failed. Please enable eApi manually on "+dutslist[i]+ " by doing 'management api http-commands' --> 'no shut' and then rerun the script"
					print "* Script Complete!"
					sys.exit(1)

	#************************************************************************
	#The below code will remove the duplicates from the grand dictionary such that one connection shows up only once. The duplicates are marked as key=temp and value=NULL

	for i in xrange(0,len(tempDictOfConnections)):
		tempvar= tempDictOfConnections[i] #Storing each dictionary in one temp variable
		#print tempvar
		#print '\n'
		instantaneoustempvar= []
		instantaneoustempvar=[tempvar['neighborDevice'],tempvar['neighborPort']]
		tempvar['neighborDevice']= tempvar['myDevice']
		tempvar['neighborPort']= tempvar['port']
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
			tempDictOfConnections[i]['neighborDevice']=tempDictOfConnections[i]['neighborDevice'].split('.')[0]
			tempDictOfConnections[i]['myDevice']=tempDictOfConnections[i]['myDevice'].split('.')[0]
			try:
				tempDictOfConnections[i]['port']='Et'+(tempDictOfConnections[i]['port'].split('Ethernet')[1])
			except:
				print "[ERROR]: One of your lldp neighbors is not in typical format. Read above LLDP Warning on how to fix it and then rerun the script"
				print "* Script Complete!"
				sys.exit(1)
			tempDictOfConnections[i]['neighborPort']='Et'+(tempDictOfConnections[i]['neighborPort'].split('Ethernet')[1])
			dictionaryOfConnections.append(tempDictOfConnections[i])


	#Below Code will try to consolidate interfaces in series
	#for i in xrange(0,len(tempDictOfConnections)):


	return dictionaryOfConnections

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

def func_eapi_enabler(dutname):
	#************************************************************************
	#The below code will enable eApi on all the DUTs in above list

	try:
		ipaddr= socket.gethostbyname(dutname)
		username='admin'
		password=''

		initproc=paramiko.SSHClient()
		initproc.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		initproc.connect(ipaddr, username=username, password=password)
		
		workproc=initproc.invoke_shell()

		output=workproc.recv(65535)
		#print output

		#Setting Pagination disabled
		workproc.send("\n ter len 0 \n") 
		workproc.send('en \n conf \n')
		workproc.send('default management api http \n')
		time.sleep(5)
		workproc.send('management api http \n')
		workproc.send("\n no shut \n")
		output=workproc.recv(65535)
		#print output
		initproc.close()
		print '[MESSAGE] We are still trying to enable eApi on '+dutname+'\n'
		return 0

	except socket.error:
		print "[ERROR]: Device "+dutname +" is unreachable. \n"
		continueOrStop=raw_input('Do you want to skip this device and proceed with other devices? (yes/no): ')
		if continueOrStop=='yes' or continueOrStop=='y':
			return 1
		else:
			print "* DUT unreachable.\n * Script Finished!"
			sys.exit(1)

def connectionConsolidator(test):
	connections = {}

	for t in test:
		b = t['myDevice']
		a = t['neighborDevice']
		p2 = t['port']
		p1 = t['neighborPort']

		if a+'_'+b not in connections:
		    connections[a+'_'+b] = {'myDevice':a, 'neighborDevice':b, 'port':[p1], 'neighborPort':[p2]}
		else:
			connections[a+'_'+b]['port'].append(p1)
			connections[a+'_'+b]['neighborPort'].append(p2)

	#print connections

	finallist=[]

	for value in connections.values():
		finallist.append(value)

	#print finallist

	for i,data in enumerate(finallist):
		data['neighborPort'].sort()
		startNeighborPort=data['neighborPort'][0]
		endNeighborPort=data['neighborPort'][-1]

		data['port'].sort()
		startport=data['port'][0]
		endport=data['port'][-1]

		if startNeighborPort!=endNeighborPort:
			data['neighborPort']=startNeighborPort+'-'+endNeighborPort.split('Et')[1]
		else:
			data['neighborPort']=startNeighborPort
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
			output= dictionaryOfConnections[i]['neighborDevice'] + '\t(' + dictionaryOfConnections[i]['neighborPort'] + ')' + '\t--------------------'  + '\t(' + dictionaryOfConnections[i]['port'] + ')' + dictionaryOfConnections[i]['myDevice']
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
		if '-' in dictionaryOfConnections[i]['neighborDevice'] or '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['neighborDevice'] or '.' in dictionaryOfConnections[i]['myDevice']:
			if '-' in dictionaryOfConnections[i]['neighborDevice'] or '.' in dictionaryOfConnections[i]['neighborDevice']:
				new_str=string.replace(dictionaryOfConnections[i]['neighborDevice'], '-', '_')
				dictionaryOfConnections[i]['neighborDevice']=new_str
			if '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['myDevice']:
				new_str=string.replace(dictionaryOfConnections[i]['myDevice'], '-', '_')
				dictionaryOfConnections[i]['myDevice']=new_str

	#The below block is for converting the topology to graphviz format
	for i in xrange(0,len(dictionaryOfConnections)):
		if intfInfo=='yes':
			tempvar=dictionaryOfConnections[i]['neighborDevice'] + ' -> ' + dictionaryOfConnections[i]['myDevice'] + ' [ label = "' + dictionaryOfConnections[i]['neighborPort'] + '<------>' + dictionaryOfConnections[i]['port'] + '" ]'
		else:
			tempvar=dictionaryOfConnections[i]['neighborDevice'] + ' -> ' + dictionaryOfConnections[i]['myDevice']
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
			if dictionaryOfConnections[i]['neighborDevice']==dictionaryOfConnections[i]['myDevice']:
				if dictionaryOfConnections[i]['neighborDevice'] not in alreadyadded:
					alreadyadded.append(dictionaryOfConnections[i]['neighborDevice'])
					value=raw_input ("Enter the level/hierarchy in range of 1 to "+nooflevels+" (with 1 being lowest) of "+dictionaryOfConnections[i]['neighborDevice'] +": ")
					dictoflevels[int(value)].append(dictionaryOfConnections[i]['neighborDevice'])
			else:
				if dictionaryOfConnections[i]['neighborDevice'] not in alreadyadded:
					alreadyadded.append(dictionaryOfConnections[i]['neighborDevice'])
					value=raw_input ("Enter the level/hierarchy in range of 1 to "+nooflevels+" (with 1 being lowest) of "+dictionaryOfConnections[i]['neighborDevice'] +": ")
					dictoflevels[int(value)].append(dictionaryOfConnections[i]['neighborDevice'])
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
		if '-' in dictionaryOfConnections[i]['neighborDevice'] or '-' in dictionaryOfConnections[i]['myDevice'] or '.' in dictionaryOfConnections[i]['neighborDevice'] or '.' in dictionaryOfConnections[i]['myDevice']:
			if '-' in dictionaryOfConnections[i]['neighborDevice'] or '.' in dictionaryOfConnections[i]['neighborDevice']:
				if '-' in dictionaryOfConnections[i]['neighborDevice']:
					new_str=string.replace(dictionaryOfConnections[i]['neighborDevice'], '-', '_')
				if '.' in dictionaryOfConnections[i]['neighborDevice']:
					new_str=string.replace(dictionaryOfConnections[i]['neighborDevice'], '.', '_')
				dictionaryOfConnections[i]['neighborDevice']=new_str
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
			tempvar=dictionaryOfConnections[i]['neighborDevice'] + ' -> ' + dictionaryOfConnections[i]['myDevice'] + ' [ label = "' + dictionaryOfConnections[i]['neighborPort'] + '<------>' + dictionaryOfConnections[i]['port'] + '",labelfontsize=0.5 ]'
		else:
			tempvar=dictionaryOfConnections[i]['neighborDevice'] + ' -> ' + dictionaryOfConnections[i]['myDevice']		
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
			#sendEmail(emailTo=emailTo, emailSubj=emailSubj, emailBody=emailBody)
			
			#Sending Email
			mailCmd='''mutt -s "%s" -a %s < %s -- %s'''%(emailSubj, emailAttachment, emailBody, emailTo)
                        os.system(mailCmd)

			print "--------------------------------------------------------------------------------------------"
			print "[MESSAGE] Email will be sent if mutt had been setup correctly. If you haven't done this, run this from arst or syscon servers since thay are already configured with mutt.\n"
			print "--------------------------------------------------------------------------------------------\n \n"
			
			os.system("deactivate")   #Deactivating the virtual environment created *R1
			return

		except Exception as e:
			print "-------------------------------"
			print "[ERROR]: Error in sending Email. Reason:"
			print e
			print "-------------------------------"
			print "[MESSAGE]: Skipping sending email and proceeding...\n"
			return

#The main function
def main(username, poolname, filePath, graphrequired, intfInfo, excludeDuts, includeIxiaPorts, consolidateInterfaces):

	#The below part is used to handle cases of username and/or filePathation provided
	if username==None and filePath==None:
		print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
		print ('[MESSAGE]: Username has not been provided. Using file for Topology generation')
		filePath = os.path.expanduser('~/setup.txt') #Default File location
		print ('[MESSAGE]: Default file at ~/setup.txt is used since custom file locaton as not been provided using -f flag')
		finalListOfDuts= fileDutList(username, filePath)

	elif username==None and filePath!=None:
		print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
		print ('[MESSAGE]: Username has not been provided. Using file for Topology generation')
		finalListOfDuts= fileDutList(username, filePath)
	
	else:
		if filePath!=None:
			print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
			print ('[WARNING]: You have provided both a DUTS list file as well as username. Username has higher priority for Topology generation and will be considered. Ignoring the DUT file info...')
		finalListOfDuts= userDutList(username, poolname) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs

		

	#This is used to remove the excludeDuts DUTs from the topology generation
	if excludeDuts!=None:
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
    parser.add_argument('-n', '--namesofinterfaces', default='yes', help='mention (yes/no) whether you need the interface names in topology(default = yes)')
    parser.add_argument('-x', '--exclude',nargs='+', help='Exclude the following DUTs during topology formation')
    options = parser.parse_args()

#Assigning the arguments to variables
username=options.user
poolname=options.pool
filePath=options.file
graphrequired=options.graph
includeIxiaPorts=options.ixia
consolidateInterfaces=options.consolidation
intfInfo=options.namesofinterfaces
excludeDuts=options.exclude

main(username, poolname, filePath, graphrequired, intfInfo, excludeDuts, includeIxiaPorts, consolidateInterfaces)
