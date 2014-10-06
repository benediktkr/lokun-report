#coding: utf-8
#
# Common methods ----
from datetime import datetime
from config import log_to_file, logfile

def debug(msg, error=False):
    s = str(datetime.now().replace(microsecond=0)) + "\t" + str(msg)
    print s
    if log_to_file or error:
        f = open(logfile, "a")
        f.write(s + "\n")
        f.close()

