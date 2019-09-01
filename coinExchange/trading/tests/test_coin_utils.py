import json
import unittest
from trading.controller.coin_utils import *

# comment out 'from trading.models import Wallet' in coin_utils.py to enable this test.

# Test with real wallet. (AdHoc test)
class CoinUtilsTestCase(unittest.TestCase):

  def test_listtransactions(self):
    with open('data/wallet_config.json') as f:
      config_json = json.load(f)
      coin_utils = get_coin_utils_imp("cny", config_json)

      # create new address
      address = coin_utils.create_wallet_address()

      self.assertFalse(not address)
      print(address)

      address = coin_utils.create_wallet_address("")
      self.assertFalse(not address)
      print(address)

      # list transactions (account: "", transaction_count: 5)
      transactions = coin_utils.listtransactions()
      self.assertTrue(len(transactions) > 0)
      print(transactions)

      transactions2 = coin_utils.listtransactions("", 5)
      self.assertTrue(len(transactions) > 0)
      print(transactions2)

      self.assertEqual(len(transactions), len(transactions2))
      self.assertEqual(transactions, transactions2)

      # get balance
      balance = coin_utils.getbalance()
      self.assertTrue(float(balance) > 0)
      print(balance)

      # send transaction
      local_address = "CUc4BpX3YdTx9WPTDXGNJfMaW86HFVXCyo"
      remote_address = "CcwbnuPii3PUMuCE9dXfFK9jPxGRresBXp"

      transaction = coin_utils.send_fund(remote_address, 1.1, "unittest transaction")
      self.assertFalse(not transaction)
      print(transaction)

      transactions = coin_utils.listtransactions()
      found = False
      for tran in transactions:
        if tran == transaction:
          found = True
          break

      self.assertTrue(found)

      # unlock wallet
      coin_utils.unlock_wallet(5)

