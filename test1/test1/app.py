#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from users.models import PaymentProvider

#from model_manager import ModelManager

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from users.models import Cryptocurrency, User, UserLogin, Order
from views.sellorderview import SellOrderView

def home(request):
    """Show the home page."""
    return render(request, 'html/index.html')

def login(request):
    login = UserLogin()
    if request.method == 'POST':
        login.username = request.POST['username']
        login.password = request.POST['password']
        manager = ModelManager()
        rc, msg, user = manager.login(login.username, login.password)
        if rc == 0:
            request.session['username'] = login.username
            request.session['userid'] = user.id

            forwardto = request.POST['forwardto']
            if forwardto:
                return redirect(forwardto)
            else:
                return redirect("accountinfo")
        else:
            return render(request, "html/login.html",
               {'message': msg, 'login':login})
    else:
        return render(request, "html/login.html",
            { 'login' : login})

def registration(request):
    login = UserLogin()
    user = User()
    user.login = login
    if request.method == 'POST':
        login.username = request.POST['username']
        login.password = request.POST['password']
        user.email = request.POST['email']
        print "registration: username %s password %s email %s" % (login.username, login.password, user.email)
        manager = ModelManager()
        rc, msg = manager.register(user)
        if 0 == rc:
            return render(request, 'html/login.html',
              {'message':msg, 'message_type':'success',
              'login': User()})
        return render(request,'html/register.html',
              {'message':msg, 'message_type':'fail', 'registration':user})
    else:
        return render(request,'html/register.html',
              {'registration':user})

def external_address(request):
    manager = ModelManager()
    if request.method == 'GET':
       user_id = int(request.GET.get('id'))
       user_addr = manager.get_user_address(user_id)
       return render(request, 'html/update_external_address.html',
            { 'user_external_address': user_addr })
    else:
        user_id = int(request.POST['userId'])
        address = request.POST['address']
        alias = request.POST['alias']
        rc, message = manager.upsert_user_external_address(user_id, address, alias)
        if rc == 0:
            useraccountInfo = manager.get_user_accountInfo(request.session['username'])
            return render(request, 'html/myaccount.html', {'useraccountInfo': useraccountInfo})
        else:
            user_addr = manager.get_user_address(user_id)
            return render(request, 'html/update_external_adress.html',
               { 'user_external_address': user_addr })
def payment_method(request):
    manager = ModelManager()
    payment_providers = []
    provider = PaymentProvider()
    provider.code = 'weixin'
    provider.name = '微信支付'
    payment_providers.append(provider)
    provider = PaymentProvider()
    provider.code = 'alipay'
    provider.name = '支付宝'
    payment_providers.append(provider)
    provider = PaymentProvider()
    provider.code = 'heepay'
    provider.name = '汇钱包'
    payment_providers.append(provider)

    if request.method == 'GET':
        userid = int(request.GET.get('id'))
        user_payment_methods = manager.get_user_payment_methods(userid)
        return render(request, 'html/update_payment_method.html',
            {'user_payment_methods':user_payment_methods,
             'userid': userid,
             'payment_providers': payment_providers})
    else:
        userid = int(request.POST['id'])
        payment_provider = request.POST['payment_provider']
        account = request.POST['account']
        rc, msg = manager.upsert_user_payment_method(userid, payment_provider, account)
        if rc == 0:
            return redirect(request, 'accountinfo', { 'rc': rc, 'message': msg})
        else:
            user_payment_methods = manager.get_user_payment_methods(userid)
            return render(request, 'html/update_payment_method.html',
               {'user_payment_methods':user_payment_methods,
                'userid': userid,
                'payment_providers': payment_providers})

def accountinfo(request):
    manager = ModelManager()
    useraccountInfo = manager.get_user_accountInfo(request.session['username'])
    return render(request, 'html/myaccount.html', {'useraccountInfo': useraccountInfo})

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
    print "receive order id %s" % (order_id)
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

def transfer(request):
    return render(request, 'html/myaccount.html')

def mysellorder(request):
    if request.method == 'POST':
       return create_sell_order(request)
    sellorders = query_user_open_sell_orders('taozhang')
    buyorders = query_buy_orders('taozhang')
    print "There is %d orders--- ".format(len(sellorders))
    return render(request, 'html/mysellorder.html', {'sellorders': sellorders, 'buyorders':buyorders,'username':'taozhang'})
