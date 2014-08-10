#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import commands
import time
import os
import re
import json
from datetime import timedelta

import requests
import psutil

import config
import common

class Selfcheck(object):
    def __init__(self, status, message=""):
        self.status = status
        self.message = message

    def __bool__(self):
        return self.status

    @property
    def name(self):
        _name = self.__class__.__name__
        if _name.endswith("Check"):
            return _name[:-5]
        return _name

    @classmethod
    def check(cls):
        checks = [c.check() for c in cls.__subclasses__()]
        result = all(c.status for c in checks)
        msg = [c.message for c in checks if c.message]
        for m in msg:
            common.debug(m, error=True)
        return cls(result, msg)

class GQFSCheck(Selfcheck):
    @classmethod
    def check(cls):
        try:
            f = open("newfile.dat", "w")
            f.close()
            os.remove("newfile.dat")
            return cls(True)
        except IOError:
            return cls(False, "Filesystem in read-only mode")

        
class TMPFSCheck(Selfcheck):
    @classmethod
    def check(cls):
        df = commands.getoutput("df").splitlines()
        # Find the first line cointaining /tmp/lokun and ignore the rest
        # result: 'tmpfs                   131072    131072         0 100% /tmp/lok$
        try:
            tmplokun = filter(lambda x: "/tmp/lokun" in x, df)[0]
        except IndexError:
            return cls(False, "/tmp/lokun not mounted")
        # Split on spaces and ignore empty strings
        # result: ['tmpfs', '131072', '131072', '0', '100%', '/tmp/lokun']
        splitted = [a for a in tmplokun.split(" ") if a != ""]
        try:
            perc = int(splitted[4].strip()[:-1])
            status = perc < 80
            if not status:
                return cls(False, "tmpfs is filling up")
            else:
                return cls(True)
        except ValueError:
            return cls(False)

class OpenVPNStatusUpdated(Selfcheck):
    @classmethod
    def check(cls):
        errors = []
        for statusfile in config.openvpn_status:
            try:
                t_file = os.path.getmtime(statusfile)
            except OSError:
                errors.append(statusfile + " doesn't exist")
                continue
            t_now = time.time()
            delta = 600
            if t_file < t_now-delta:
                errors.append(statusfile + " hasn't been updated in 10 mins")
    
        if errors:
            return cls(False, ", ".join(errors))
        return cls(True)

class StuckClientScriptsCheck(Selfcheck):
    @classmethod
    def check(cls):
        regex = r'.client-[cd]'
        pslist = commands.getoutput("ps aux")
        if re.search(regex, filter(lambda s: s != '\n', pslist)):
            return cls(False, "client-{dis,}connect script is running")
        return cls(True)

class ProcessAliveCheck(Selfcheck):
    @classmethod
    def check(cls):
        openvpn_procs = filter(lambda p: p.name() == "openvpn" if hasattr(p.name, '__call__') else p.name == "openvpn", psutil.process_iter())
        if len(openvpn_procs) < 1:
            return cls(False, "openvpn process not found with ps")
        for proc in openvpn_procs:
            try:
                os.kill(proc.pid, 0)
            except OSError:
                return cls(False, "openvpn pid " + str(proc.pid) + " dead")
        return cls(True)

## api.lokun.is

def send_heartbeat(data):
    data = dict(data, **{'secret': config.key, 'name': config.servername})
    url = config.API+'/nodes/'+data['name']
    for _ in range(3):
        try:
            json = requests.post(url, data, timeout=4.20,
                                verify=config.verifyssl).json()
            return json
        except requests.ConnectionError as c:
            common.debug("Retrying API in 30 secs: " + str(c), error=True)
            time.sleep(30)
    else:
        common.debug("Giving up", error=True)
        sys.exit(1)

class Report(object):
    def json(self):
        return json.dumps(self)
    
    @property
    def selfcheck(self):
        return Selfcheck.check().status
    
    @property
    def total_throughput(self):
        with open("/sys/class/net/eth0/statistics/rx_bytes", "r") as f:
            return int(f.read().strip())

    @property
    def throughput(self):
        """Returns avg bytes per sec over 1.5 secs and total rx_bytes"""
        diff = []
        with open("/sys/class/net/eth0/statistics/rx_bytes", "r") as f:
            for _ in range(3):
                f.seek(0)
                start = int(f.read().strip())
                time.sleep(0.5)
                f.seek(0)
                end = int(f.read().strip())
                diff.append(end-start)
        return sum(diff)/3*2

    @property
    def usercount(self):
        count = []
        for statusfile in config.openvpn_status:
            status = open(statusfile, 'r').readlines()
            users = 0
            for line in status:
                if "," in line:
                    uname = line.split(",")[0]
                    if uname.isalnum() and uname not in ["END", "Updated"]:
                        users += 1
            count.append(users)
        return sum(count)

    @property
    def uptime(self):
        with open('/proc/uptime', 'r') as f:
            seconds = float(f.readline().split()[0])
            uptime = str(timedelta(seconds = seconds))
            u = uptime.split(", ")
            if len(u) == 1:
                days = "0"
                hours = u[0].split(":")[0]
            else:
                days = u[0].split(" ")[0]
                hours = u[1].split(":")[0]
            return days + "d " + hours + "h"

    @property
    def cpu(self):
        p = []
        for _ in range(3):
            p.append(psutil.cpu_percent())
            time.sleep(0.5)
        return sum(p)/3

    @property
    def load(self):
        uptime = commands.getoutput("uptime")
        _load = uptime.split("load average: ")[1].split(", ")[0]
        return _load

    def __iter__(self):
        attrs = []
        attrs.append(('cpu', self.cpu))
        attrs.append(('uptime', self.uptime))
        attrs.append(('total_throughput', self.total_throughput))
        attrs.append(('throughput', self.throughput))
        attrs.append(('selfcheck', self.selfcheck))
        attrs.append(('usercount', self.usercount))
        return iter(attrs)


def main():
    report = dict(Report())
    
    verbose = "-v" in sys.argv
    if verbose:
        common.debug("SENT: " + str(report))

    response = send_heartbeat(report)

    error = 'error' in response
    if verbose and not error:
        common.debug("RECV: " + str(response), error=False)

    if error:
        if not verbose:
            common.debug("SENT: " + str(report), error=True)
        common.debug("ERROR: " + str(response), error=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        common.debug(traceback.format_exc(), error=True)
