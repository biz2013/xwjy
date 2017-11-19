import json
from jsonrpc import ServiceProxy, JSONRPCException
#access = ServiceProxy("http://127.0.0.1:19344")
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")
#print access.stop()
#print access.getinfo()

try:
    print '------------- getbalance ---------'

    print access.getbalance()
#    print access.getbalance('')
    print access.getbalance('first')
    print access.getbalance('count')
    print access.getbalance('second')
except JSONRPCException, e:
    print repr(e.error)

print '-------------- move everything from <empty> to second ----'
#try:
#     print access.move('','second', 10)
#except JSONRPCException, e:
#     print repr(e.error)

print '-------------- list all accounts in the wallet -----'
addresses = access.listreceivedbyaddress(0, True)

#jsonobj=json.loads(addresses)
print 'There are %d addresses in the wallet' % (len(addresses))
print addresses

print 'Address groupings:'
print access.listaddressgroupings()

try:
    #print '----- listreceivedbyaccount(0, True)--------'
    # Deprecated API, it will cause exception
    #print access.listreceivedbyaccount(0, True)

    print '----- list transaction of all accounts ------'
    print access.listtransactions() 
#print access.getbalance()

#print '-------------------------------------------------'

#try:

#    print access.walletpassphrase('iloveit1172',200)
#    print access.sendtoaddress('AXvrDohCBxLytjs6nbCHhj4KBv5gukwvuj',0.15, 'another try to test','what will this show up')
#    print access.sendfrom('first', 'AXvrDohCBxLytjs6nbCHhj4KBv5gukwvuj',0.1, 6)
except JSONRPCException, e:
    print repr(e.error)

#print '******************** transactions of second **********************'
#print access.listtransactions('second')
#print access.getaccountaddress('second')
#print '&&&&&&&&&&&&&&&&&&&& transactions of first &&&&&&&&&&&&&&&&&&&&&&'
#print access.listtransactions('first')
#print access.getnewaddress('account')
