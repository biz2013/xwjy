class OrderItem(object):
   def __init__(self, order_id, owner_user_id, owner_login, unit_price,
         unit_price_currency, total_units, available_units, total_amount,
         crypto, lastmodified_at, status, order_type,
         sub_type = 'OPEN',
         selected_payment_provider = None, account_at_payment_provider=None,
         order_source = 'TRADESITE'):
       self.order_id=order_id
       self.owner_user_id = owner_user_id
       self.owner_login = owner_login
       self.unit_price = unit_price
       self.unit_price_currency= unit_price_currency
       self.total_units = total_units
       self.available_units = available_units
       self.total_amount = total_amount
       self.crypto = crypto
       self.lastmodified_at = lastmodified_at
       self.status = status
       self.order_type = order_type
       self.selected_payment_provider = selected_payment_provider
       self.account_at_payment_provider = account_at_payment_provider
       self.order_source = order_source
