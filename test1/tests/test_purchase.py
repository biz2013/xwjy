from django.test import TestCase, TransactionTestCase
from users.models import UserLogin

class PurchaseTestCase(TransactionTestCase):
    fixtures = ['fixture_for_tests.json']

    def test_create_sell_order(self):
       try:
           user = UserLogin.objects.get(username='taozhang')
           self.assertEqual('taozhang', user.username)
       except user.DoesNotExist:
           self.fail('Should have one record with user taozhang')
