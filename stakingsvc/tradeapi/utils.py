#!/usr/bin/python
# -*- coding: utf-8 -*-
import hashlib
import logging

logger = logger = logging.getLogger("tradeapi.utils")

def sign_api_content(json, secret_key):
    sorted_keys = sorted(json.keys())
    count = 0
    str_to_be_signed = ""
    for key in sorted_keys:
        if count > 0:
            str_to_be_signed = str_to_be_signed + '&'
        str_to_be_signed = '{0}{1}={2}'.format(str_to_be_signed, key, json[key])
        count = count + 1
    if count > 0:
        str_to_be_signed = str_to_be_signed + '&'
    str_to_be_signed = '{0}key={1}'.format(str_to_be_signed, secret_key.upper())
    m = hashlib.md5()
    logger.debug("str to be signed {0}".format(str_to_be_signed))
    m.update(str_to_be_signed.encode('utf-8'))
    return m.hexdigest().upper()

def create_tradeEx_request_meta_info(settings):
    return None