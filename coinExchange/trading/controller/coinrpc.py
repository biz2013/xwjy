from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import logging

logger = logging.getLogger("site.coin_rpc")

# TODO: Add logging and make sure it works.

class CoinProxy(object):
  def __init__(self, server_ip, port, user_name, user_password, account):
    self.server_ip = server_ip
    # found in coin conf, rpcport
    self.port = port
    # found in coin conf, rpcuser
    self.user_name = user_name
    # found in coin conf, rpcpassword
    self.user_password = user_password

    # wallet account, group of addresses.
    self.account = account

    # "http://<user>:<password>@<server_ip>:<port>"
    # we could use below curl request for debugging.
    # curl  -v --data-binary '{"jsonrpc":"1.0","id":"curltext","method":"getblockcount","params":[]}' -H 'content-type:text/plain;'  http://cnyfundrpc:J4oxViM8jsC6ySbqoweniVML1t65LtYmbuHB7DsFYdH@192.168.1.214:18189/
    self.conn = AuthServiceProxy("http://%s:%s@%s:%s"%(user_name, user_password, server_ip, port))

  def __init__(self, server_ip, port, user_name, user_password, account, conn):
    self.server_ip = server_ip
    # found in coin conf, rpcport
    self.port = port
    # found in coin conf, rpcuser
    self.user_name = user_name
    # found in coin conf, rpcpassword
    self.user_password = user_password

    # wallet account, group of addresses.
    self.account = account

    # "http://<user>:<password>@<server_ip>:<port>"
    # we could use below curl request for debugging.
    # curl  -v --data-binary '{"jsonrpc":"1.0","id":"curltext","method":"getblockcount","params":[]}' -H 'content-type:text/plain;'  http://cnyfundrpc:J4oxViM8jsC6ySbqoweniVML1t65LtYmbuHB7DsFYdH@192.168.1.214:18189/
    self.conn = conn

  def listtransactions(self, lookback_count):
    return self.conn.listtransactions(lookback_count)

  def sendtoaddress(self, dest_addr, amount, comment):
    return self.conn.sendtoaddress(dest_addr, amount, '{0}'.format(comment))

  #
  def unlockwallet(self, passphrase, timeout_in_sec):
    return self.conn.walletpassphrase(passphrase, timeout_in_sec)

  def getnewaddress(self, account):
    return self.conn.getnewaddress(account)