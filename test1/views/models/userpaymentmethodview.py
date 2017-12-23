class UserPaymentMethodView(object):
    def __init__(self, id, provider_code, provider_name, account, qrcode_image):
        self.user_payment_method_id = id
        self.provider_code = provider_code
        self.provider_name = provider_name
        self.account_at_provider = account
        self.qrcode_image = qrcode_image
