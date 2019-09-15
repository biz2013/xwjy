import logging, json, sys

from django.contrib.auth.decorators import login_required

from tradeex.data.api_const import *
from trading.models import UserWalletTransaction

sys.path.append('../stakingsvc/')

from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseServerError

from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.heepaymanager import *
from trading.controller import ordermanager
from trading.controller import userpaymentmethodmanager
from trading.views import errorpageview
from trading.controller.paypalclient import PayPalClient
from paypalcheckoutsdk.orders import OrdersGetRequest, OrdersCreateRequest
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

  # 2. Set up your server to receive a call from the client
  """You can use this function to retrieve an order by passing order ID as an argument"""

  def get_order(self, order_id):
    """Method to get order"""
    request = OrdersGetRequest(order_id)
    # 3. Call PayPal to get the transaction

    # TODO: error handling on paypal check.
    response = self.client.execute(request)
    # 4. Save the transaction in your database. Implement logic to save transaction to your database for future reference.
    print('Status Code: ', response.status_code)
    print('Status: ', response.result.status)
    print('Order ID: ', response.result.id)
    print('Intent: ', response.result.intent)

    print('Gross Amount: {} {}'.format(response.result.purchase_units[0].amount.currency_code,
                                       response.result.purchase_units[0].amount.value))

    return (response.result.purchase_units[0].amount,  # amount
            response.result.purchase_units[0].reference_id,  # buy order id
            response.result.purchase_units[0].description,  # seller id / sell order id
            response.result.purchase_units[0].payments.captures[0],  # payment detail status
            response.result
            )

  def create_order(self, buy_order_id, total_amount, description, unit_price_currency, debug=False):
    request = OrdersCreateRequest()
    request.prefer('return=representation')
    # 3. Call PayPal to set up a transaction
    request.request_body(self.build_purchase_order_body(buy_order_id, total_amount, description, unit_price_currency))
    response = self.client.execute(request)
    if debug:
      print('Status Code: ', response.status_code)
      print('Status: ', response.result.status)
      print('Order ID: ', response.result.id)
      print('Intent: ', response.result.intent)

    return response

  def build_purchase_order_body(self, buy_order_id, total_amount, description, unit_price_currency):
    """Method to create body with CAPTURE intent"""
    return \
      {
        "intent": "CAPTURE",
        "application_context": {
          "shipping_preference": "NO_SHIPPING",
        },
        "purchase_units": [
          {
            "reference_id": buy_order_id,
            "description": description,

            "amount": {
              "currency_code": unit_price_currency,
              "value": total_amount
            }
          }
        ]
      }

@csrf_exempt
def confirm_paypal_order(request):
  try:
    if request.method == 'POST':
      logger.info("Receive async payment notification ")

      response = request.body.decode('utf-8')
      json_data = json.loads(response)

      buy_order_id = json_data.get('buy_order_id')
      paypal_return_details = json_data.get('details')

      buy_order_info = ordermanager.get_order_info(buy_order_id)
      sell_order_info = buy_order_info.reference_order
      buy_order_transaction_info = ordermanager.get_order_transactions(buy_order_id)

      seller_user_id = sell_order_info.user_id
      paypal_order_id = json_data.get('orderID')

      # TODO: Verify orderID == transaction
      if buy_order_transaction_info.payment_bill_no != paypal_order_id:
        error_msg = "buy order {0} 's transaction id {1} isn't equal to the reference id {2} returned from paypal.". \
          format(buy_order_info.order_id, buy_order_transaction_info.payment_bill_no, paypal_order_id)
        logger.error(error_msg)
        raise Exception(error_msg)

      seller_paypal_payment_method = userpaymentmethodmanager.get_user_paypal_payment_method(seller_user_id)
      if seller_paypal_payment_method == None:
        error_msg = "user {0} didn't set paypal payment, there is no paypal info.". \
          format(seller_user_id)
        logger.error(error_msg)
        raise Exception(error_msg)

      if not seller_paypal_payment_method.client_id or not seller_paypal_payment_method.client_secret:
        error_msg = "seller {0} didn't set up client id or client secret for their paypal payment.". \
          format(seller_user_id)
        logger.error(error_msg)
        return HttpResponse(content='error')

      clientID = seller_paypal_payment_method.client_id
      clientSecret = seller_paypal_payment_method.client_secret

      # TODO: Check return value and error handling
      paypal_payment_info = GetOrder(clientID, clientSecret).get_order(paypal_order_id)

      if paypal_payment_info[4].status.upper() != "COMPLETED":
        error_msg = "Paypal serverside error: {0}, Status Code {1}".format(
          paypal_payment_info[4].status, paypal_payment_info[4].status_code
        )
        raise Exception(error_msg)

      if paypal_order_id != buy_order_transaction_info.payment_bill_no:
        error_msg = "The returned paypal order id doesn't match paypal id of the returned buy order."
        raise Exception(error_msg)

      if len(paypal_return_details['purchase_units']) != 1:
        error_msg = "purchase units returned from paypal confirmation is not 1, detail is {0}".format(
          paypal_return_details)
        raise Exception(error_msg)

      # Validate amount
      if buy_order_info.total_amount != float(paypal_payment_info[0].value):
        error_msg = "payment amount {0} user paid doesn't match with the number from paypal confirmation". \
          format(buy_order_info.total_amount, paypal_payment_info[0].value)
        raise Exception(error_msg)

      if buy_order_info.unit_price_currency != paypal_payment_info[0].currency_code:
        error_msg = "payment currency {0} user paid doesn't match with the currency code from paypal confirmation". \
          format(buy_order_info.unit_price_currency, paypal_payment_info[0].currency_code)
        raise Exception(error_msg)

      capture = paypal_payment_info[3]
      logger.info("paypal payment details for buy order {0} is {1}.".format(buy_order_id, capture))

      if capture.status.lower() == 'completed':
        # Update buy order transaction as "SUCCESS".
        ordermanager.update_purchase_order_payment_transaction(buy_order_id, TRADE_STATUS_SUCCESS, "")
        # Confirm order complete.
        ordermanager.confirm_purchase_order(buy_order_id, buy_order_info.user.username)
        return HttpResponse(content='OK')
      elif capture.status.upper() == 'PENDING' and capture.status_details.reason.upper() == "RECEIVING_PREFERENCE_MANDATES_MANUAL_ACTION":
        # Paid by buyer but unclaimed from seller.
        ordermanager.update_purchase_order_payment_transaction(buy_order_id, TRADE_STATUS_PAYSUCCESS, "")
        return HttpResponse(content='OK')

      error_msg = "UnExpected paypal capture status {0}, status detail is {1}.".format(capture.status, capture.status_details)
      ordermanager.update_purchase_order_payment_transaction(buy_order_id, TRADE_STATUS_FAILURE, error_msg)

    return HttpResponseServerError(content=error_msg)
  except Exception as e:
    error_msg = 'Confirmation processing hit exception: {0}, exception {1}'.format(sys.exc_info()[0], e)
    logger.exception(error_msg)

    ordermanager.update_purchase_order_payment_transaction(buy_order_id, TRADE_STATUS_FAILURE, error_msg)
    return HttpResponseServerError(content=error_msg)
