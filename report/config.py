from os import path 
import sys

API = "http://localhost:8080"
verifyssl = True
openvpn_status = "openvpn-status.log"
keyfile = "keyfile.txt"
servernamefile = "servername.txt"
logfile = "debug.log"
log_to_file = False

key = ''.join(open(keyfile, "r").readlines()).strip()
servername = ''.join(open(servernamefile, "r").readlines()).strip()


