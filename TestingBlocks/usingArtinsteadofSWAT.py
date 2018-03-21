def userDutList(username,poolname):
	print "\n > Neighbor Details of DUTS in Art list output for user '"+username+ "':"

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

		print "\t * The DUTs owned by " + username +" are:  " + str(dutslist)

		return dutslist

	except Exception as e:
		print "\n \t [ERROR] There was some issue with reaching the user servers. Please fix reachability to Arista Network \n"
		print "* Script Complete!"
		sys.exit()