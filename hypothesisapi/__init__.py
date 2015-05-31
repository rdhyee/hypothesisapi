# -*- coding: utf-8 -*-
from __future__ import absolute_import

__author__ = 'Raymond Yee'
__email__ = 'raymond.yee@gmail.com'
__version__ = '0.1.0'

import requests
import json

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode



APP_URL = "https://hypothes.is/app"
API_URL = "https://hypothes.is/api"

# We can probably learn a lot from https://h.readthedocs.org/en/latest/api.html

class API(object):
    """
    currently a wrapper for the nascent web API for 
    """
    
    def __init__(self, username, password, api_url=API_URL, app_url=APP_URL):
        """
        I think at this point, a hypothes.is username/password required for API to work
        """
        self.api_url = api_url
        self.app_url = app_url
        self.username = username
        self.password = password
        self.csrf_token = None
        self.token = None

    def create (self, payload):
        
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
        data = json.dumps(payload_out)
        headers = {"content-type": "application/json;charset=UTF-8",
                   "X-Annotator-Auth-Token": self.token, 
                   "x-csrf-token": self.csrf_token
                   }
        r = requests.post(self.api_url + "/annotations", headers = headers, data = data)
        if r.status_code == 200:
            return r.json()
        else:
            print("Failed\n")
            print(r.text)
            return None
        
    def login(self):
        
        # pick up some cookies to start the session
        
        r = requests.get(self.app_url)
        cookies = r.cookies

        # make call to https://hypothes.is/app?__formid__=login
        
        payload = {"username":self.username,"password":self.password}
        self.csrf_token = cookies['XSRF-TOKEN']
        data = json.dumps(payload)
        headers = {'content-type':'application/json;charset=UTF-8', 'x-csrf-token': self.csrf_token}
        
        r = requests.post(url=self.app_url  + "?__formid__=login", data=data, cookies=cookies, headers=headers)
        
        # get token

        url = self.api_url + "/token?" + urlencode({'assertion':self.csrf_token})
        r = (requests.get(url=url,
                         cookies=cookies, headers=headers))
        
 
        self.token =  r.content
    
    def search_id (self, _id):
        
        url = self.api_url + "/search?_id=" + _id
        
        headers = {"X-Annotator-Auth-Token": self.token, "x-csrf-token":self.csrf_token}
        r = requests.get(url, headers = headers)
        if r.status_code == 200:
            return r.json()
        else:
            return None
        
    def search (self, user, offset=0, page_size=10):
        
        headers = {"X-Annotator-Auth-Token": self.token, "x-csrf-token":self.csrf_token}
        page_size = page_size
        user_acct = "acct:{user}@hypothes.is".format(user=user)
        
        limit=page_size
        
        more_results = True
    
        while more_results:
            search_dict = {'user':user_acct, 'limit':limit, 'offset':offset}
            url = self.api_url + "/search?{query}".format(query=urlencode(search_dict))
            
            r = requests.get(url, headers=headers)
            rows = r.json().get("rows")
            
            if len(rows):
                for row in rows:
                    yield row
                offset += page_size
            else:
                more_results = False

    
    
        
        
