#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Machine translation using Microsoft Translator API
"""
import sys
import os
import argparse
import uuid
import json
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from logging import getLogger, StreamHandler, FileHandler, Formatter, DEBUG

import openpyxl

__author__ = 'Yuta OHURA <bultau@gmail.com>'
__status__ = 'development'
__version__ = '0.1'
__date__ = '17 May 2018'


class Translator:
    """
    Main class of translation
    """

    def __init__(self, api_key):
        self._api_key = api_key
        self._host = 'https://api.cognitive.microsofttranslator.com'
        self._path = '/translate?api-version=3.0'
        self._headers = {
            'Ocp-Apim-Subscription-Key': self._api_key,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

    def translate(self, base_string, to_lang):
        """
        Main function of translation
        """
        req = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504])
        req.mount('https://', HTTPAdapter(max_retries=retries))
        req.mount('http://', HTTPAdapter(max_retries=retries))

        requestBody = [{
            'Text': base_string,
        }]

        content = json.dumps(requestBody, ensure_ascii=False).encode('utf-8')

        res = req.request('POST', self._host + self._path + '&to=' +
                          to_lang, data=content, headers=self._headers, timeout=30)

        return res.text


if __name__ == '__main__':
    logger = getLogger(__name__)
    handler = StreamHandler(sys.stdout)
    handler.setFormatter(Formatter('%(asctime)s %(message)s'))
    handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)

    p = argparse.ArgumentParser()
    p.add_argument(
        '-t', '--to', help='language which you want to translate to')
    p.add_argument('-k', '--api-key', help='your API Key of Microsoft Azure')
    p.add_argument(
        '-s', '--input-string', help='character string which you want to translate', default=None)
    p.add_argument(
        '-f', '--input-file', help='input file which you want to translate', default=None)

    args = p.parse_args()

    trs = Translator(args.api_key)

    if args.input_string is not None:
        result = trs.translate(args.string, args.to)
        output = json.dumps(json.loads(result), indent=4, ensure_ascii=False)
    elif args.input_file is not None:
        wb = openpyxl.load_workbook(args.input_file)
        sheet = wb['data']
        for row in sheet.rows:
            if row[0].row == 1:
                continue
            string = row[1].value
            if string is not None:
                try:
                    ret_json = trs.translate(string, args.to)
                    ret_dict = json.loads(ret_json)
                    logger.debug(json.dumps(json.loads(ret_json),
                                            indent=4, ensure_ascii=False))
                    ret_text = ret_dict[0]['translations'][0]['text']
                    row[2].value = ret_text
                except KeyError as e:
                    logger.error('error has occured on line %s' %
                                 str(row[0].row))
                    logger.error(e)
        tmp_txt = os.path.splitext(args.input_file)
        wb.save('.'.join([tmp_txt[0] + '_translated', tmp_txt[1]]))
    else:
        logger.error('you must specify the string or file to translate')
        sys.exit()
