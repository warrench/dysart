# -* coding: utf-8 -*-

import json
import urllib.request as request
import sys
from typing import Union

import numpy as np

# auth info should probably be handled by urllib.request


class DyPyClient():
    """
    A basic remote client for DyPy
    """

    def __init__(self, hostname, port):
        self._response = ''
        self.server_address = '{}:{}'.format(hostname, port)
        pass

    @property
    def response(self) -> Union[int, float, str, np.array]:
        """parse and return the reponse string.
        This method is potentially _extremely dangerous_, and must be approached
        with great care. DO NOT replace this function body with
                        `return eval(self._response)`
        which could run arbitrary code served over an untrusted network on the
        client. For this demo version, the
        """
        try:
            return float(self._response)
        except Exception:
            raise ValueError('non-float reponse from dysart server')

    def issue_query(self, doc_class, name, method):
        """

        """
        d = {'user': 'root',
             'secret': 'root',
             'doc_class': doc_class,
             'name': name,
             'method': method}
        d_flat = [item for kv in d.items() for item in kv]

        url_prefix = 'http://{}/?'.format(self.server_address)
        with request.urlopen((url_prefix + '{}={}&' * len(d)).format(*d_flat)) as u:
            self.response = json.loads(u.read().decode('utf-8'))


if __name__ == '__main__':
    client = DyPyClient(hostname='localhost', port='8000')
    while True:
        reqstr = input(' :: ')
        doc_class, name, method, *_ = reqstr.split()
        client.issue_query(*reqstr.split())
        print(client.response)
