import json
import unittest
import os
from unittest.mock import MagicMock, Mock, patch
from trading.controller.coinrpc import CoinProxy
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

cny_list_transactions_ret_expect = json.load(open('data/cny_getnewaddress_ret.json'))
cny_getnewaddress_ret_expect = json.load(open('data/cny_getnewaddress_ret.json'))
cny_sendtoaddress_ret_expect = json.load(open('data/cny_sendtoaddress_ret.json'))

class CoinRpcTestCase(unittest.TestCase):

  def setUp(self):
    self.connMock = Mock()

    config = {
      'listtransactions.return_value': cny_list_transactions_ret_expect,
      'sendtoaddress.return_value': cny_sendtoaddress_ret_expect,
      'getnewaddress.return_value': cny_getnewaddress_ret_expect,
      'walletpassphrase.return_value': '',
      'getbalance.return_value' : '34.5'
    }

    self.connMock.configure_mock(**config)
    self.coin_rpc = CoinProxy.fromMockConn("192.168.1.214", "8516", "rpcuser", "rpcpassword", self.connMock)

  def test_listtransactions(self):
    account = ""
    transactions = self.coin_rpc.listtransactions(account, 10)
    self.assertEqual(transactions, cny_list_transactions_ret_expect)
    self.connMock.listtransactions.assert_called_once_with(account, 10)

  def test_sendtoaddress(self):
    recieve_address = "any_address"
    amount = 10.0
    comment = "any comment"
    transaction_id = self.coin_rpc.sendtoaddress(recieve_address, amount, comment)
    self.assertEqual(transaction_id, cny_sendtoaddress_ret_expect)
    self.connMock.sendtoaddress.assert_called_once_with(recieve_address, amount, comment)

  #no return value for walletpassphrase command.
  def test_unlockwallet(self):
    passphrase = "any passphrase"
    time_in_sec = 600
    self.coin_rpc.unlockwallet(passphrase, time_in_sec)
    self.connMock.walletpassphrase.assert_called_once_with(passphrase, time_in_sec)

  def test_getnewaddress(self):
    account = "any account"
    address = self.coin_rpc.getnewaddress(account)
    self.assertEqual(address, cny_getnewaddress_ret_expect)
    self.connMock.getnewaddress.assert_called_once_with(account)

  def test_getbalance(self):
    account = ""
    balance = self.coin_rpc.getbalance(account)
    self.assertEqual(34.5, float(balance))
    self.connMock.getbalance.assert_called_once_with(account)




