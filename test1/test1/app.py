from django.shortcuts import render
from users.models import Cryptocurrency, User, UserLogin, Order

def home(request):
    """Show the home page."""
    return render(request, 'html/index.html')

def create_sell_order(request):
    userobj = User.objects.get(login_id = request.GET.get('username'))
    user_login = UserLogin.objects.get(username = request.GET.get('username'))
    crypto = Cryptocurrency.objects.get(currency_code = 'AXFund')
    order = Order.objects.create(
        user= userobj,
        created_by = user_login,
        lastupdated_by = user_login, 
        reference_order=None, 
        cryptocurrencyId= crypto,
        order_type='SELL',
        sub_type = 'OPEN',
        units = float(request.GET.get('quantity')),
        unit_price = float(request.GET.get('unitprice')),
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

def mysellorder(request):
    action = request.GET.get('action')
    if action is not None and action == 'create_order':
       return create_sell_order(request)
    return render(request, 'html/mysellorder.html', {'username':'taozhang'})
