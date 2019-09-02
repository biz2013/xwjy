from .base import *

DEBUG=False

# https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
# A list of strings representing the host/domain names that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, 
# which are possible even under many seemingly-safe web server configurations.

STATIC_ROOT = "/var/www/coinexchange/static/"

MEDIA_ROOT = "/var/www/coinexchange/media/"

ALLOWED_HOSTS = [ '52.43.117.129', 'localhost', '127.0.0.1', '[::1]']

TRADESITE_PAYMENT_URLPREFIX="http://52.43.117.129:8081/trading/payment_qrcode_url/"

API_TRANS_LIMIT_IN_CENT = 1000000

API_SITE_URL = {
    'stakinguser1' : 'https://www.9lp.com/member/getpaymentqrcode.php?out_trade_no={0}'
}
