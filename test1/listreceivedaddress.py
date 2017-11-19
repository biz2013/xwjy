import json
from jsonrpc import ServiceProxy, JSONRPCException
#access = ServiceProxy("http://127.0.0.1:19344")
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

print '-------------- list all accounts in the wallet -----'
addresses = access.listreceivedbyaddress(0, True)

#jsonobj=json.loads(addresses)
print 'There are %d addresses in the wallet' % (len(addresses))
print addresses
