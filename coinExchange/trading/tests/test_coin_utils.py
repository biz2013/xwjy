import json
import unittest
from trading.controller.coin_utils import *

# Test with real wallet.
class CoinUtilsTestCase(unittest.TestCase):

  def test_listtransactions(self):
    with open('data/wallet_config.json') as f:
      config_json = json.load(f)
      coin_utils = get_coin_utils("cny", config_json)
      print(coin_utils.create_wallet_address())