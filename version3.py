# Copyright (c) 2015 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#!/usr/bin/python

#PREREQUISITES: Below python libraries must be installed on the computer, eapi must be enabled on the DUTS, the DUTs must have management connectivity from the computer
import pexpect #SSH library with expect support
import json #Output of eApi needs to be parsed
import pyeapi #eApi support
import sys
import os
import time
import string
import ConfigParser #For checking input arguments
import argparse
from graphviz import Source #Make a topology graph
import paramiko
import socket
from pyeapi import eapilib
import subprocess
import textwrap

def func_list_from_file(username,fileloc):
	print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
	print "\t\t\t\t\tList of DUTS as per the file provided is:"

	listofdutsasperfile=[]
	temp=[]

	file = open(fileloc)
	listofdutsasperfile = file.readlines()

	for i,data in enumerate(listofdutsasperfile):
		if '#' in data[0] or '\n' in data[0]:
			listofdutsasperfile[i]=None
	#print listofdutsasperfile

	for i,data in enumerate(listofdutsasperfile):
		if data!=None:
			temp.append(data.strip())
	#print temp

	print str(temp)
	return temp

def func_listofduts_grabber_NoNeedPassword(username,poolname):
	print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
	print "\t\t\t\t\tNeighbor Details of DUTS in Art list output for user '"+username+ "':"

	usernamelogin='anandgokul'
	server='us128'
	password='anandgokul123'
	#*************************************************************************************
	#The below code will use directly run Art list command and get output (NO SSH)

	#The below try-except block will cover exception when user-server is unreachable
	try:
		child = pexpect.spawn("ssh "+ usernamelogin+ "@"+server,timeout=30)
		child.expect("password:")
		child.sendline(password)

		cmd1= "Art list --pool="+poolname+" | grep "+ username
		child.expect(">")
		child.sendline(cmd1)

		#Saving the output to duts1
		child.expect(">")
		duts1= (child.before)
		#print duts1

		#Splitting the output based on newline into list duts2
		duts2=duts1.strip()
		duts2= duts2.split("\n")
		#print duts2

		#Stripping the leading whitespaces in each element of above list. After that saving only the dut name in another list
		duts3=[]
		for i in xrange(0, len(duts2)):
		   duts2[i]=duts2[i].strip()
		   if i!=0:
		      duts3.append((duts2[i].split(" "))[0])
		#print duts3

		#We got only the dut names as list in dut3. But, there is another trash entry at end which needs to be removed. 
		dutslist=duts3[:-1]

		print "\n \n The DUTs owned by " + username +" are:  " + str(dutslist)

		return dutslist

	except Exception as e:
		print "\n [ERROR] There was some issue with reaching the user servers. Please fix reachability to Arista Network \n"
		sys.exit()

def func_excluder(var_dutslist,excluded):
	print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
	print "Note: Some devices are marked to be excluded from topology. \n"
	
	#Removing the matches using intersections
	ss= set(var_dutslist)
	fs =set(excluded)

	finallist= list(ss.union(ss)  - ss.intersection(fs))
	
	print "The final DUTs for which Topology will be generated are: "+str(finallist)

	return finallist

def func_warning_message():
	print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
	print "Note: Please ensure that the ports are not shut or errdisabled. Else, they will not be included in your topology."
	print "IMPORTANT NOTE: All non-LLDP supported neighbors (such as linux servers) are also shown as Ixia connections. \n"

def func_neighbor_generator(dutslist):
	
#************************************************************************
#The below code will grab lldp info from all DUTs in json format and refine it and
#it will consolidate all the lldp information into a single dictionary

	grand_diction=[]

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
		   	grand_diction.append(temp_diction)
		   	#print temp_diction

		   grand_diction = grand_diction[:-1]
		   #print grand_diction	

		except pyeapi.eapilib.ConnectionError as e:
	  		print "\n[Please Wait]: eApi is not enabled on one of your devices namely:<-- "+dutslist[i]+"-->. Hold on while we do that for you \n"
	  		
	  		func_eapi_enabler(dutslist[i])

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
					grand_diction.append(temp_diction)
				#print temp_diction

				grand_diction = grand_diction[:-1]

				#print grand_diction

			except:
				print "Oops...the above eApi enabling failed. can you enable eApi manually on "+dutslist[i]+ " manually by doing 'management api http-commands' --> 'no shut'"
				sys.exit(1)

	#************************************************************************
	#The below code will remove the duplicates from the grand dictionary such that one connection shows up only once. The duplicates are marked as key=temp and value=NULL

	for i in xrange(0,len(grand_diction)):
		tempvar= grand_diction[i] #Storing each dictionary in one temp variable
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
		for j in xrange(0,len(grand_diction)):
			if tempvar == grand_diction[j]:
				count=count+1

		if count==2:
			grand_diction[i]={'temp':'Null'}

	#print grand_diction

	#************************************************************************
	#The below code will remove the duplicates completely by removing dictionaries with key as temp. ALso, removing the '.sjc.aristanetworks.com' in DUT name

	final_dict=[] #This list will have only non-duplicate values

	for i in xrange(0,len(grand_diction)):
		if grand_diction[i].get('temp')== None:
			grand_diction[i]['neighborDevice']=grand_diction[i]['neighborDevice'].split('.')[0]
			grand_diction[i]['myDevice']=grand_diction[i]['myDevice'].split('.')[0]
			try:
				grand_diction[i]['port']='Et'+(grand_diction[i]['port'].split('Ethernet')[1])
			except:
				print "[ERROR]: One of your lldp neighbors is not in typical format. Cannot proceed..."
				sys.exit()
			grand_diction[i]['neighborPort']='Et'+(grand_diction[i]['neighborPort'].split('Ethernet')[1])
			final_dict.append(grand_diction[i])

	return final_dict

