from os import path 
import sys

if "--dev" in sys.argv:
    API = "http://localhost:8080"
    verifyssl = False
    openvpn_status = ["openvpn-status.log", "openvpn-status-tcp.log"]
    keyfile = "keyfile.dev.txt"
    servernamefile = "servername.dev.txt"
    logfile = "debug.log"
    if "--realapi" in sys.argv:
        API = "https://api.lokun.is"
        verifyssl = True
        keyfile= "keyfile.api.txt"
        servernamefile = "servername.api.txt"
else:
    API = "https://api.lokun.is"
    verifyssl = False
    openvpn_status = ["/tmp/lokun/openvpn-status.log", "/tmp/lokun/openvpn-status-tcp.log"]
    keyfile = "/etc/openvpn/keyfile.txt"
    servernamefile = "/etc/openvpn/servername.txt"
    logfile = "/tmp/lokun/debug.log"

iface = 'eth0'
key = ''.join(open(keyfile, "r").readlines()).strip()
servername = ''.join(open(servernamefile, "r").readlines()).strip()
log_to_file = servername in ["vpn2", "vpn00", "testvpn"]

