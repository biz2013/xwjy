import json, subprocess, logging

logger = logging.getLogger(__name__)

def axfd_listtransactions(axfaccount, lookback_count):
    sitesettings = context_processor.settings(request)['settings']
    axfd_path = sitesettings.axfd_path
    axfd_datadir = sitesettings.axfd_datadir
    result_str = subprocess.check_output(
       [axfd_path, '-datadir=%s'%(axfd_data), 'listtransactions', account, str(lookback_count)])
    return json.loads(result_str)

def axfd_send_fund(dst, amount, comment):
    sitesettings = context_processor.settings(request)['settings']
    axfd_path = sitesettings.axfd_path
    axfd_datadir = sitesettings.axfd_datadir
    result_str = subprocess.check_output(
       [axfd_path, '-datadir=%s'%(axfd_data), 'sendtoaddress', dst, str(amount), comment])
    return json.loads(result_str)
