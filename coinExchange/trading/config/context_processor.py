from trading.models import SiteSettings


def settings(request):
  return {'settings': SiteSettings.load()}


# in Paypal checkout mode, we only support one paypal seller, this is limited by how paypalrestsdk works, it only
# allow one paypal application per environment.
def is_paypal_checkout_mode():
  return True


# We only support one paypal seller, so it's hardcoded. Also he is the only one could create CAD.
PAYPAL_PRIMARY_USER = "yingzhou61@yahoo.ca"
#PAYPAL_ENV = "Sandbox"
PAYPAL_ENV = "Live"
#PAYPAL_PRIMARY_USER = "xb2.wang@gmail.com"


def is_paypal_primary_user(user_name):
  return user_name.lower() == PAYPAL_PRIMARY_USER.lower()

def is_paypal_live():
  return PAYPAL_ENV == "Live"
