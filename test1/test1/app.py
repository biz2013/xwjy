#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render

#from model_manager import ModelManager

# this is for test UI. A fake one
from test_model_manager import ModelManager
from users.models import Cryptocurrency, User, UserLogin, Order
from views.sellorderview import SellOrderView

def home(request):
    """Show the home page."""
    return render(request, 'html/index.html')

def show_sell_orders_for_purchase(request):
    manager = ModelManager()
    sellorders = manager.query_active_sell_orders()
    print "--- there are %d ---" % (len(sellorders))
    for order in sellorders:
       print "--- order id is %d --" % (order.id)
    return render(request, 'html/purchase.html',
           {'sellorders': sellorders, 'username':'taozhang'
            }
           )
def show_purchase_input(request):
    manager = ModelManager()
    owner_user_id = request.POST["owner_user_id"]
    order_id = request.POST["reference_order_id"]
    print "receive order id %d" & (order_id)
    owner_payment_methods = manager.get_user_payment_methods(owner_user_id)
    for method in owner_payment_methods:
        print ("provider %s has image %s" % (method.provider_name, method.qrcode_image))
    sellorder = SellOrderView(
       request.POST["reference_order_id"],
       owner_user_id,
       request.POST["locked_in_unit_price"],
       'CYN',
       request.POST["available_units_for_purchase"],
       owner_payment_methods)
    print 'sellorder id is here %s' % (sellorder.order_id)
    login = request.POST['username']
    return render(request, 'html/input_purchase.html',
           {'username':'taozhang',
            'sellorder': sellorder }
           )

def create_sell_order(request):
    login = request.POST['username']
    userobj = User.objects.get(login_id = login)
    user_login = UserLogin.objects.get(username = login)
    crypto = Cryptocurrency.objects.get(currency_code = 'AXFund')
    order = Order.objects.create(
        user= userobj,
        created_by = user_login,
        lastupdated_by = user_login,
        reference_order=None,
        cryptocurrencyId= crypto,
        order_type='SELL',
        sub_type = 'OPEN',
        units = float(request.POST['quantity']),
        unit_price = float(request.POST['unitprice']),
        unit_price_currency = 'CYN',
        status = 'OPEN')
    order.save()
    return render(request, 'html/mysellorder.html', {'username':'taozhang'})

    """
   ORDER_TYPE = (('BUY','Buy'),('SELL','Sell'))
   CURRENCY = (('CYN', 'Renminbi'), ('USD', 'US Dollar'))
   STATUS = (('OPEN','OPEN'), ('CANCELLED','CANCELLED'), ('PARTIALFILLED', 'PARTIALFILLED'), ('FILLED','FILLED'))
   user = models.ForeignKey('User', on_delete=models.CASCADE)
   reference_order = models.ForeignKey('self', null=True)
   cryptocurrencyId = models.ForeignKey('Cryptocurrency')
   reference_wallet = models.ForeignKey('Wallet', null= True)
   reference_wallet_trxId = models.CharField(max_length=128, null = True)
   order_type = models.CharField(max_length=8, choices=ORDER_TYPE)
   sub_type = models.CharField(max_length=16, default='')
   units = models.FloatField()
   unit_price = models.FloatField()
   unit_price_currency = models.CharField(max_length = 8, choices=CURRENCY, default='CYN')
   status = models.CharField(max_length=32, choices=STATuS)

    """

def query_user_open_sell_orders(userlogin):
    return Order.objects.filter(user__login = userlogin).filter(order_type='SELL').filter(~Q(status='FILLED') | ~Q(status='CANCELLED'))

def query_buy_orders(userlogin):
    return Order.objects.select_related('reference_order','reference_order__user').filter(reference_order__user__login= userlogin)

def mysellorder(request):
    if request.method == 'POST':
       return create_sell_order(request)
    sellorders = query_user_open_sell_orders('taozhang')
    buyorders = query_buy_orders('taozhang')
    print "There is %d orders--- ".format(len(sellorders))
    return render(request, 'html/mysellorder.html', {'sellorders': sellorders, 'buyorders':buyorders,'username':'taozhang'})
