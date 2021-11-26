# This is a simple Mavlink Log analyzer tool
# pymavlink package is required
from pymavlink import mavutil
import fnmatch
import argparse

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
    parser = argparse.ArgumentParser(prog='mavLogStat')
    parser.add_argument('logfile', help='log file to analyze')
    args = parser.parse_args()

    if args.logfile is None:
        parser.print_help()
    else:
        print(f'Loading {args.logfile} ...')
        mlog = mavutil.mavlink_connection(args.logfile, notimestamps=False,
                                          zero_time_base=False,
                                          progress_callback=progress_bar)

        mlog.flightmode_list()

        param_servo_auto_trim = mlog.params['SERVO_AUTO_TRIM']
        param_stall_prevention = mlog.params['STALL_PREVENTION']

        # print('\n All parameters:')
        # showParams(mlog.params)

        print('\nVehicle parameters:')
        print(f'Servo auto trim: {param_servo_auto_trim} - {"OK" if param_servo_auto_trim == 1.0 else "Warning!"}')
        print(f'Stall prevention: {param_stall_prevention} - {"OK" if param_stall_prevention == 0.0 else "Warning!"}')
