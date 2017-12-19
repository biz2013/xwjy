from .singletonmodel SingletonModel

class SiteSettings(SingletonModel):
    support = models.EmailField(default='support@example.com')
    heepay_notify_url_host = models.CharField(default='localhost')
    heepapy_notify_url_port = models.IntegerField(default=8000)
    
