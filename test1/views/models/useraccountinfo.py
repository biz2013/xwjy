import json
class UserAccountInfo(object):
    def __init__(self, login, userid, balance, locked_balance, available_balance,
            receiving_address, external_axfund_address,
            external_address_alias,
            paymentmethods):
        self.username = login
        self.userid = userid
        self.balance = balance
        self.locked_balance = locked_balance
        self.available_balance = available_balance
        self.receiving_address = receiving_address
        self.externaladdress = external_axfund_address
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
