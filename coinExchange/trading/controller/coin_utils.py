import json, subprocess, logging
from trading.controller.coinrpc import CoinProxy

logger = logging.getLogger("site.coin_util")

# TODO : consolidate a unified way to store/fetch coin configuration.
# Currently we have three places: 1) sitesetting table, 2) wallet table, 3) config file.
# We need to save them into one place.
def get_cnyfd_utils(config):
  return

def get_axfd_utils(sitesettings, config):
  wallet_account_name = sitesettings.axfd_account_name
  axfd_passphrase = sitesettings.axfd_passphrase
  wallet_rpc_user = sitesettings.axfd_rpc_user
  wallet_rpc_user_password = sitesettings.axfd_rpc_user_password
  wallet_ip = config.axfd_host
  wallet_rpc_port = config.axfd_host_port
  transaction_lookback_count = config.axfd_lookback_count

  axfd_tool = CoinUtils(wallet_account_name, axfd_passphrase,
                        wallet_ip, wallet_rpc_port, wallet_rpc_user,
                        wallet_rpc_user_password, transaction_lookback_count)

  return axfd_tool

# Control coin wallet with remote rpc calls.
class CoinUtils(object):

  def __init__(
      self,
      account_name,
      passphrase,
      coin_host_ip,
      coin_host_port,
      rpc_user,
      rpc_user_password,
      transaction_lookback_count
  ):
    self.account = account_name
    self.passphrase = passphrase
    self.host = coin_host_ip
    self.host_port = coin_host_port
    self.rpc_user = rpc_user
    self.rpc_userpassword = rpc_user_password
    self.transaction_lookback_count = transaction_lookback_count
    self.coin_rpc = CoinProxy(
      self.host,
      self.host_port,
      self.rpc_user,
      self.rpc_userpassword,
      self.account)

  def listtransactions(self):
    res = self.coin_rpc.listtransactions(self.transaction_lookback_count)
    logger.info("listtransaction return: {0}".format(res))

    return res

  def send_fund(self, dst, amount, comment):
    logger.info('{0} {1} {2} \'{5}\''.format(
      'sendtoaddress', dst, str(amount), comment
    ))

    transaction_id = self.coin_rpc.sendtoaddress(dst, amount, comment)

    logger.info("send to address return transaction id {0}".format(transaction_id))

    transactions = self.listtransactions()
    for trans in transactions:
      # if accidentally send money to address in the same accounts
      # you can see two trans have the same txid. so need to check
      # category field
      if trans['txid'] == transaction_id.rstrip() and trans['category'] == 'send':
        return trans
    raise ValueError("Not redeem transaction for txid {0}".format(transaction_id))

  def unlock_wallet(self, timeout_in_sec):
    logger.info("unlock_wallet with {0} seconds".format(timeout_in_sec))
    self.coin_rpc.unlockwallet(self.passphrase, timeout_in_sec)

  def create_wallet_address(self):
    new_address = self.coin_rpc.getnewaddress(self.account)
    logger.info("Wallet address {0} created".format(new_address))

    return new_address
