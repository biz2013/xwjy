import sys
import json
from jsonrpc import ServiceProxy, JSONRPCException
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

fromacct = sys.argv[1]
toacct = sys.argv[2]
amt = float(sys.argv[3])
try:
    print 'move 1.0 from \'%s\' to \'%s\': %s' % (fromacct, toacct, access.move(fromacct, toacct, amt))

except JSONRPCException, e:
    print repr(e.error)

