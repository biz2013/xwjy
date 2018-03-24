from trading.models import SiteSettings

def settings(request):
    return {'settings': SiteSettings.load()}

