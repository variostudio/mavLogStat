# This is a simple Mavlink Log analyzer tool
# mavlink package is required
from pymavlink import mavutil
import fnmatch
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
    file = '/home/troll/Projects/Z84/log_11_2021-10-27-14-17-30.bin'

    print(f'Loading {file} ...')
    mlog = mavutil.mavlink_connection(file, notimestamps=False,
                                      zero_time_base=False,
                                      progress_callback=progress_bar)

    mlog.flightmode_list()

    param_servo_auto_trim = mlog.params['SERVO_AUTO_TRIM']
    param_stall_prevention = mlog.params['STALL_PREVENTION']

    print('\n All parameters:')
    showParams(mlog.params)

    print('\n Vehicle parameters:')
    print(f'Servo auto trim: {param_servo_auto_trim}')
    print(f'Stall prevention: {param_stall_prevention}')

