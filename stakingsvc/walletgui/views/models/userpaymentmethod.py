class UserPaymentMethodView(object):
    def __init__(self, id, userid, provider_code, provider_name, account):
        self.id = id
        self.userid = userid
        self.provider_code = provider_code
        self.provider_name = provider_name
        self.account_at_provider = account
