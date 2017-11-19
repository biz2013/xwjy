import sys
import json
from jsonrpc import ServiceProxy, JSONRPCException
#access = ServiceProxy("http://127.0.0.1:19344")
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

print '-------------- list all accounts in the wallet -----'
try:
    print access.listreceivedbyaccount(1, True)
except JSONRPCException, e:
    print repr(e.error)

