# Copyright (c) 2015 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#!/usr/bin/python

import pexpect
import json
import pyeapi

username= "anandgokul"

print"\n \n ----------------------------------------------------------------------------------------------------------------------  \n"
print "\t\t\t\t\tNeighbor Details of DUTS in testbed for User '"+username+ "':"

cmd1= "Art list --pool=systest| grep "+ username
cmd2 = "show lldp neighbor"

#*************************************************************************************
#The below code will use login to us128 and grab the list of DUTs owned by current user

child = pexpect.spawn("ssh "+ username+ "@us128",timeout=120)
child.expect("password:")
child.sendline("anandgokul123")

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
print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
print "WARNING: Ensure all ports are not shut or errdisabled. Else, they will not be included in your topology\n "
#************************************************************************
#The below code will use the DUT names from above and get raw lldp information


# for i in xrange(0,len(dutslist)):
#    print dutslist[i]+ ":"
#    print ""
#    child = pexpect.spawn("ssh admin@"+dutslist[i],timeout=120)
#    child.expect(">")
#    child.sendline("enable")
#    child.expect("#")
#    child.sendline(cmd2)
#    child.expect("#")
#    print(child.before)
#    print ""
#    print"-----------------------------------------------------------"
#    child.close()

#************************************************************************
#The below code will grab lldp info from all DUTs in json format and refine it and
#it will consolidate all the lldp information into a single dictionary

grand_diction=[]

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

#************************************************************************
#The below code will print the output in neat format
for i in xrange(0,len(final_dict)):
	print final_dict[i]['neighborDevice'] + '\t(' + final_dict[i]['neighborPort'] + ')' + '\t--------------------'  + '\t(' + final_dict[i]['port'] + ')' + final_dict[i]['myDevice']




print"\n ---------------------------------------------------------------------------------------------------------------------- \n "
print "Presented to you by anandgokul (Ping me if any errors/ exceptions are encountered....Sayonara! :D "


#************************************************************************
#The below code will get the connected interfaces output

#Sayonara guys! Enjoy the code. Presented to you by one and only anandgokul@