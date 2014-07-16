#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Nessecary setting for OpenVPN:
# "script-security >= 2"

import os
import sys
import requests
import config
import common

def auth(cn):
    """ASK the API for authentication for a given user"""
    json = requests.post(config.API+'/vpn/'+cn+'/sub', 
                         {'secret': config.key},
                         verify=config.verifyssl,
                         timeout=4.20).json()
    if "error" in json:
        common.debug("error: " + json["error"])
        return False
    if json['sub_status'] == "True":
        return True
    return False

def main():
    cn = os.environ['common_name']
    if auth(cn):
        common.debug(cn + " authed")
        sys.exit(0)             # Accept
    else:
        common.debug(cn + " not authed")
        sys.exit(1)             # Reject
        
if __name__ == "__main__":
    main()


