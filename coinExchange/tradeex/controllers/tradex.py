#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from trading.views.models.orderitem import *
from trading.models import *
from tradeex.models import *
from trading.controller import ordermanager

import logging
import datetime as dt
import pytz

logger = logging.getLogger("tradeex.tradeexchangemanager")

class TradeExchangeManager(object):
    def get_order_owner_account_at_payment_provider(self, order, payment_provider, api_call_order_id):
        try:
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
        return Order.objects.filter(Q(status='OPEN') & Q(order_type='SELL') &
               ~Q(sub_type='ALL_OR_NOTHING') & Q(total_amount__gt=amount) & 
               Q(unit_price_currency=currency) & Q(cryptocurrency=crypto)).order_by('total_amount', '-created_at')

    def get_active_sell_orders(self, crypto, currency):
        return Order.objects.filter(Q(status='OPEM') & Q(order_type='BUY') &
                Q(unit_price_currency=currency) & Q(cryptocurrency=crypto)).order_by('total_amount', '-created_at')

    def find_transaction(self, trx_bill_no):
        return APIUserTransaction.objects.get(pk=trx_bill_no)

    def decide_sell_price(self, orders):
        min_price_normal_order = 1000000.0
        min_price_api_order = 1000000.0
        max_price_normal_order = 0.0
        suggested_price = 0.0
        for order in orders:
            if (order.order_source == 'TRADESITE'):
                if order.unit_price - min_price_normal_order < 0:
                    min_price_normal_order = order.unit_price
                if order.unit_price - max_price_normal_order > 0:
                    max_price_normal_order = order.unit_price
            elif (order.order_source == 'API' and order.unit_price - min_price_normal_order < 0):
                min_price_api_order = order.unit_price

        if min_price_normal_order < min_price_api_order:
            suggested_price = max([0.05, min_price_normal_order * .95])
        else:
            if min_price_api_order < max_price_normal_order:
                suggested_price = max([0.05, min_price_api_order + 0.01, min_price_api_order * 1.005])
            else:
                suggested_price = max([0.05, min([min_price_api_order - 0.01, min_price_api_order * 0.995])])
        
        return suggested_price
                



    # after issue payment command, payment provider will return a bill no, and we need to
    # record that with the api transaction
    def update_api_trans_with_bill_no(self, api_trans_id, payment_bill_no):
        return APIUserTransaction.objects.filter(transactionId = api_trans_id).update(
                reference_bill_no = payment_bill_no
                )

    def purchase_by_cash_amount(self, api_user, request_obj, crypto, is_api_call=True):
        api_user_id = api_user.user.id
        amount = request_obj.total_fee
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
            raise ValueError('NOT_SELL_ORDER_FOUND')    


        for sell_order in qualify_orders:
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

            seller_payment_provider = buyer_payment_provider
            seller_payment_account = ''
            try:
                seller_payment_account = self.get_order_owner_account_at_payment_provider(
                    sell_order, buyer_payment_provider, api_call_order_id)
                logger.info("purchase_by_cash_amount(): [out_trade_no:{0}] get target sell order {1}'s payment account {2}:{3}".format(
                    api_call_order_id, sell_order.order_id, buyer_payment_provider, seller_payment_account
                ))
            except ValueError as ve:
                logger.warn('purchase_by_cash_amount(): [out_trade_no:{0}] Cannot find the seller\'s dedicated account in payment provider {1}, move to the next order'.format(
                    api_call_order_id, buyer_payment_provider))
                continue
            
            buyorder_id = None
            try:
                api_trans_id = 'API_TX_{0}'.format(
                    dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
                )
                buyorder_id = ordermanager.create_purchase_order(order_item, sell_order.order_id, 
                    buyer_payment_provider, 'admin', 
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
            
            return api_trans_id, buyorder_id, seller_payment_account

        if qualify_orders:
            logger.error("purchase_by_cash_amount(): [out_trade_no:{0}] None of the qualified sell order could be secured for purchase.".format(
                api_call_order_id
            ))
        raise ValueError('NOT_SELL_ORDER_CAN_BE_LOCKED')    
    
    def handle_payment_notificiation(self, payment_provider, notification, api_trans):
        if payment_provider != 'heepay':
            raise ValueError('handle_payment_notificiation(): {0} is not supported')
        
        ordermanager.update_order_with_heepay_notification(notification.original_json, 'admin', api_trans)     
        api_trans.refresh_from_db()
        return api_trans


    def post_sell_order(self, request_obj, api_user):
        current_sell_orders = self.get_active_sell_orders('AXFund', 'CNY')
        unit_price = self.decide_sell_price(current_sell_orders)
        api_trans_id = 'API_TX_{0}'.format(
                dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
        )
        order_item = OrderItem('', # order_id empty for purchase
               api_user.user.id, 
               '',  # no need for user login of the order
               unit_price,
               'CNY',
               round(reqeust_obj.total_fee / unit_price, 8),
               0,  # no need for available_units
               reqeust_obj.total_fee,
               'AXFund',
               '', # no need for lastmodified_at
               '', # no need for status
               'BUY',
               sub_type='ALL_OR_NOTHING',
               selected_payment_provider= request_obj.payment_provider,
               account_at_payment_provider = request_obj.payment_account,
               order_source = 'API') # order type is buy
        order_id = ordermanager.create_sell_order(order, 'admin', api_user, request_obj, api_trans_id)
        return api_trans_id, order_id

    
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
            