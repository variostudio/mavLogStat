# This is a simple Mavlink Log analyzer tool
# pymavlink, geopy and folium packages are required
from pymavlink import mavutil
from geopy import distance
from operator import itemgetter
import argparse
import folium


def progress_bar(pct):
    if pct % 2 == 0:
        print('.', end='')


def show_mission(wps, map_output):
    if len(wps) > 0:
        first_location = None
        current_location = None
        auto_land_set = False
        first_marker_skipped = False
        max_range = 0
        total_length = 0

        normalized_wps = sorted(set(wps), key=itemgetter(2))

        wp_locations = []
        for wp in normalized_wps:
            if first_location is None:
                first_location = (wp[0], wp[1])
                current_location = (wp[0], wp[1])

            if wp[0] != 0 and wp[1] != 0:
                segment_len = distance.distance(current_location, (wp[0], wp[1])).m
                current_location = (wp[0], wp[1])
                total_length += segment_len
                home_dist = distance.distance(first_location, current_location).m
                if home_dist > max_range:
                    max_range = home_dist

                if wp[4] == 21:
                    auto_land_set = True

                wp_locations.append(current_location)
                if first_marker_skipped:
                    folium.Marker(
                        location=[wp[0], wp[1]],
                        popup="Waypoint #{0}".format(wp[2]),
                        tooltip="Waypoint #{2}: [{0}, {1}], Alt={3} m, Type={4}".format(wp[0], wp[1], wp[2], wp[3], wp[4]),
                        icon=folium.Icon(icon="plus", color="blue"),
                    ).add_to(map_output)
                else:
                    first_marker_skipped = True

        folium.PolyLine(
            wp_locations, color='grey'
        ).add_to(map_output)

        print('\nMission data found in log file:')
        print('Total distance: %.2f kn' % (total_length / 1000))
        print('Maximum distance from home: %.2f km' % (max_range / 1000))
        print(f'Auto Landing is configured: {auto_land_set}')
    else:
        print('\nNo mission data is found')


def show_plot_data(log, filename):
    max_altitude = 0
    max_distance = 0
    total_distance = 0
    last_bat_msg = None
    last_gps_msg = None
    first_gps_msg = None
    points = []
    wps = []

    while True:
        msg = log.recv_match(type=['BAT', 'BARO', 'GPS', 'CMD'])
        if msg is None:
            break

        mtype = msg.get_type()

        if mtype == 'CMD':
            wps.append((msg.Lat, msg.Lng, msg.CNum, msg.Alt, msg.CId))

        if mtype == 'BAT':
            last_bat_msg = msg

        if mtype == 'GPS':
            if first_gps_msg is None:
                first_gps_msg = msg
                last_gps_msg = msg

            dist = distance.distance((last_gps_msg.Lat, last_gps_msg.Lng), (msg.Lat, msg.Lng))
            home = distance.distance((first_gps_msg.Lat, first_gps_msg.Lng), (msg.Lat, msg.Lng))
            total_distance += dist.m
            last_gps_msg = msg
            points.append((msg.Lat, msg.Lng))
            if home.m > max_distance:
                max_distance = home.m

        if mtype == 'BARO':
            alt = msg.Alt
            if alt > max_altitude:
                max_altitude = alt

    print('\nFlight statistics:')
    print('Total time: %.2f sec' % (last_bat_msg.TimeUS/1000000))
    print('Maximum altitude: %.2f m' % max_altitude)
    print('Used: %.2f mAh' % last_bat_msg.CurrTot)
    print(f'Home location: {first_gps_msg.Lat}, {first_gps_msg.Lng}')
    print(f'Last known location: {last_gps_msg.Lat}, {last_gps_msg.Lng}')
    print('Total distance: %.2f km' % (total_distance/1000))
    print('Maximum range: %.2f km' % (max_distance/1000))
    print('Average efficiency: %.2f mAh/km' % (last_bat_msg.CurrTot * 1000 / total_distance))

    base_map = folium.Map([first_gps_msg.Lat, first_gps_msg.Lng], zoom_start=10)
    folium.PolyLine(
        points, color='darkorange'
    ).add_to(base_map)

    folium.Marker(
        location=[first_gps_msg.Lat, first_gps_msg.Lng],
        popup="Take off",
        tooltip="Take off: [{0}, {1}]".format(first_gps_msg.Lat, first_gps_msg.Lng),
        icon=folium.Icon(icon="chevron-up", color="green"),
    ).add_to(base_map)

    folium.Marker(
        location=[last_gps_msg.Lat, last_gps_msg.Lng],
        popup="Landing",
        tooltip="Landing: [{0}, {1}]".format(last_gps_msg.Lat, last_gps_msg.Lng),
        icon=folium.Icon(icon="chevron-down", color="darkgreen"),
    ).add_to(base_map)

    show_mission(wps, base_map)

    print('\n{0}.html saved. Open in browser to show track'.format(filename))
    base_map.save('{0}.html'.format(filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='mavLogPlot')
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
        print(f'\nLoading done. Please wait while processing.')
        show_plot_data(mlog, args.logfile)
