#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# "script-security >= 2"
import os 
import sys
import requests
import config
import common

def report(cn, traffic):
    """Report traffic for a CN to record"""
    requests.post(config.API+'/vpn/'+cn+'/report',
                  {'secret': config.key, 'dl': traffic},
                  verify=config.verifyssl,
                  timeout=4.20)    

def main():
    cn = os.environ['common_name']
    in_bytes = int(os.environ['bytes_sent']) # sent by server
    out_bytes = int(os.environ['bytes_received']) 
    traffic = in_bytes + out_bytes

    report(cn, traffic)
    
    mib = str(traffic/1024/1024)
    common.debug(cn + " disconnect. " + mib + " mb")
    common.debug(" in: " + str(in_bytes/1024/1024))
    common.debug(" out: " + str(out_bytes/1024/1024))
    sys.exit(0)
    
if __name__ == "__main__":
    main()
