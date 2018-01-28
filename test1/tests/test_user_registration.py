from django.test import TestCase
from controller.axfd_utils import AXFundUtility
from test1.app import *
from users.models import *


class UserRegistrationTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        print("setUpTestData: Run once to set up non-modified data for all class methods.")
        pass

    def setUp(self):
        print("setUp: Run once for every test method to setup clean data.")
        pass

        #self.assertFalse(False)
        #self.assertEqual(1 + 1, 2)

    def test_add_user_wallet_success(self):
        addr = create_user_axfund_wallet()

        user_wallet = UserWallet.objects.select_for_update().filter(Q(user__isnull=True))[0]
        self.assertEqual(addr, user_wallet.wallet_addr)