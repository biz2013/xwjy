import sys
from walletgui.models import SiteSettings

def settings(request):
    return {'settings': SiteSettings.load()}

