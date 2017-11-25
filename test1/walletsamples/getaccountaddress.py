import sys
import json
from jsonrpc import ServiceProxy, JSONRPCException
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

account = sys.argv[1]
try:
    print 'address of \'%s\' is %s' % (account, access.getaccountaddress(account))

except JSONRPCException, e:
    print repr(e.error)

