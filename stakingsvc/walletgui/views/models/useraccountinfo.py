import json
class UserAccountInfo(object):
    def __init__(self, userid, balance, total_deposit, total_withdraw,
          receiving_address, external_addresses, paymentmethods):
        self.userid = userid
        self.balance = balance
        self.total_deposit = total_deposit
        self.total_withdraw = total_withdraw
        self.receiving_address = receiving_address
        self.external_addresses = external_addresses
        self.paymentmethods = paymentmethods
    def tojson(self):
        json_str = {}
        json_str['username'] = self.username
        json_str['userid'] = self.userid
        json_str['balance'] = self.balance
        json_str['locked_balance'] = self.locked_balance
        json_str['available_balance'] = self.available_balance
        json_str['receiving_address'] = self.receiving_address
        json_str['exerternaladdress'] = self.externaladdress
        paymentmethods = []
        for method in self.paymentmethods:
            element = {}
            element['id'] = method.user_payment_method_id
            element['provider_name'] = method.provider_name
            element['account_at_provider'] = method.account_at_provider
            element['qrcode_image'] = method.qrcode_image
            paymentmethods.append(element)
        json_str['paymentmethods'] = paymentmethods
