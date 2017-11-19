import sys
import json
from jsonrpc import ServiceProxy, JSONRPCException
#access = ServiceProxy("http://127.0.0.1:19344")
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

addr = sys.argv[1]
try:
    print 'account of %s is %s' % (addr, access.getaccount(addr))

except JSONRPCException, e:
    print repr(e.error)

