import json, subprocess, logging

logger = logging.getLogger("site.axf_util")

class AXFundUtility(object):
    def __init__(self, axfd_path_val, axfd_datadir_val, axfd_account_val):
        self.axfd_path = axfd_path_val
        self.axfd_datadir = axfd_datadir_val
        self.axfd_account = axfd_account_val


    def listtransactions(self, lookback_count):
        logger.info('{0} {1} {2} {3} {4}'.format(
            self.axfd_path, '-datadir=%s'%(self.axfd_datadir),
            'listtransactions', self.axfd_account, lookback_count
        ))
        result_str = subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir),
            'listtransactions', self.axfd_account, str(lookback_count)])
        logger.info("listtransaction return: {0}".format(result_str))
        return json.loads(result_str)

    def send_fund(self, src_account, dst, amount, comment, lookback_count):
        logger.info('{0} {1} {2} {3} {4} \'{5}\''.format(
            self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'sendtoaddress',
            dst, str(amount), comment
        ))
        result_str = subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'sendtoaddress',
            dst, str(amount), '\"{0}\"'.format(comment)])
        logger.info("send to address return transaction id {0}".format(
            result_str))
        transactions = self.listtransactions(src_account, lookback_count)
        for trans in transactions:
            if trans['txid'] == result_str:
                return trans
        return result_str

    def unlock_wallet(self, passphrase, timeout_in_sec):
        logger.info("unlock wallet ...")
        subprocess.check_output(
           [self.axfd_path, '-datadir=%s'%(self.axfd_datadir), 'walletpassphrase',
            passphrase, str(timeout_in_sec)])
