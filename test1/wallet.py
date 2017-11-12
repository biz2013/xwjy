from __future__ import absolute_import
from jsonrpc import ServiceProxy
#access = ServiceProxy("http://127.0.0.1:19344")
access = ServiceProxy("http://axfundrpc:9iNDhVdyRbsXoDxS3s2MiUenSTTixKAs4HzDvHYtRFTC@127.0.0.1:19345")
print access.getinfo()
print access.listreceivedbyaddress(6, True)
print access.getbalance()
print access.listtransactions('second')
#print access.getaccountaddress('second')
print access.listtransactions('first')
#print access.getnewaddress('account')
