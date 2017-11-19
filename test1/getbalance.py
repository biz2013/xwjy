import json
from jsonrpc import ServiceProxy, JSONRPCException
#access = ServiceProxy("http://127.0.0.1:19344")
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

try:
    print '------------- getbalance ---------'

    print 'overall: %f' % (access.getbalance())
    print 'balance of <empty>: %f' % (access.getbalance(''))
    print 'balance of first: %f' % (access.getbalance('first'))
    print 'balance of account: %f' % (access.getbalance('account'))
    print 'balance of second: %f' % (access.getbalance('second'))
    print 'balance of third: %f' % (access.getbalance('third'))
except JSONRPCException, e:
    print repr(e.error)

