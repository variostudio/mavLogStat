# This is a simple Mavlink Log analyzer tool
# pymavlink package is required
from pymavlink import mavutil
import fnmatch
import argparse


def progress_bar(pct):
    if pct % 2 == 0:
        print('.', end='')


def show_all_params(params):
    wildcard = '*'
    k = sorted(params.keys())
    for p in k:
        if fnmatch.fnmatch(str(p).upper(), wildcard.upper()):
            print("%-16.16s %f" % (str(p), params[p]))


def show_user_params(params):
    param_servo_auto_trim = params['SERVO_AUTO_TRIM']
    param_stall_prevention = params['STALL_PREVENTION']

    print('\nVehicle parameters:')
    print(f'Servo auto trim: {param_servo_auto_trim} - {"OK" if param_servo_auto_trim == 1.0 else "Warning!"}')
    print(f'Stall prevention: {param_stall_prevention} - {"OK" if param_stall_prevention == 0.0 else "Warning!"}')


def show_flight_stat(log):
    max_alt = 0
    last_bat_msg = None
    last_gps_msg = None
    first_gps_msg = None

    while True:
        msg = log.recv_match(type=['BAT', 'BARO', 'GPS'])
        if msg is None:
            break

        mtype = msg.get_type()

        if mtype == 'BAT':
            last_bat_msg = msg

        if mtype == 'GPS':
            if first_gps_msg is None:
                first_gps_msg = msg
            last_gps_msg = msg

        if mtype == 'BARO':
            alt = msg.Alt
            if alt > max_alt:
                max_alt = alt

    print('\nFlight statistics:')
    print('Total time: %.2f sec' % (last_bat_msg.TimeUS/1000000))
    print('Maximum altitude: %.2f m' % max_alt)
    print('Used: %.2f mAh' % last_bat_msg.CurrTot)
    print(f'Home location: {first_gps_msg.Lat}, {first_gps_msg.Lng}')
    print(f'Last known location: {last_gps_msg.Lat}, {last_gps_msg.Lng}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='mavLogStat')
    parser.add_argument('logfile', help='log file to analyze')
    args = parser.parse_args()

    if args.logfile is None:
        parser.print_help()
    else:
        print(f'Loading {args.logfile} ', end='')
        mlog = mavutil.mavlink_connection(args.logfile, notimestamps=False,
                                          zero_time_base=False,
                                          progress_callback=progress_bar)

        mlog.flightmode_list()
        print(f'\nLoaded {mlog._count} messages total')

        show_user_params(mlog.params)

        show_flight_stat(mlog)
