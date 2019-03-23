import logging, json, sys
sys.path.append('../stakingsvc/')

from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.heepaymanager import *
from trading.controller import ordermanager
from trading.controller import userpaymentmethodmanager
from trading.views import errorpageview
from trading.controller.paypalclient import PayPalClient
from paypalcheckoutsdk.orders import OrdersGetRequest
from trading.views.heepay_notify_view import get_payment_confirmation_json

logger = logging.getLogger("site.paypal_confirm")

## Doc:
# How to setup paypalcheckoutsdk: https://developer.paypal.com/docs/checkout/reference/server-integration/setup-sdk/#set-up-the-environment
# How to get transaction detail: https://developer.paypal.com/docs/checkout/reference/server-integration/get-transaction/#on-the-server
# Full detail of order status: https://developer.paypal.com/docs/api/orders/v2/#orders_get

class GetOrder(PayPalClient):
    ## TODO (6): Lock seller order at step TODO (5)? Need to clean up if failed the payment verification. What's the error flow it could be?
    # We seems need to lock seller order
    # We need to verify paypal transaction with buy order.

    # Relationship between buy_order and sell_order?

  #2. Set up your server to receive a call from the client
  """You can use this function to retrieve an order by passing order ID as an argument"""
  def get_order(self, order_id):
    """Method to get order"""
    request = OrdersGetRequest(order_id)
    #3. Call PayPal to get the transaction

    #TODO: error handling on paypal check.
    response = self.client.execute(request)
    #4. Save the transaction in your database. Implement logic to save transaction to your database for future reference.
    print('Status Code: ', response.status_code)
    print('Status: ', response.result.status)
    print('Order ID: ', response.result.id)
    print('Intent: ', response.result.intent)

    print('Gross Amount: {} {}'.format(response.result.purchase_units[0].amount.currency_code,
                       response.result.purchase_units[0].amount.value))

    return (response.result.purchase_units[0].amount,   # amount
            response.result.purchase_units[0].reference_id,     # buy order id
            response.result.purchase_units[0].description,      # seller id / sell order id
            response.result.purchase_units[0].payments.captures[0])     # payment status

@csrf_exempt
def confirm_paypal_order(request):
    try:
        if request.method == 'POST':
            logger.info("Receive async payment notification ")

            response = request.body.decode('utf-8')
            json_data = json.loads(response)

            buy_order_id = json_data.get('buy_order_id')
            paypal_order_description = json_data.get('seller_info')
            seller_info = paypal_order_description.split('/')
            seller_user_id = seller_info[0]
            seller_order_id = seller_info[1]
            orderID = json_data.get('orderID')

            # TODO : read seller paypal client id and secret
            seller_paypal_payment_method = userpaymentmethodmanager.get_user_paypal_payment_method(seller_user_id)
            if seller_paypal_payment_method == None:
                error_msg = "user {0} didn't set paypal payment, there is no paypal info.". \
                    format(seller_user_id)
                logger.error(error_msg)
                return HttpResponse(content='error')

            if not seller_paypal_payment_method.client_id or not seller_paypal_payment_method.client_secret:
                error_msg = "seller {0} didn't set up client id or client secret for their paypal payment.". \
                    format(seller_user_id)
                logger.error(error_msg)
                return HttpResponse(content='error')

            clientID = seller_paypal_payment_method.client_id
            clientSecret = seller_paypal_payment_method.client_secret

            # TODO: Check return value and error handling
            paypal_payment_info = GetOrder(clientID, clientSecret).get_order(orderID)
            db_buy_order_info = ordermanager.get_order_info(paypal_payment_info[1])
            db_sell_order_info = ordermanager.get_order_info(db_buy_order_info.reference_order_id)

            # Validate order id and other info.
            if db_buy_order_info.order_id != buy_order_id:
                error_msg = "buy order id {0} issued by user doesn't match with buy order id from paypal confirmation {1}".\
                    format(buy_order_id, db_buy_order_info.order_id)
                logger.error(error_msg)
                return HttpResponse(content='error')

            if paypal_payment_info[2] != paypal_order_description:
                error_msg = "paypal description {0} issued by user doesn't match with description from paypal confirmation {1}". \
                    format(paypal_order_description, paypal_payment_info[2])
                logger.error(error_msg)
                return HttpResponse(content='error')

            if str(db_sell_order_info.user_id) != seller_user_id:
                error_msg = "paypal seller id {0} issued by user doesn't match with seller id associated with the buy order". \
                    format(seller_user_id, db_sell_order_info.user_id)
                logger.error(error_msg)
                return HttpResponse(content='error')

            if str(db_sell_order_info.order_id) != seller_order_id:
                error_msg = "paypal sell order id {0} issued by user doesn't match with sell order id associated with the buy order". \
                    format(seller_order_id, db_sell_order_info.id)
                logger.error(error_msg)
                return HttpResponse(content='error')

            # Validate amount
            if db_buy_order_info.total_amount != float(paypal_payment_info[0].value):
                error_msg = "payment amount {0} user paid doesn't match with the number from paypal confirmation". \
                    format(db_buy_order_info.total_amount, paypal_payment_info[0].value)
                logger.error(error_msg)
                return HttpResponse(content='error')

            if db_buy_order_info.unit_price_currency != paypal_payment_info[0].currency_code:
                error_msg = "payment currency {0} user paid doesn't match with the currency code from paypal confirmation". \
                    format(db_buy_order_info.unit_price_currency, paypal_payment_info[0].currency_code)
                logger.error(error_msg)
                return HttpResponse(content='error')

            capture = paypal_payment_info[3]
            logger.info("paypal payment details for buy order {0} is {1}.".format(buy_order_id, capture))

            if capture.status.lower() == 'completed' :
                ordermanager.confirm_purchase_order(buy_order_id, 'admin')
                return HttpResponse(content='OK')
            elif capture.status.upper() == 'PENDING' and capture.status_details.reason.upper() == "RECEIVING_PREFERENCE_MANDATES_MANUAL_ACTION":
                # TODO: shouldn't confirm purchase since the payment is waiting for user accept. We may need to defer to a background job to confirm payment, since this require user to manually approve.
                ordermanager.confirm_purchase_order(buy_order_id, 'admin')
                return HttpResponse(content='OK')

        return HttpResponse(content='error')
    except Exception as e:
        error_msg = 'Confirmation processing hit exception: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if request.method == 'GET':
            return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
                                            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
        else:
            return HttpResponse(content='error')