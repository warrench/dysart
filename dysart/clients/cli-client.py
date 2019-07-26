# -* coding: utf-8 -*-

import json
import urllib.request as request
import sys

if __name__ == '__main__':
    d = {'user': 'root',
         'secret': 'root',
         'doc_class': sys.argv[1],
         'name': sys.argv[2],
         'method': sys.argv[3]}
    d_flat = [item for kv in d.items() for item in kv]
    url_prefix = 'http://localhost:8000/?'
    with request.urlopen((url_prefix + '{}={}&'*len(d)).format(*d_flat)) as u:
        response = json.loads(u.read().decode('utf-8'))

    print(response['res'])

# auth info should probably be handled by urllib.request
"""
authinfo = request.HTTPBasicAuthHandler()
authinfo.add_password(realm='PDQ Application',
                      uri='http://localhost:8000/',
                      user='root',
                      passwd='root')
"""
