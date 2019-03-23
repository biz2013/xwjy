class UserPaymentMethodView(object):
    def __init__(self, id, userid, provider_code, provider_name, account, qrcode_image, client_id, client_secret):
        self.user_payment_method_id = id
        self.userid = userid
        self.provider_code = provider_code
        self.provider_name = provider_name
        self.account_at_provider = account
        self.qrcode_image = qrcode_image
        self.client_id = client_id
        self.client_secret = client_secret
