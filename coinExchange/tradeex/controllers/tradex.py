#!/usr/bin/python
# -*- coding: utf-8 -*-

from trading.models import Order
from trading.controller import ordermanager

class TradeExchangeManager(object):
    def get_order_owner_account_at_payment_provider(self, order, payment_provider):
        try:
            wallet = UserWallet.objects.get(
                 user = order.user,
                 provider__code = payment_provider)
            return wallet.account_at_provider
        except UserWallet.DoesNotExist:
            logger.error('order {0} does not have the required payment provider {1}'.format(
                order.order_id, payment_provider)
            )
            raise ValueError('REQUIRED_ACCOUNT_NOT_FOUND')
        except UserWallet.MultipleObjectsReturned:
            logger.info('order {0} owner {1} has multiple accounts with payment provider {2}'.format(
                order.order_id, order.user.id, payment_provider)
            )
            raise ValueError('TOO_MANY_ACCOUNTS_AT_PROVIDER')
        
    def get_qualified_orders_to_buy(self, crypto, amount, currency):
        # query all the orders that best fit the buy order
        return Order.objects.filter( Q(status='OPEN') & 
               Q(order_type='SELL') & Q(sub_type != 'ALL_OR_NOTHING') &
               Q(total_amount > amount) & Q(unit_currency=currency) &
               Q(cryptocurrency=crypto)).order_by('total_amount', -'createdat')

    def purchase_by_cash_amount(self, api_user_id, crypto, amount, currency, 
        buyer_payment_provider, buyer_payment_account, api_call_order_id, is_api_call=True):
        qualify_orders = self.get_qualified_orders_to_buy(crypto, amount, currency)
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
                    sell_order, buyer_payment_provider)
            except ValueError as ve:
                logger.warn('Cannot find the seller\'s dedicated account in payment provider {0}, move to the next order'.format(buyer_payment_provider))
                continue
            
            buyorder = None
            try:
                buyorder = ordermanager.create_purchase_order(order_item, sell_order.order_id, 
                    buyer_payment_provider, 'admin', 
                    True, # is_api_call = True
                    api_call_order_id
                )
            except ValueError as ve:
                if ve.args[0] == 'SELLORDER_NOT_OPEN':
                    logger.warn('This sell order {0} was locked, move to the next'.format(sell_order.order_id))
                elif ve.args[0] == 'BUY_EXCEED_AVAILABLE_UNITS':
                    logger.error('This sell order {0}\'s total amount {1} is less than the purchase amount {2}, this SHOULD NOT HAPPEN, move to the next'.format(
                        sell_order.order_id, sell_order.total_amount, amount) )
                else:
                    logger.error('Hit error {0} when trying to buy from sell order {0}'.format(
                        sell_order.order_id
                    ))
                continue
        
            if not buyorder:
                logger.warn('Failed to create api buy order for sell order {0}, move to the next candidate'.format(sell_order.order_id))
                continue
            
            return buyorder, seller_payment_account

        raise ValueError('NOT_SELL_ORDER_FOUND')    
    

    def post_sell_order(self):
        pass
    
    def confirm_order(self):
        pass

    def cancel_order(self):
        pass
    
    def query_order_status(self):
        pass