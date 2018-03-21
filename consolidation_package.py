test = [{u'neighborDevice': 'ck338', u'neighborPort': u'Et14/3', 'myDevice': u'co546', u'port': u'Et5', u'ttl': 120},
{u'neighborDevice': 'ck338', u'neighborPort': u'Et14/4', 'myDevice': u'co546', u'port': u'Et6', u'ttl': 120},
{u'neighborDevice': 'fm210', u'neighborPort': u'Et25', 'myDevice': u'ck338', u'port': u'Et10/4', u'ttl': 120},
{u'neighborDevice': 'fm210', u'neighborPort': u'Et26', 'myDevice': u'ck338', u'port': u'Et10/3', u'ttl': 120},
{u'neighborDevice': 'fm210', u'neighborPort': u'Et27', 'myDevice': u'co546', u'port': u'Et1', u'ttl': 120},
{u'neighborDevice': 'fm210', u'neighborPort': u'Et28', 'myDevice': u'co546', u'port': u'Et2', u'ttl': 120},
{u'neighborDevice': 'fm367', u'neighborPort': u'Et21', 'myDevice': u'ck338', u'port': u'Et17/3', u'ttl': 120},
{u'neighborDevice': 'fm367', u'neighborPort': u'Et15', 'myDevice': u'ck338', u'port': u'Et14/1', u'ttl': 120},
{u'neighborDevice': 'fm367', u'neighborPort': u'Et17', 'myDevice': u'ck338', u'port': u'Et14/3', u'ttl': 120},
{u'neighborDevice': 'fm367', u'neighborPort': u'Et16', 'myDevice': u'ck338', u'port': u'Et14/2', u'ttl': 120},
{u'neighborDevice': 'fm367', u'neighborPort': u'Et41', 'myDevice': u'fm210', u'port': u'Et41', u'ttl': 120},
{u'neighborDevice': 'fm367', u'neighborPort': u'Et42', 'myDevice': u'fm210', u'port': u'Et42', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et18', 'myDevice': u'fm367', u'port': u'Et18', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et19', 'myDevice': u'fm367', u'port': u'Et19', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et22', 'myDevice': u'fm210', u'port': u'Et22', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et23', 'myDevice': u'fm210', u'port': u'Et23', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et25', 'myDevice': u'co546', u'port': u'Et3', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et26', 'myDevice': u'co546', u'port': u'Et4', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et27', 'myDevice': u'ck338', u'port': u'Et10/1', u'ttl': 120},
{u'neighborDevice': 'lf218', u'neighborPort': u'Et28', 'myDevice': u'ck338', u'port': u'Et10/2', u'ttl': 120},
{'neighborDevice': 'ck338', 'neighborPort': u'Et16/1', 'myDevice': 'Ixia_11', 'port': 'unknown'}, {'neighborDevice':
'ck338', 'neighborPort': u'Et16/3', 'myDevice': 'Ixia_67', 'port': 'unknown'}, {'neighborDevice': 'ck338',
'neighborPort': u'Et16/2', 'myDevice': 'Ixia_25', 'port': 'unknown'}, {'neighborDevice': 'lf218', 'neighborPort':
u'Et3', 'myDevice': 'Ixia_74', 'port': 'unknown'}, {'neighborDevice': 'lf218', 'neighborPort': u'Et1', 'myDevice':
'Ixia_34', 'port': 'unknown'}]

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

print finallist


# # Kiran's raw consolidation code
# test = [{u'neighborDevice': 'ck338', u'neighborPort': u'Et14/3', 'myDevice': u'co546', u'port': u'Et5', u'ttl': 120}, {u'neighborDevice': 'ck338', u'neighborPort': u'Et14/4', 'myDevice': u'co546', u'port': u'Et6', u'ttl': 120}, {u'neighborDevice': 'fm210', u'neighborPort': u'Et25', 'myDevice': u'ck338', u'port': u'Et10/3', u'ttl': 120}, {u'neighborDevice': 'fm210', u'neighborPort': u'Et26', 'myDevice': u'ck338', u'port': u'Et10/4', u'ttl': 120}, {u'neighborDevice': 'fm210', u'neighborPort': u'Et27', 'myDevice': u'co546', u'port': u'Et1', u'ttl': 120}, {u'neighborDevice': 'fm210', u'neighborPort': u'Et28', 'myDevice': u'co546', u'port': u'Et2', u'ttl': 120}, {u'neighborDevice': 'fm367', u'neighborPort': u'Et15', 'myDevice': u'ck338', u'port': u'Et14/1', u'ttl': 120}, {u'neighborDevice': 'fm367', u'neighborPort': u'Et16', 'myDevice': u'ck338', u'port': u'Et14/2', u'ttl': 120}, {u'neighborDevice': 'fm367', u'neighborPort': u'Et41', 'myDevice': u'fm210', u'port': u'Et41', u'ttl': 120}, {u'neighborDevice': 'fm367', u'neighborPort': u'Et42', 'myDevice': u'fm210', u'port': u'Et42', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et18', 'myDevice': u'fm367', u'port': u'Et18', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et19', 'myDevice': u'fm367', u'port': u'Et19', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et22', 'myDevice': u'fm210', u'port': u'Et22', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et23', 'myDevice': u'fm210', u'port': u'Et23', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et25', 'myDevice': u'co546', u'port': u'Et3', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et26', 'myDevice': u'co546', u'port': u'Et4', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et27', 'myDevice': u'ck338', u'port': u'Et10/1', u'ttl': 120}, {u'neighborDevice': 'lf218', u'neighborPort': u'Et28', 'myDevice': u'ck338', u'port': u'Et10/2', u'ttl': 120}, {'neighborDevice': 'ck338', 'neighborPort': u'Et16/1', 'myDevice': 'Ixia_11', 'port': 'unknown'}, {'neighborDevice': 'ck338', 'neighborPort': u'Et16/3', 'myDevice': 'Ixia_67', 'port': 'unknown'}, {'neighborDevice': 'ck338', 'neighborPort': u'Et16/2', 'myDevice': 'Ixia_25', 'port': 'unknown'}, {'neighborDevice': 'lf218', 'neighborPort': u'Et3', 'myDevice': 'Ixia_74', 'port': 'unknown'}, {'neighborDevice': 'lf218', 'neighborPort': u'Et1', 'myDevice': 'Ixia_34', 'port': 'unknown'}]
 
# # neighborDevice
# # neighborPort
# # myDevice
# # port
# # class Interface:
   
# #     def __init__(self, myDevice, neighborDevice, port, neighborPort):
# #         self.neighborDevice = neighborDevice
# #         self.neighborPort = neighborPort
# #         self.myDevice = myDevice
# #         self.port = port
 
 
# class DeviceConnectivity:
 
#     def __init__(self):
#         self.connections = {}
 
#     def add_device(self, device):
#         b = device['myDevice']
#         a = device['neighborDevice']
#         p2 = device['port']
#         p1 = device['neighborPort']
       
#         if a+'_'+b not in self.connections:
#             self.connections[a+'_'+b] = {'myDevice':a, 'neighborDevice':b, 'port':[p1], 'neighborPort':[p2]}
 
#         else:
#             self.connections[a+'_'+b]['port'].append(p1)
#             self.connections[a+'_'+b]['neighborPort'].append(p2)
#             # port = self.connections[a+'_'+b]['port']
#             # minimum_port = min(p1, *port)
#             # maximum_port = max(p1, *port)
 
#             # neighborPort = self.connections[a+'_'+b]['neighborPort']
#             # minimum_neighborPort= min(p1, *neighborPort)
#             # maximum_neighborPort = max(p1, *neighborPort)
 
#             # self.connections[a+'_'+b]['port'] = [minimum_port, maximum_port]
#             # self.connections[a+'_'+b]['port'] = [minimum_neighborPort, maximum_neighborPort]
       
#     def print_everything(self):
#         for value in self.connections.values():
#             print(value)
 
# d = DeviceConnectivity()
 
# for t in test:
#     d.add_device(t)
 
# d.print_everything()