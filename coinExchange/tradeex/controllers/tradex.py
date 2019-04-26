#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.conf import settings
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from tradeex.data.api_const import *
from tradeex.models import *
from tradeex.utils import *
from tradeex.data.tradeapiresponse import TradeAPIResponse
from tradeex.responses.heepayresponse import HeepayResponse
from trading.views.models.orderitem import *
from trading.models import *
from trading.controller import ordermanager, userpaymentmethodmanager
from trading.controller.heepaymanager import *
from trading.controller.global_constants import *


import logging
import datetime as dt
import pytz

logger = logging.getLogger("tradeex.tradeexchangemanager")

# in case in the future we need to reconstruct the
# response from trade exchange.  For now, it is
# just straight return
def create_prepurchase_response_from_heepay(heepay_response, api_user, api_trans_id, api_out_trade_no,
        subject=None, attach = None):
    
    response = TradeAPIResponse(
        api_user.apiKey, api_user.secretKey,
        heepay_response.return_code, 
        heepay_response.return_msg, 
        heepay_response.result_code,
        heepay_response.result_msg,
        api_out_trade_no,
        api_trans_id,
        subject = subject,
        attach = attach,
        total_fee = heepay_response.total_fee,
        payment_url = heepay_response.hy_url
    )

    return response.to_json()       


