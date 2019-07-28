from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import logging

logger = logging.getLogger("site.coin_rpc")

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

  @classmethod
  def fromMockConn(self, server_ip, port, user_name, user_password, account, conn):
    proxy = CoinProxy(server_ip, port, user_name, user_name, account)
    proxy.conn = conn

    return proxy

  def listtransactions(self, lookback_count):
    logger.info("wallet rpc: list transactions with count {0} on server {1}".format(lookback_count, self.server_ip))
    return self.conn.listtransactions(lookback_count)

  def sendtoaddress(self, dest_addr, amount, comment):
    logger.info("wallet rpc: send {0} to address {1} with comment {2}".format(amount, dest_addr, comment))
    return self.conn.sendtoaddress(dest_addr, amount, '{0}'.format(comment))

  def unlockwallet(self, passphrase, timeout_in_sec):
    logger.info("wallet rpc: unlock wallet with {0} seconds".format(timeout_in_sec))
    return self.conn.walletpassphrase(passphrase, timeout_in_sec)

  def getnewaddress(self, account):
    logger.info("wallet rpc: get new address for account {0}".format(account))
    return self.conn.getnewaddress(account)