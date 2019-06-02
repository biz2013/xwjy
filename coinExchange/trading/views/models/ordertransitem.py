class OrderTransactionItem(object):
    def __init__(self,order_id, buyer_username, buyer_weixin_nickname, buyer_site,
        seller_username, seller_weixin_nickname, seller_site,
        trade_source, units, total_amount, unit_price, unit_price_currency,
        order_status, sell_order_source, created_at, lastupdated_at):

        self.order_id = order_id
        self.buyer_username =  buyer_username
        self.buyer_weixin_nickname = buyer_weixin_nickname
        self.buyer_site = buyer_site
        self.seller_username = seller_username
        self.seller_weixin_nickname = seller_weixin_nickname
        self.seller_site = seller_site
        self.trade_source = trade_source
        self.units = units
        self.total_amount = total_amount
        self.unit_price = unit_price
        self.unit_price_currency = unit_price_currency
        self.order_status = order_status
        self.sell_order_source = sell_order_source
        self.created_at = created_at
        self.lastupdated_at = lastupdated_at
