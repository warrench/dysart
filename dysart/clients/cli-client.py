# -* coding: utf-8 -*-

import urllib.request as request

if __name__ == '__main__':
    d = {'user': 'root',
         'secret': 'root',
         'doc_class': 'QubitSpectrum',
         'name': 'qb_spec',
         'method': 'linewidth'}
    d_flat = [item for kv in d.items() for item in kv]
    url_prefix = 'http://localhost:8000/?'
    with request.urlopen((url_prefix + '{}={}&'*len(d)).format(*d_flat)) as u:
        print(u.read())


# auth info should probably be handled by urllib.request
"""
authinfo = request.HTTPBasicAuthHandler()
authinfo.add_password(realm='PDQ Application',
                      uri='http://localhost:8000/',
                      user='root',
                      passwd='root')
"""
