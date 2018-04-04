# Copyright (c) 2015 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#!/usr/bin/python

#PREREQUISITES: Below python libraries must be installed on the computer, eapi must be enabled on the DUTS, the DUTs must have management connectivity from the computer

import pexpect
import json
import pyeapi
import sys
import os
import time

def func_requirements_satisfier():
	print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
	print "\t\t\t\t\tInstalling the requirements for running this script\n \n"
	print "Please enter your password for installing the required Python packages like pyeapi, pexpect, and json \n"
	time.sleep(3)

	var= os.system("sudo pip install pexpect")
	var= os.system("sudo pip install simplejson")
	var= os.system("sudo pip install pyeapi")

	os.system('tput reset') #This is used to clear the screen ...similar to Ctrl+L in bash

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
	try:
		for i in xrange(0,len(dutslist)):
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
  		print "\n Huh...:x :x FAILED: eApi is not enabled on one of your devices namely:<-- "+dutslist[i]+"-->. Kindle enable eApi on them by configuring: 'management api http-commands--> no shut' to proceed \n"
  		sys.exit()

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

def func_eapi_enabler(dutslist):
	#************************************************************************
	#The below code will enable eApi on all the DUTs in above list

	ssh_newkey = 'Are you sure you want to continue connecting'

	for i in xrange(0,len(dutslist)):

		child_new = pexpect.spawn("ssh "+ "admin@"+dutslist[i],timeout=120)

		ret_val=child_new.expect([ssh_newkey,"word",">"])
	        if ret_val == 0:
	            	child_new.sendline('yes')
	            	ret_val=child_new.expect([ssh_newkey,'password:',">"])
	        if ret_val==1:
	            	child_new.sendline("arastra")
	            	child_new.expect("#")
	        elif ret_val==2:
	            	pass


		child_new.expect(">")
		child_new.sendline("enable")
		child_new.expect("#")
		child_new.sendline("conf t")
		child_new.expect("#")
		child_new.sendline("management api http-commands")
		child_new.expect("#")
		child_new.sendline("no shut")
		child_new.expect("#")
		child_new.close()

def func_neighbor_printer(final_dict):
	#************************************************************************
	#The below code will print the output in neat format
	for i in xrange(0,len(final_dict)):
		print final_dict[i]['neighborDevice'] + '\t(' + final_dict[i]['neighborPort'] + ')' + '\t--------------------'  + '\t(' + final_dict[i]['port'] + ')' + final_dict[i]['myDevice']


	print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
	print "Presented to you by anandgokul (Ping me if any errors/ exceptions are encountered. This script doesn't handle most exceptions as of now...Will add that functionality l8r....Sayonara! :D \n \n"

if __name__== "__main__":
  
  	#First argument is username of person to login to us128
	#Second argument is the us128 password for username
	#Third argument is username of person whose account we want to see

	usernamelogin= sys.argv[1]
	server='us128'
	password= sys.argv[2]
	username=sys.argv[3]

  	func_requirements_satisfier()  #install the required python libraries automatically
  	var_dutslist= func_listofduts_grabber(usernamelogin,server,password,username) #login to us128 and grab the list of DUTs owned by current user and return a list containing the DUTs
  	func_warning_message() #Will warn users about the list of reasons why the script could fail
  	##Doesn't work YET### func_eapi_enabler(var_dutslist) #Will enable eApi on all DUTs so that users don't have to...How cool!  For now, I will give out a error message asking users to enable eAPI manually.
  	var_finalconnectiondetails= func_neighbor_generator(var_dutslist) #does the work of grabbing lldp info from all the DUTs, and removing duplicates 
  	func_neighbor_printer(var_finalconnectiondetails)
 	

#************************************************************************
#Sayonara guys! Enjoy the code. Presented to you by one and only anandgokul@

