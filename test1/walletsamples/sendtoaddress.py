import sys
import json
from jsonrpc import ServiceProxy, JSONRPCException
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

if len(sys.argv) < 3:
    print 'Usage: sendtoaddress address amount'
    sys.exit(-1)
newaddr = sys.argv[1]
amount = float(sys.argv[2])
try:
    print 'send %f to address \'%s\'' % (amount, newaddr)
    print access.walletpassphrase('iloveit1172',200)
    print 'send: %s' % (access.sendtoaddress(newaddr, amount))

except JSONRPCException, e:
    print repr(e.error)

