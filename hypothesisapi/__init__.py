# -*- coding: utf-8 -*-
from __future__ import absolute_import

__author__ = 'Raymond Yee'
__email__ = 'raymond.yee@gmail.com'
__version__ = '0.2.0'

import requests
import json

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode



APP_URL = "https://hypothes.is/app"
API_URL = "https://hypothes.is/api"

# We can probably learn a lot from https://h.readthedocs.org/en/latest/api.html

def remove_none(d):
    return dict([(k,v) for (k, v) in d.items() if v is not None])

class API(object):
    """
    currently a wrapper for the nascent web API for 
    """
    
    def __init__(self, username, api_key, api_url=API_URL, app_url=APP_URL):
        """
        I think at this point, a hypothes.is username/api_token required for API to work
        """
        self.api_url = api_url
        self.app_url = app_url
        self.username = username
        self.api_key = api_key

    def create(self, payload):
        
        user = self.username
        user_acct = "acct:{user}@hypothes.is".format(user=user)
        
        payload_out = payload.copy()
        payload_out["user"] = user_acct
        if not "uri" in payload:
            return None
        if not "permissions" in payload:
            perms = {
                "read"  : ["group:__world__"],
                "update": ["acct:{user}@hypothes.is".format(user=user)],
                "delete": ["acct:{user}@hypothes.is".format(user=user)],
                "admin" : ["acct:{user}@hypothes.is".format(user=user)]
                }
            payload_out["permissions"] = perms
        if not "document" in payload:
            doc = {}
            payload_out["document"] = doc
        if not "text" in payload:
            payload_out["text"] = None            
        if not "tags" in payload:
            payload_out["tags"] = None
        if not "target" in payload: 
            target = [
                {
                "selector": 
                    [
                        {
                        "start": None,
                        "end": None,
                        "type": "TextPositionSelector"
                        }, 
                        {
                        "type": "TextQuoteSelector", 
                        "prefix": None,
                        "exact": None,
                        "suffix": None
                        },
                    ]
                }
            ]
            payload_out["target"] = target
        headers = {"content-type": "application/json;charset=UTF-8",
                   "Accept": "application/json",
                   "Authorization": "Bearer "+self.api_key
                   }
        print(payload_out)
        r = requests.post(self.api_url + "/annotations", headers=headers, json=payload_out)
        if r.status_code == 200:
            return r.json()
        else:
            print("Failed\n")
            print(r.text)
            return None
        

    def get_annotation(self, _id):
        """
        https://hypothes.is/api/annotations/:id
        """
        url = self.api_url + "/annotations/" + _id
        headers = {"Accept": "application/json"}
        r = requests.get(url, headers = headers)
        
        if r.status_code == 200:
            return r.json()
        else:
            return None
             
    '''
    As per https://h.readthedocs.io/en/latest/api.html?#search I don't think this is a thing anymore.
    '''
    def search_id(self, _id):
        
        url = self.api_url + "/search?_id=" + _id
        
        headers = {"Accept": "application/json"}
        r = requests.get(url, headers = headers)
        if r.status_code == 200:
            return r.json()
        else:
            return None

    def search(self, user=None, sort=None, order="asc", offset=0, limit=200, uri=None, **kw):
        
        headers = {"content-type": "application/json;charset=UTF-8",
                   "Accept": "application/json",
                   "Authorization": "Bearer "+self.api_key
                   }

        user_acct = "acct:{user}@hypothes.is".format(user=user) if user is not None else None

        search_dict = ({'user':user_acct,
         'sort':sort,
         'order':order,
         'offset':offset,
         'uri':uri,
         'limit':limit})
    
        search_dict.update(kw)
        search_dict = remove_none(search_dict)
        
        more_results = True
    
        while more_results:
    
            url = self.api_url + "/search?{query}".format(query=urlencode(search_dict))
            
            r = requests.get(url, headers=headers)
            rows = r.json().get("rows", [])
            
            if len(rows):
                for row in rows:
                    yield row
                search_dict['offset'] += limit
            else:
                more_results = False
