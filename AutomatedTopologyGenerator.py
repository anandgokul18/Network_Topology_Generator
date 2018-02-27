# Copyright (c) 2015 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

#!/usr/bin/python

import pexpect

print "\t\t\t\t\tNeighbor Details of DUTS in testbed \n"

cmd = "show lldp neighbor"

dut = [ "fm367", "lf218", "ck338"]

for i in xrange(0,len(dut)):
   print dut[i]+ ":"
   print ""
   child = pexpect.spawn("ssh admin@"+dut[i],timeout=120)
   child.expect(">")
   child.sendline("enable")
   child.expect("#")
   child.sendline(cmd)
   child.expect("#")
   print(child.before)
   print ""
   print"-----------------------------------------------------------"
   child.close()