def func_ixia(dutslist,var_finalconnectiondetails):
	
#************************************************************************
#The below code will grab lldp info from all DUTs in json format and refine it and
#it will consolidate all the lldp information into a single dictionary

	#print var_finalconnectiondetails

	ixialist=[]

	for i in xrange(0,len(dutslist)):
		
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
			if 'Management' in listofconnections[k] or 'Port-Channel' in listofconnections[k]:
				listofconnections[k]=None
			#print listofconnections[k]

		#Removing lldp interfaces from ixia interfaces
		for j in xrange(0,len(var_finalconnectiondetails)):
			#print var_finalconnectiondetails[i]
		   	if var_finalconnectiondetails[j]['neighborDevice'] or var_finalconnectiondetails[j]['myDevice']==dutslist[i]:
		   		if var_finalconnectiondetails[j]['neighborDevice']==dutslist[i]:
		   			for k in xrange(0,len(listofconnections)):
		   				if listofconnections[k]==('Ethernet'+var_finalconnectiondetails[j]['neighborPort'].split('Et')[1]):
		   					listofconnections[k]=None
		   		if var_finalconnectiondetails[j]['myDevice']==dutslist[i]:
		   			for k in xrange(0,len(listofconnections)):
		   				if listofconnections[k]==('Ethernet'+var_finalconnectiondetails[j]['port'].split('Et')[1]):
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
				ixiadict['myDevice']='IxiaChassis'
				ixiadict['port']='Unknown'
				ixialist.append(ixiadict)
				#print onlyixiaconnections
	
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
		print '[Update] We are still trying to enable eApi on '+dutname+'\n'


	except socket.error:
		print "[ERROR]: Device "+dutname +" is unreachable. Please fix it and rerun the script! \n"
		sys.exit(1)

def func_neighbor_printer(final_dict,ixiadict):
	#************************************************************************
	#The below code will print the output in neat format
	for i in xrange(0,len(final_dict)):
		print final_dict[i]['neighborDevice'] + '\t(' + final_dict[i]['neighborPort'] + ')' + '\t--------------------'  + '\t(' + final_dict[i]['port'] + ')' + final_dict[i]['myDevice']

	print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
	print "Presented to you by anandgokul. Ping me if any errors/ exceptions are encountered that I missed handling...Sayonara! :D \n \n"


