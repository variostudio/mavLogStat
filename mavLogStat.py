# This is a simple Mavlink Log analyzer tool
# mavlink package is required
from pymavlink import mavutil
import fnmatch
import copy
from time import sleep
from MAVProxy.modules.lib import multiproc

def progress_bar(pct):
    if pct % 2 == 0:
        print('#', end='')

def showParams(params):
    wildcard = '*'
    k = sorted(params.keys())
    for p in k:
        if fnmatch.fnmatch(str(p).upper(), wildcard.upper()):
            print("%-16.16s %f" % (str(p), params[p]))


if __name__ == '__main__':
    multiproc.freeze_support()
    file = 'log_11_2021-10-27-14-17-30.bin'

    print(f'Loading {file} ...')
    mlog = mavutil.mavlink_connection(file, notimestamps=False,
                                      zero_time_base=False,
                                      progress_callback=progress_bar)

    sleep(5)
    msgs = copy.copy(mlog.messages)
    params = copy.copy(mlog.params)
    showParams(params)
