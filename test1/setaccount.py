import sys
import json
from jsonrpc import ServiceProxy, JSONRPCException
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

addr=sys.argv[1]
account = sys.argv[2]
try:
    print 'set address of \'%s\' to account %s:%s' % (addr, account, access.setaccount(addr,account))
    print access.listreceivedbyaddress(0, True)
except JSONRPCException, e:
    print repr(e.error)

