# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
"""
import requests
import time

key = ""
def check_api(bigram):
    query_string = { 'api-key': key, 'fq': 'body:"%s %s"' % (bigram[0], bigram[1])}
    req = requests.get('https://api.nytimes.com/svc/search/v2/articlesearch.json', params=query_string)
    if req.status_code in set([429, 529, 504]):
        time.sleep(25)
        return check_api(bigram)
    if req.status_code == 500:
        return False 
    try:
        result = req.json()
    except:
        import pdb; pdb.set_trace()
    num_results = len(result['response']['docs'])
    return num_results < 2
