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
import ConfigParser #For checking input arguments
from graphviz import Source #Make a topology graph
import paramiko
import socket
from pyeapi import eapilib
import subprocess

def func_listofduts_grabber(usernamelogin,server,password,username):
	print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
	print "\t\t\t\t\tNeighbor Details of DUTS in testbed for User '"+username+ "':"

	#*************************************************************************************
	#The below code will use login to us128 and grab the list of DUTs owned by current user

	#The below try-except block will cover exception when user-server is unreachable
	try:
		child = pexpect.spawn("ssh "+ usernamelogin+ "@"+server,timeout=120)
		child.expect("password:")
		child.sendline(password)

		cmd1= "Art list --pool=systest| grep "+ username
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
		print "\n Huh...:x :x FAILED: Could not resolve hostname " + server + "- Please verify the server hostname and reachability \n"
		sys.exit()

def func_warning_message():
	print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
	print "WARNING 1: Ensure connectivity to the DUTs from this device"
	#print "WARNING 2: Ensure eapi is enabled on your DUTs (management api http-commands--> no shut) " #Adding exception handling for this
	print "WARNING 2: Ensure that the ports are not shut or errdisabled. Else, they will not be included in your topology. \n"

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
			grand_diction[i]['port']='Et'+(grand_diction[i]['port'].split('Ethernet')[1])
			grand_diction[i]['neighborPort']='Et'+(grand_diction[i]['neighborPort'].split('Ethernet')[1])
			final_dict.append(grand_diction[i])

	return final_dict

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
		print '[Update] eApi has been successfully enabled on '+dutname+'\n'


	except socket.error:
		print "[ERROR]: Device "+dutname +" is unreachable. Please fix it and rerun the script! \n"
		sys.exit(1)

def func_neighbor_printer(final_dict):
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
	print "Please complete the installation the Xcode Dev Tools (if prompted) via the GUI and rerun this script"
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
	for i in xrange(0,len(final_dict)):
		tempvar=final_dict[i]['neighborDevice'] + ' -> ' + final_dict[i]['myDevice'] + ' [ label = "' + final_dict[i]['neighborPort'] + '---' + final_dict[i]['port'] + '" ]'
		graph_string=graph_string+tempvar+'\n'

	graph_string=graph_string+'}'
	#print graph_string

	print "----------------------------------------------------------------------------"
	print "Your topology (both .PDF and .GV) has been generated on the current directory"
	print "There is both a readily-available pdf file as well as a .gv file which can be imported to graphing tools like OmniGraffle for further editing(get license for Omnigraffle from helpdesk..:/\n"
	try:
		s = Source(graph_string, filename="Topology.gv", format="pdf")
		s.view()
	except:
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
			print "You don't have OmniGraffle installed. Please contact IT helpdesk"


		elif returned_value==0: #That means OmniGraffle is present
			print "----------------------------------------------------------------------------"
			print "If you have Omnigraffle installed, choose 'Hierarchial' for getting the Topology in editable format."
			subprocess.call(
    			["/usr/bin/open", "-W", "-n", "-a", "/Applications/OmniGraffle.app","Topology.gv"]
    		)

	except:
		print "Finished!"
		sys.exit(1)

#LOGICAL MAIN FUNCTION
def logical_main(usernamelogin, server, password, username):
	
  	var_dutslist= func_listofduts_grabber(usernamelogin,server,password,username) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs
  	func_warning_message() #Will warn users about the list of reasons why the script could fail
  	
  	var_finalconnectiondetails= func_neighbor_generator(var_dutslist) #does the work of grabbing lldp info from all the DUTs, and removing duplicates 
  	#print var_finalconnectiondetails
  	
  	func_neighbor_printer(var_finalconnectiondetails)

  	graphrequired = raw_input("Do you need a graphical representation? (Y/n) ")
  	if graphrequired=='n' or graphrequired=='N':
  		print 'Finished!'
  	else:
  		func_graph_gen(var_finalconnectiondetails) #generates a graphical representation

# Intermediate Function between Actual Main and Logical Main
def main(argv=sys.argv):

	userinput=sys.argv[1]

	try:
		usernamelogin=(userinput.split('@'))[0]
		server=(userinput.split('@')[1]).split("::")[0]
		password=userinput.split('::')[1]

		if password=='': #Covering the corner case wherein :: is given but no password after that
			print '\n[[ERROR]]: Please give the input in the form of: username@userserver::password [differentuser] \n'
			print 'Example in case you need your own topology\t\t: anandgokul@us128::password'
			print "Example in case you need someone else's topology\t: anandgokul@us128::password jonsnow\n"
			sys.exit(1)

	except IndexError:
		print '\n[[ERROR]]: Please give the input in the form of: username@userserver::password [differentuser] \n'
		print 'Example in case you need your own topology\t\t: anandgokul@us128::password'
		print "Example in case you need someone else's topology\t: anandgokul@us128::password jonsnow\n"
		sys.exit(1)

	#************************************************************************
	#handling cases wherein user hasn't provided different user for topology
	if len(sys.argv) == 2:
		username=usernamelogin
	if len(sys.argv) == 3:
		username=sys.argv[2]

	logical_main(usernamelogin, server, password, username)

if __name__== "__main__":

  	#Usage: python filename.py loginname@server::password usernamefordetails

	#************************************************************************
	#The below code will handle error and provide info as to how input should be given

	if len(sys.argv) < 2 or len(sys.argv) > 3: #This kicks in if user hasnt provided even the basic login info, passwored AND if user provided more than required info
    		sys.stderr.write("Usage:  username@userserver::password [username]\n")
    		sys.stderr.write('  <mandatory>  [optional]\n')
    		sys.exit(1)

	main(sys.argv)


#************************************************************************
#Sayonara guys! Enjoy the code. Presented to you by one and only anandgokul@

