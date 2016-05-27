import os
import sys

import argparse
import requests

from hypothesisapi import *

parser = argparse.ArgumentParser()
parser.add_argument('-u', dest='user', action='store',
                    help='hypothes.is user')

parser.add_argument('-k', dest='api_key', action='store',
                    help='hypothes.is api_key')

parser.add_argument('-l', dest='test_uri', action='store',
                    help='url to annotate')

args = parser.parse_args()

# Set up Hypothes.is config
H = API(args.user, args.password)
H.login()

# Now test create on test_uri
payload = {
    "uri"  : args.test_uri,
    "text" : "testing create in hypothes.is API"
    }
    
r = H.create(payload)

if (r is not None):
    print(r)