def func_graph_gen(final_dict):

	#Installing the requirements for graphviz
	#var= os.system("sudo pip install graphviz")
	print "\n----------------------------------------------------------------------------"
	print "Please complete the installation of Xcode Dev Tools (if prompted) via the GUI and rerun this script"
	print "Status:"
	var1= os.system("xcode-select --install")
	print "----------------------------------------------------------------------------"
	var= os.system("brew install graphviz")

	os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash

	graph_string='''
	digraph finite_state_machine {	
	rankdir=LR;
	size="8,5"
	node [shape = circle];
	'''
	
	#The below block is for handling '-' and '.' being present in DUT name
	for i in xrange(0,len(final_dict)):
		if '-' in final_dict[i]['neighborDevice'] or '-' in final_dict[i]['myDevice'] or '.' in final_dict[i]['neighborDevice'] or '.' in final_dict[i]['myDevice']:
			if '-' in final_dict[i]['neighborDevice'] or '.' in final_dict[i]['neighborDevice']:
				new_str=string.replace(final_dict[i]['neighborDevice'], '-', '_')
				final_dict[i]['neighborDevice']=new_str
			if '-' in final_dict[i]['myDevice'] or '.' in final_dict[i]['myDevice']:
				new_str=string.replace(final_dict[i]['myDevice'], '-', '_')
				final_dict[i]['myDevice']=new_str

	#The below block is for converting the topology to graphviz format
	for i in xrange(0,len(final_dict)):
		tempvar=final_dict[i]['neighborDevice'] + ' -> ' + final_dict[i]['myDevice'] + ' [ label = "' + final_dict[i]['neighborPort'] + '---' + final_dict[i]['port'] + '" ]'
		graph_string=graph_string+tempvar+'\n'

	graph_string=graph_string+'}'
	#print graph_string

	print "----------------------------------------------------------------------------"
	print "Your topology (both .PDF and .GV) has been generated on the current directory"
	print "There is both a readily-available pdf file as well as a .gv file which can be imported to graphing tools like OmniGraffle for further editing(get license for Omnigraffle from helpdesk..:/\n"
	print "If your device names contains either '.' or '-', it will be replaced by '_' to avoid conflict with other packages"
	try:
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()
	except:
		print"\n ---------------------------------------------------------------------------------------------------------------------- "
		print "[ERROR] Looks like we encountered an error. We'll see if installing a package fixes it. Please provide your mac password if prompted"
		print"---------------------------------------------------------------------------------------------------------------------- "
		var=os.system('''/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"''')
		var= os.system("brew install graphviz")
		os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()
		
	try:
		installationcheckcmd="ls /Applications/ | grep -i OmniGraffle"
		returned_value = subprocess.call(installationcheckcmd, shell=True)

		if returned_value==1: #That means OmniGraffle is NOT present
			print "----------------------------------------------------------------------------"
			print "The PDF file has been generated in current directory! " #Instead of OmniGraffle not installed message


		elif returned_value==0: #That means OmniGraffle is present
			print "----------------------------------------------------------------------------"
			print "If you have Omnigraffle installed, choose 'Hierarchial' for getting the Topology in editable format."
			subprocess.call(
    			["/usr/bin/open", "-W", "-n", "-a", "/Applications/OmniGraffle.app","Topology.gv"]
    		)

	except:
		print "Finished!"
		sys.exit(1)

#The main function
def main(username, poolname, fileloc, excluded):

	

	#The below part is used to handle cases of username and/or filelocation provided
	if username==None:
		print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
		print ('[INFORMATION]: Username has not been provided. Using file for Topology generation')
		if fileloc==None:
				fileloc = os.path.expanduser('~/setup.txt') #Default File location
				print ('Default file at ~/setup.txt is used since non-default file locaton as not been provided using -f flag')
		var_dutslist= func_list_from_file(username, fileloc)

	if username!=None and fileloc==None:
		var_dutslist= func_listofduts_grabber_NoNeedPassword(username, poolname) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs

	if fileloc!=None and username!=None:
		print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
		print ('[WARNING]: You have provided both a DUTS list file as well as username. Username has higher priority for Topology generation and will be considered. Ignoring the DUT file info...')
		var_dutslist= func_listofduts_grabber_NoNeedPassword(username, poolname) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs

	

	#This is used to remove the excluded DUTs from the topology generation
	if excluded!=None:
		var_dutslist=func_excluder(var_dutslist,excluded)

	

	func_warning_message() #Will warn users about the list of reasons why the script could fail
	  	
	
	var_finalconnectiondetails= func_neighbor_generator(var_dutslist) #does the work of grabbing lldp info from all the DUTs, and removing duplicates 
  	#print var_finalconnectiondetails
	
	var_ixiadict= func_ixia(var_dutslist, var_finalconnectiondetails) 

	var_finalconnectiondetails=var_finalconnectiondetails+var_ixiadict
	#print var_finalconnectiondetails

	func_neighbor_printer(var_finalconnectiondetails, var_ixiadict)

	graphrequired = raw_input("Do you need a graphical representation? (Y/n) ")
	if graphrequired=='n' or graphrequired=='N':
		print 'Finished!'
	else:
		func_graph_gen(var_finalconnectiondetails) #generates a graphical representation



if __name__== "__main__":

  	#Usage: python filename.py username pool

	# Parsing Options
    parser = argparse.ArgumentParser(description='Used to generate topology incl. ixia connection by taking username as input',formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-u', '--user', help="Username of user who's topology is needed")
    parser.add_argument('-p', '--pool', default='systest', help='Specify the pool for the above user (default = systest)')
    parser.add_argument('-f', '--file', help='Setup File / DUT List to Load (default = ~/setup.txt)')
    parser.add_argument('-x', '--exclude',nargs='+', help='Exclude the following DUTs from the my devices list during topology formation')
    options = parser.parse_args()


    # if len(sys.argv)==1:
    # 	print "[ERROR] Please provide arguments to proceed. Please use -h flag for further help \n"
    # 	sys.exit(1)

#Assigning the arguments to variables
username=options.user
poolname=options.pool
fileloc=options.file
excluded=options.exclude

main(username, poolname, fileloc, excluded)
	#************************************************************************
	#Sayonara guys! Enjoy the code. Presented to you by one and only anandgokul@