class UserPaymentMethodView(object):
    def __init__(self, id, provider_name, qrcode_image):
        self.user_payment_method_id = id
        self.provider_name = provider_name
        self.qrcode_image = qrcode_image