class TradeExchangeManager(object):

    # decide whether the user advertised payment method match what sell order 
    # dictate:
    #  1. As long as sell order does not have payment method explicitly assigned, we say it does not match.  
    #  2. If sell order dicated payment method does not have qrcode and that method is flag as 'manual', 
    #     we say it does not match
    #  3. If old buyer call use heepay but sell order has weixin setup, we say it matches
    #  4. If buyer and seller expect same payment method, we call it match
    #  5. Otherwise it is not match
    def payment_method_is_match(self, seller_payment_method, buyer_payment_provider, api_call_order_id, sell_order_id):
        if not seller_payment_method:
            logger.warn('purchase_by_cash_amount(): [out_trade_no:{0}] sell order {1} has no payment method setup, move to the next order'.format(
                api_call_order_id, sell_order_id))
            return False

        if not seller_payment_method.provider_qrcode_image and settings.PAYMENT_API_STATUS[seller_payment_method.provider.code] == 'manual':
            logger.warn('purchase_by_cash_amount(): [out_trade_no:{0}] sell order {1} has not setup payment qrcode for manual process, move to the next order'.format(
                api_call_order_id, sell_order_id))
            return False
        
        if buyer_payment_provider == seller_payment_method.provider.code or (buyer_payment_provider == PAYMENTMETHOD_HEEPAY and seller_payment_method.provider.code == PAYMENTMETHOD_WEIXIN):
            return True
        
        logger.warn('purchase_by_cash_amount(): [out_trade_no:{0}] sell order {1} ask for {2} but buyer requested {3} as payment provider, move to the next order'.format(
            api_call_order_id, sell_order_id, seller_payment_method.provider.code, buyer_payment_provider))

        return False

    def create_manual_payment_url(self, api_user, api_trans_id, buy_order_id):
        return '{0}?key={1}'.format(settings.TRADESITE_PAYMENT_URLPREFIX, buy_order_id)

    def get_order_owner_account_at_payment_provider(self, order, payment_provider, api_call_order_id):
        if order and order.account_at_selected_payment_provider and order.selected_payment_provider.code == payment_provider:
            return order.account_at_selected_payment_provider
        try:
            logger.info('get_order_owner_account_at_payment_provider({0},{1},{2}): order does not have account #, query user payment method of the order owner'.format(
                order.order_id, payment_provider, api_call_order_id
            ))
            payment_method = UserPaymentMethod.objects.get(
                 user = order.user,
                 provider__code = payment_provider)
            return payment_method.account_at_provider
        except UserPaymentMethod.DoesNotExist:
            logger.error('get_order_owner_account_at_payment_provider(): [out_trade_no:{0}] order {1} does not have the required payment provider {2}'.format(
                api_call_order_id, order.order_id, payment_provider)
            )
            raise ValueError('PAYMENT_ACCOUNT_NOT_FOUND')
        except UserPaymentMethod.MultipleObjectsReturned:
            logger.info('get_order_owner_account_at_payment_provider(): [out_trade_no:{0}] order {1} owner {2} has multiple accounts with payment provider {3}'.format(
                api_call_order_id, order.order_id, order.user.id, payment_provider)
            )
            raise ValueError('TOO_MANY_ACCOUNTS_AT_PROVIDER')
        
    def get_qualified_orders_to_buy(self, crypto, amount, currency):
        # query all the orders that best fit the buy order
        candidates = []
        orders =  Order.objects.filter(
            (Q(status='OPEN') | Q(status='PARTIALFILLED')) & 
            Q(order_type='SELL') & Q(units_available_to_trade__gt=0.0) &
            Q(unit_price_currency=currency) &
            Q(cryptocurrency__currency_code=crypto)).order_by('unit_price', 'total_amount','created_at')
        for order in orders:
            available_amount = order.unit_price * order.units_available_to_trade
            diff = round(available_amount - amount, 2)
            if diff >= 0.0:
                if order.sub_type == 'ALL_OR_NOTHING':
                    if diff > 0.01:
                        continue
                candidates.append(order)

        return candidates if len(candidates) > 0 else None

    def get_active_sell_orders(self, crypto, currency, userId):
        return Order.objects.filter(
            ~Q(user__id = userId)
            & (Q(status='OPEN') or Q(status='PARTIALFILLED')) 
            & Q(order_type='SELL') 
            & Q(unit_price_currency=currency) 
            & Q(cryptocurrency__currency_code=crypto)).order_by('total_amount', '-created_at')

    def find_transaction(self, trx_bill_no):
        return APIUserTransaction.objects.get(pk=trx_bill_no)

    def decide_sell_price(self, orders):
        min_price_normal_order = 1000000.0
        min_price_api_order = 1000000.0
        max_price_normal_order = 0.0
        suggested_price = 0.0
        for order in orders:
            logger.info('decide_sell_price(): order {0}, unit price {1} source {2} type {3}'.format(
                order.order_id, order.unit_price, order.order_source, order.order_type
            ))
            if (order.order_source == 'TRADESITE'):
                if order.unit_price - min_price_normal_order < 0:
                    min_price_normal_order = order.unit_price
                if order.unit_price - max_price_normal_order > 0:
                    max_price_normal_order = order.unit_price
            elif (order.order_source == 'API' and order.unit_price - min_price_normal_order < 0):
                min_price_api_order = order.unit_price
        
        if not orders or len(orders) == 0:
            logger.info('decide_sell_price(): no sell order found, clear min prices')
            min_price_normal_order = 0
            min_price_api_order = 0
        
        logger.info("decide_sell_price(): min /maxorder price {0}/{1} min api price {2}".format(
            min_price_normal_order, max_price_normal_order, min_price_api_order
        ))
        if min_price_normal_order < min_price_api_order:
            suggested_price = max([0.05, min_price_normal_order * .95])
            logger.debug("decide_sell_price(): get redeem price {0} that is 5% lower than min trade price {1}, but not lower than 0.05".format(
                suggested_price, min_price_normal_order
            ))
            
        else:
            suggested_price = max([0.05, min_price_api_order + 0.01, min_price_api_order * 1.005])
            if suggested_price > min_price_normal_order:
                suggested_price = max([0.05, min([min_price_api_order - 0.01, min_price_api_order * 0.995])])
                logger.debug("decide_sell_price(): get redeem price {0} that is 0.05% (or at least 0.01) lower than min api price {1}, but not lower than 0.05".format(
                    suggested_price, min_price_api_order
                ))
            else:
                logger.debug("decide_sell_price(): get redeem price {0} that is 0.05% (or at least 0.01) higher than min api price {1}, but not lower than 0.05".format(
                    suggested_price, min_price_api_order
                ))                

        return suggested_price

    # after issue payment command, payment provider will return a bill no, and we need to
    # record that with the api transaction
    def update_api_trans_with_bill_no(self, api_trans_id, payment_bill_no):
        return APIUserTransaction.objects.filter(transactionId = api_trans_id).update(
                reference_bill_no = payment_bill_no
                )

    def find_last_transaction_price(self, crypto, currency):
        processed_purchases = Order.objects.filter(
            Q(status='FILLED') & 
            Q(order_type='BUY') & Q(total_amount__gt=0.0) &
            Q(unit_price_currency=currency) &
            Q(cryptocurrency__currency_code=crypto)).order_by('-lastupdated_at')
        if not processed_purchases or len(processed_purchases) == 0:
            raise ValueError(ERR_NO_SELL_ORDER_TO_SUPPORT_PRICE)
        return processed_purchases[0].unit_price    

    # This function wrap old routine that call heepay to create order
    # It will return heepay's response which contains the payment url that will be
    # shown to the buyer
    def create_response_based_on_heepay_call(self, buyerorder_id, request_obj, seller_payment_account, sitesettings, api_user,api_trans_id):
        notify_url = settings.HEEPAY_NOTIFY_URL_FORMAT.format(
        sitesettings.heepay_notify_url_host,
        sitesettings.heepay_notify_url_port)
        return_url = request_obj.return_url
        
        heepay_api_key = sitesettings.heepay_app_id
        heepay_api_secret = sitesettings.heepay_app_key
        
        heepay = HeePayManager()
        json_payload = heepay.create_heepay_payload('wallet.pay.apply', buyorder_id, heepay_api_key, 
            heepay_api_secret, "127.0.0.1", float(request_obj.total_fee)/100.0,
            seller_payment_account, request_obj.payment_account, 
            notify_url, return_url, request_obj.expire_minute, subject = request_obj.subject)
        try:
            status, reason, message = heepay.send_buy_apply_request(json_payload)
        except:
            logger.error('purchase_by_cash_amount(): sending request to heepay hit exception {0}'.format(
                sys.exc_info()[0]
            ))
            raise ValueError(ERR_HEEPAY_REQUEST_EXCEPTION)
        response_json = json.loads(message) if status == 200 else None
        if status != 200:
            logger.error('purchase_by_cash_amount(): sending request to heepay get error {0}:{1}-{2}'.format(
                status, reason, message
            ))
            raise ValueError(ERR_HEEPAY_REQUEST_ERROR)

        # TODO: hard coded right now
        #api_client = APIClient('https://wallet.heepay.com/api/v1/payapply')
        #response_json = api_client.send_json_request(heepay_request)
        logger.info("prepurchase(): [out_trade_no:{0}] heepay reply: {1}".format(
            request_obj.out_trade_no, json.dumps(response_json, ensure_ascii=False)
        ))

        if response_json['return_code'] == 'SUCCESS':
            ordermanager.post_open_payment_order(
                        buyorder_id, 'heepay',
                        response_json['hy_bill_no'],
                        response_json['hy_url'],
                        api_user.user.username)
            
            heepay_response = HeepayResponse.parseFromJson(response_json, heepay_api_secret)
            final_resp_json = create_prepurchase_response_from_heepay(
                heepay_response, api_user,api_trans_id, request_obj.out_trade_no,
                request_obj.subject, request_obj.attach)
            logger.info('prepurchase(): send final reply {0}'.format(
                json.dumps(final_resp_json, ensure_ascii=False)
            ))
            return final_resp_json
        else:
            if response_json['return_msg'] == HEEPAY_ERR_NONEXIST_RECEIVE_ACCOUNT:
                logger.error('purchase_by_cash_amount(): target sell order {0} had bad account, cancel the sell order and the purchase order'.format(
                    sell_order.order_id
                ))
                purchase_order = Order.objects.get(order_id=buyorder_id)
                admin = User.objects.get(username='admin')

                # cancel purchase order will flag sell order as bad account here
                ordermanager.cancel_purchase_order(purchase_order, TRADE_STATUS_BADRECEIVINGACCOUNT, 
                    PAYMENT_STATUS_BADRECEIVINGACCOUNT, admin)
            else:
                logger.error('purchase_by_cash_amount(): submit heepay request for seller order {0} hit error {1}.  Move to next one'.format(
                    sell_order.order_id, response_json['return_msg']
                ))
            return None  

    # This is the interface that handles the api call of purchase
    def purchase_by_cash_amount(self, api_user, request_obj, crypto, sitesettings, is_api_call=True):
        api_user_id = api_user.user.id
        amount_in_cent = int(request_obj.total_fee) 
        amount = float(amount_in_cent / 100.0)
        currency = 'CNY'

        buyer_payment_provider = request_obj.payment_provider
        buyer_payment_account =  request_obj.payment_account
        api_call_order_id =  request_obj.out_trade_no
        logger.info("purchase_by_cash_amount(api_user:{0}, crypto {1}, amount {2}{3}, from account {4}:{5}, out_trade_no:{6})".format(
            api_user_id,  crypto, amount, currency, buyer_payment_provider, 
            buyer_payment_account, api_call_order_id,
        ))

        qualify_orders = self.get_qualified_orders_to_buy(crypto, amount, currency)
        if qualify_orders:
            logger.info("purchase_by_cash_amount(): [out_trade_no {0}] Find {1} qualified sell orders to buy from".format(
                api_call_order_id, len(qualify_orders)))
        else:
            raise ValueError(ERR_NO_RIGHT_SELL_ORDER_FOUND)    

        for sell_order in qualify_orders:
            logger.info('Try to purchase order {0}amount {1}'.format(
                sell_order.order_id, round(amount / sell_order.unit_price, 8)))
            order_item = OrderItem('', # order_id empty for purchase
               api_user_id, 
               '',  # no need for user login of the order
               sell_order.unit_price,
               sell_order.unit_price_currency,
               round(amount / sell_order.unit_price, 8),
               0,  # no need for available_units
               amount,
               crypto,
               '', # no need for lastmodified_at
               '', # no need for status
               'BUY') # order type is buy

            # this is for backward compatible with heepay api call
            seller_payment_account = ''

            seller_payment_method = None
            seller_payment_method = sell_order.seller_payment_method if sell_order.seller_payment_method else userpaymentmethodmanager.get_weixin_paymentmethod(sell_order.user.id)
            
            if not self.payment_method_is_match(seller_payment_method, buyer_payment_provider, 
                                                api_call_order_id, sell_order.order_id):
                continue
        
            # in case heepay api is working again... we need more logic
            if buyer_payment_provider == PAYMENTMETHOD_HEEPAY and settings.PAYMENT_API_STATUS[PAYMENTMETHOD_HEEPAY] == 'auto':
                seller_payment_account = seller_payment_method.account_at_payment_provider
            
            buyorder_id = None
            try:
                api_trans_id = 'API_TX_{0}'.format(
                    dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
                )

                logger.info('come to create order api_trans_id: {0}'.format(api_trans_id))
                buyorder_id = ordermanager.create_purchase_order(order_item, sell_order.order_id, 
                    seller_payment_method.provider.code, 'admin', 
                    api_user, request_obj, api_trans_id
                )
            except ValueError as ve:
                if ve.args[0] == 'SELLORDER_NOT_OPEN':
                    logger.warn('purchase_by_cash_amount(): [out_trade_no:{0}] This sell order {1} was locked, move to the next'.format(
                        api_call_order_id, sell_order.order_id))
                elif ve.args[0] == 'BUY_EXCEED_AVAILABLE_UNITS':
                    logger.error('purchase_by_cash_amount(): [out_trade_no:{0}] This sell order {1}\'s total amount {2} is less than the purchase amount {3}, this SHOULD NOT HAPPEN, move to the next'.format(
                        api_call_order_id, sell_order.order_id, sell_order.total_amount, amount) )
                else:
                    logger.error('purchase_by_cash_amount(): [out_trade_no:{0}] Hit error {1} when trying to buy from sell order {2}'.format(
                        api_call_order_id, sell_order.order_id, ve.args[0]
                    ))
                continue
        
            if not buyorder_id:
                logger.warn('purchase_by_cash_amount(): [out_trade_no:{0}] Sell order {1} cannot be secured, move to the next candidate'.format(
                    api_call_order_id, sell_order.order_id))
                continue
            
            # This part is the legacy heepay call.  It will call heepay to create purchase order, extract
            # the payment url and return that to caller.
            if request_obj.payment_provider == 'heepay' and settings.PAYMENT_API_STATUS['heepay'] == 'auto':
                final_response = create_response_based_on_heepay_call(buyerorder_id, request_obj, seller_payment_account, 
                    sitesettings, api_user,api_trans_id)
                if final_response:
                    return final_response
            
            payment_url = self.create_manual_payment_url(api_user, api_trans_id, buyorder_id)
            ordermanager.post_open_payment_order(
                buyorder_id, seller_payment_method.provider.code,
                '',
                payment_url,
                api_user.user.username)

            return TradeAPIResponse(
                api_user.apiKey, api_user.secretKey,
                'SUCCESS', 
                '', 
                'SUCCESS',
                '',
                request_obj.out_trade_no,
                api_trans_id,
                subject = request_obj.subject,
                attach = request_obj.attach,
                total_fee = request_obj.total_fee,
                payment_url = payment_url
            ).to_json()
        
        if qualify_orders:
            logger.error("purchase_by_cash_amount(): [out_trade_no:{0}] None of the qualified sell order could be secured for purchase.".format(
                api_call_order_id
            ))
        raise ValueError(ERR_NO_RIGHT_SELL_ORDER_FOUND)    
    
    def handle_payment_notificiation(self, payment_provider, notification, api_trans):
        logger.debug('handle_payment_notificiation()')
        if payment_provider != 'heepay':
            raise ValueError('handle_payment_notificiation(): {0} is not supported')
        
        ordermanager.update_order_with_heepay_notification(notification.original_json, 'admin', api_trans)     
        api_trans.refresh_from_db()
        return api_trans


    def post_sell_order(self, request_obj, api_user, api_trans=None):
        if not request_obj and not api_trans:
            raise ValueError('post_sell_order(): request_obj and api_trans cannot be None at the same time')
        current_sell_orders = self.get_active_sell_orders('AXFund', 'CNY' , api_user.user.id)
        if current_sell_orders:
            unit_price = round(self.decide_sell_price(current_sell_orders),2)
        else:
            unit_price = self.find_last_transaction_price('AXFund','CNY')

        logger.info("post_sell_order(): get round-up sell price {0}".format(unit_price))
        if not api_trans:
            api_trans_id = 'API_TX_{0}'.format(
                    dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
            )
        else:
            api_trans_id = api_trans.transactionId
        
        amount_in_cent = int(request_obj.total_fee) if type(request_obj.total_fee) is str else request_obj.total_fee
        amount = float(amount_in_cent / 100.0)
        sell_units = round(amount / unit_price, MIN_CRYPTOCURRENCY_UNITS_DECIMAL)
        logger.info("post_sell_order(): after roundup, sell {0} yuan of axfund = {1} x @{2}".format(
            amount, sell_units, unit_price))
        
        order_item = OrderItem('', # order_id empty for purchase
               api_user.user.id, 
               '',  # no need for user login of the order
               unit_price,
               'CNY',
               sell_units,
               0,  # no need for available_units
               amount,
               'AXFund',
               '', # no need for lastmodified_at
               '', # no need for status
               'SELL',
               sub_type='ALL_OR_NOTHING',
               selected_payment_provider= request_obj.payment_provider if request_obj else None,
               account_at_payment_provider = request_obj.payment_account if request_obj else None,
               order_source = 'API') # order type is buy
        order_id = ordermanager.create_sell_order(order_item, 'admin', api_user, request_obj, api_trans_id)
        return APIUserTransactionManager.get_transaction_by_id(api_trans_id), order_id

    
    def confirm_order(self):
        pass

    def cancel_order(self):
        pass
    
    def query_order_status(self, out_trade_no, trx_bill_no):
        try:
            return APIUserTransaction.objects.get(transactionId=trx_bill_no, out_trade_no=out_trade_no)
        except APIUserTransaction.DoesNotExist:
            logger.error('query_order_status(out_trade_no={0},trx_bill_no={1}) could not be found'.format(
                out_trade_no, trx_bill_no
            ))
            raise ValueError('API_TRANS_NOT_FOUND')
        except APIUserTransaction.MultipleObjectsReturned:
            logger.error('query_order_status(out_trade_no={0},trx_bill_no={1}) found too many'.format(
                out_trade_no, trx_bill_no
            ))
            raise ValueError('API_TRANS_NOT_FOUND')
            
