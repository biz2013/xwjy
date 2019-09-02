import json, subprocess, logging
from trading.controller.coinrpc import CoinProxy
from trading.models import Wallet

logger = logging.getLogger("site.coin_util")

# Sample config object: trading/tests/data/wallet_config.json
# config object is read from database, Wallet table, config_json column
def get_coin_utils_imp(coin_name, config):
  if not config['account']:
    # Default account is ""
    config['account'] = ""

  if not config['passphrase']:
    logger.error('get_coin_utils({0}): the wallet passphrase is empty'.format(coin_name))
    raise ValueError('{0} INCORRECT_CRYPTO_CONFIG'.format(coin_name))

  if not config['rpc_user']:
    logger.error('get_coin_utils({0}): the wallet rpc user name is empty'.format(coin_name))
    raise ValueError('{0} INCORRECT_CRYPTO_CONFIG'.format(coin_name))

  if not config['rpc_user_password']:
    logger.error('get_coin_utils({0}): the wallet rpc user password is empty'.format(coin_name))
    raise ValueError('{0} INCORRECT_CRYPTO_CONFIG'.format(coin_name))

  if not config['host_ip']:
    logger.error('get_coin_utils({0}): the host ip is empty'.format(coin_name))
    raise ValueError('{0} INCORRECT_CRYPTO_CONFIG'.format(coin_name))

  if int(config['rpc_port']) <= 0:
    logger.error('get_coin_utils({0}): the wallet rpc port number {1} is incorrect.'.format(coin_name, config.rpc_port))
    raise ValueError('{0} INCORRECT_CRYPTO_CONFIG'.format(coin_name))

  if int(config['transaction_lookback_count']) <= 0:
    logger.error('get_coin_utils({0}): the wallet transaction lookback acount is incorrect.'.format(coin_name, config.transaction_lookback_count))
    raise ValueError('{0} INCORRECT_CRYPTO_CONFIG'.format(coin_name))

  return CoinUtils(
    coin_name,
    config['account'],
    config['passphrase'],
    config['host_ip'],
    config['rpc_port'],
    config['rpc_user'],
    config['rpc_user_password'],
    config['transaction_lookback_count'])

def get_coin_utils(coin_code):
  try:
    wallet = Wallet.objects.get(cryptocurrency__currency_code=coin_code)
    coin_name = wallet.cryptocurrency.name
    if not wallet.config_json:
      logger.error('get_coin_utils({0}): the wallet does not have config'.format(coin_code))
      raise ValueError('{0}: CRYPTO_WALLET_NO_CONFIG'.format(coin_code))
    return get_coin_utils_imp(coin_name, json.loads(wallet.config_json))

  except Wallet.DoesNotExist:
    logger.error('get_coin_utils({0}): the wallet does not exist'.format(coin_code))
    raise ValueError('CRYPTO_WALLET_NOTFOUND')
  except Wallet.MultipleObjectsReturned:
    logger.error('get_coin_utils({0}): there are more than one wallets'.format(coin_code))
    raise ValueError('CRYPTO_WALLET_NOT_UNIQUE')

  # Control coin wallet with remote rpc calls.
class CoinUtils(object):

  def __init__(
      self,
      coin_name,
      account_name,
      passphrase,
      coin_host_ip,
      coin_rpc_port,
      rpc_user,
      rpc_user_password,
      transaction_lookback_count
  ):
    self.coin_name = coin_name
    self.account = account_name
    self.passphrase = passphrase
    self.host = coin_host_ip
    self.rpc_port = coin_rpc_port
    self.rpc_user = rpc_user
    self.rpc_userpassword = rpc_user_password
    self.transaction_lookback_count = transaction_lookback_count
    self.coin_rpc = CoinProxy(
      self.host,
      self.rpc_port,
      self.rpc_user,
      self.rpc_userpassword)
    logger.info("create coin_util for {0} on host {1}:{2}".format(coin_name, coin_host_ip, coin_rpc_port))

  def listtransactions(self, account = None, transaction_lookback_count = None):
    if account is None:
      wallet_account = self.account
    else:
      wallet_account = account

    if transaction_lookback_count is None:
      wallet_transaction_lookback_count = self.transaction_lookback_count
    else:
      wallet_transaction_lookback_count = transaction_lookback_count

    res = self.coin_rpc.listtransactions(wallet_account, wallet_transaction_lookback_count)
    logger.debug("listtransaction return: {0}".format(res))

    return res

  def getbalance(self, account = None):
    if account is None:
      wallet_account = self.account
    else:
      wallet_account = account

    res = self.coin_rpc.getbalance(wallet_account)
    logger.info("getbalance return: {0}".format(res))

    return res

  # return entire transaction
  # ex: {'account': '', 'address': 'CcwbnuPii3PUMuCE9dXfFK9jPxGRresBXp', 'category': 'send', 'amount': Decimal('-1.10000000'), 'fee': Decimal('-0.01000000'), 'confirmations': 0, 'txid': '606b6bef69216e53215c7ab8b8fab85b928c2c8b0bdd89a8b0e9e4b6596481db', 'time': 1564680775, 'timereceived': 1564680775, 'comment': 'unittest transaction'}
  def send_fund(self, dst, amount, comment):
    logger.info('{0} {1} {2} \'{3}\''.format(
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

  def unlock_wallet(self, timeout_in_sec, passphrase = None):
    if passphrase is None:
      wallet_passphrase = self.passphrase
    else:
      wallet_passphrase = passphrase

    logger.info("unlock_wallet with {0} seconds".format(timeout_in_sec))
    self.coin_rpc.unlockwallet(wallet_passphrase, timeout_in_sec)

  def create_wallet_address(self, account = None):
    if account is None:
      wallet_account = self.account
    else:
      wallet_account = account

    new_address = self.coin_rpc.getnewaddress(wallet_account)
    logger.info("Wallet address {0} created".format(new_address))

    return new_address
