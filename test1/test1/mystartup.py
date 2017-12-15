from django.apps import AppConfig
from controller.global_utils import *

class XWJYAppConfig(AppConfig):
    name = 'test1'
    def ready(self):
        LOGGER = setup_logger('xwjy.log', 'xwjy')        
