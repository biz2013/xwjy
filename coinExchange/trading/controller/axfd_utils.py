import json, subprocess, logging

logger = logging.getLogger("site.axf_util")

class AXFundUtility(object):
    def __init__(self, settings):
        self.axfd_path = settings.axfd_path
        self.axfd_datadir = settings.axfd_datadir
        self.axfd_account = settings.axfd_account_name
        self.axfd_passphrase = settings.axfd_passphrase
        self.axfd_lookback_count = settings.axfd_list_trans_count

    def listtransactions(self):
        return self.listtransactions_impl(self.axfd_lookback_count)

    def listtransactions_impl(self, lookback_count):
        logger.info('{0} {1} {2} {3} {4}'.format(
            self.axfd_path, '-datadir=%s'%(self.axfd_datadir),
            'listtransactions', self.axfd_account, lookback_count
        ))
        result_str = subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir),
            'listtransactions', self.axfd_account, str(lookback_count)])
        #logger.info("listtransaction return: {0}".format(result_str))
        return json.loads(result_str.decode('utf-8'))

    def send_fund(self, dst, amount, comment):
        return self.send_fund_impl(self.axfd_account, dst, amount, comment, self.axfd_lookback_count)

    def send_fund_impl(self, src_account, dst, amount, comment, lookback_count):
        logger.info('{0} {1} {2} {3} {4} \'{5}\''.format(
            self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'sendtoaddress',
            dst, str(amount), comment
        ))
        result_str = subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'sendtoaddress',
            dst, str(amount), '{0}'.format(comment)])
        result_str = result_str.decode('utf-8')
        logger.info("send to address return transaction id {0}".format(
            result_str))
        transactions = self.listtransactions()
        for trans in transactions:
            # if accidentally send money to address in the same accounts
            # you can see two trans have the same txid. so need to check
            # category field
            if trans['txid'] == result_str.rstrip() and trans['category'] == 'send':
                return trans
        raise ValueError("Not redeem transaction for txid {0}".format(result_str))

    def unlock_wallet(self, timeout_in_sec):
        self.unlock_wallet_impl(self.axfd_passphrase, timeout_in_sec)

    def unlock_wallet_impl(self, passphrase, timeout_in_sec):
        logger.info("unlock wallet ...")
        subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'walletpassphrase',
            passphrase, str(timeout_in_sec)])

    def create_wallet_address(self):
        logger.info('Create wallet address: {0} {1} {2}'.format(
            self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'getnewaddress',
        ))

        result_str = subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'getnewaddress',
            self.axfd_account])

        result_str = result_str.rstrip()
        logger.info("Wallet address {0} created".format(result_str))
        return result_str.decode('utf-8')
