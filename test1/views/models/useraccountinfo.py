class UserAccountInfo(object):
    def __init__(self, user, balance, locked_balance, available_balance,
            internal_axfund_address, external_axfund_address,
            paymentmethods):
        self.user = user
        self.balance = balance
        self.locked_balance = locked_balance
        self.available_balance = available_balance
        self.address = internal_axfund_address
        self.externaladdress = external_axfund_address
        self.paymentmethods = paymentmethods
