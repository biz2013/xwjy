from users.sitesettings import SiteSettings

def settings(request):
    return {'settings': SiteSettings.load()}
