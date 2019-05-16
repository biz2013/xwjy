#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import logging, json

logger = logging.getLogger('tradeex.apiclient')

class APIClient(object):
    def __init__(self, url, retry_policy=None):
        self.url = url
        self.retry_policy = retry_policy

    def send_json_request(self, pay_load, trackingId = '', response_format='json'):
        headers = {"Content-Type": "application/json",
               "charset": "utf-8"}
        request_str = json.dumps(pay_load, ensure_ascii=False)
        logger.info("apiclient.send_json_request(): {0} send request to {1}, with json:{2}".format(
            '[trackId: {0}]'.format(trackingId) if trackingId else '',
            self.url, request_str
        ))
        r = requests.post(self.url, json=pay_load, headers= headers, allow_redirects=True, verify=False)
        logger.info("response is {0}".format(r.text))
        return r.json() if response_format=='json' else r.text