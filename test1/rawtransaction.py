import json
from jsonrpc import ServiceProxy, JSONRPCException
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")

print '------------- get raw transaction ---------'
trans = access.getrawtransaction('0a2dfcdf8e0b75c522394f34eb6a62a8242b28e4bc763016fa13470b9cadb124', 0)
print trans
print 'decoded: %s' % (access.decoderawtransaction(trans))
