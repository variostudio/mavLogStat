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


def show_messages(messages, map_output):
    for message in messages:
        folium.Marker(
            location=[message[1], message[2]],
            popup="Message: {0}".format(message[0]),
            tooltip="Message",
            icon=folium.Icon(icon="asterisk", color="orange")
        ).add_to(map_output)


def show_failsafe(messages, map_output):
    for message in messages:
        if message[0].startswith('Failsafe'):
            if "Long event on" in message[0]:
                folium.Marker(
                    location=[message[1], message[2]],
                    popup=message[0],
                    tooltip="Failsafe - long event",
                    icon=folium.Icon(icon="exclamation-sign", color="red")
                ).add_to(map_output)
            if "Short event on" in message[0]:
                folium.Marker(
                    location=[message[1], message[2]],
                    popup=message[0],
                    tooltip="Failsafe - short event",
                    icon=folium.Icon(icon="exclamation-sign", color="pink")
                ).add_to(map_output)


def show_track(points, first_gps_msg, last_gps_msg, longest_distance_gps, max_distance, info_html, map_output):
    folium.PolyLine(
        points, color='darkorange'
    ).add_to(map_output)

    folium.Marker(
        location=[first_gps_msg.Lat, first_gps_msg.Lng],
        popup="Take off: [{0}, {1}]".format(first_gps_msg.Lat, first_gps_msg.Lng),
        tooltip="Take off",
        icon=folium.Icon(icon="circle-arrow-up", color="green")
    ).add_to(map_output)

    iframe = folium.IFrame(html=info_html, width=400, height=200)
    info_popup = folium.Popup(iframe)

    folium.Marker(
        location=[last_gps_msg.Lat, last_gps_msg.Lng],
        # popup="Landing: [{0}, {1}]".format(last_gps_msg.Lat, last_gps_msg.Lng),
        popup=info_popup,
        tooltip="Landing",
        icon=folium.Icon(icon="circle-arrow-down", color="darkgreen")
    ).add_to(map_output)

    folium.Marker(
        location=[longest_distance_gps.Lat, longest_distance_gps.Lng],
        popup="The most remote point: [{0}, {1}], {2:.2f} km".format(
            longest_distance_gps.Lat, longest_distance_gps.Lng, max_distance / 1000),
        tooltip="The most remote point",
        icon=folium.Icon(icon="asterisk", color="blue")
    ).add_to(map_output)


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
                        tooltip="Waypoint #{0}".format(wp[2]),
                        popup="Waypoint #{2}: [{0}, {1}], Alt={3} m, Type={4}"
                                .format(wp[0], wp[1], wp[2], wp[3], wp[4]),
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


def draw_map(filename, first_gps_msg, last_gps_msg, longest_distance_gps, points, wps, max_distance, messages,
             info_html):
    track_layer = folium.FeatureGroup(name='Track')
    failsafe_layer = folium.FeatureGroup(name='Failsafe', show=False)
    mission_layer = folium.FeatureGroup(name='Mission', show=False)
    message_layer = folium.FeatureGroup(name='Messages', show=False)

    base_map = folium.Map([first_gps_msg.Lat, first_gps_msg.Lng], zoom_start=10)
    base_map.add_child(track_layer)
    base_map.add_child(failsafe_layer)
    base_map.add_child(mission_layer)
    base_map.add_child(message_layer)
    base_map.add_child(folium.map.LayerControl(collapsed=False))

    show_track(points, first_gps_msg, last_gps_msg, longest_distance_gps, max_distance, info_html, track_layer)
    show_mission(wps, mission_layer)
    show_messages(messages, message_layer)
    show_failsafe(messages, failsafe_layer)

    print('\n{0}.html saved. Open in browser to show track'.format(filename))
    base_map.save('{0}.html'.format(filename))


def show_data_and_map(log, filename):
    max_altitude = 0
    max_distance = 0
    total_distance = 0
    last_bat_msg = None
    last_gps_msg = None
    first_gps_msg = None
    longest_distance_gps = None
    points = []
    wps = []
    messages = []

    while True:
        msg = log.recv_match(type=['GPS', 'MSG', 'MODE', 'BAT', 'BARO', 'CMD'], blocking=True)
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
                longest_distance_gps = msg

        if mtype == 'MSG':
            messages.append([msg.Message, last_gps_msg.Lat, last_gps_msg.Lng])

        if mtype == 'MODE':
            messages.append(["Mode: {0}".format(msg.Mode), last_gps_msg.Lat, last_gps_msg.Lng])

        if mtype == 'BARO':
            alt = msg.Alt
            if alt > max_altitude:
                max_altitude = alt

    print('\nFlight statistics:')
    print('Total time: %.2f sec' % (last_bat_msg.TimeUS / 1000000))
    print('Maximum altitude: %.2f m' % max_altitude)
    print('Used: %.2f mAh' % last_bat_msg.CurrTot)
    print(f'Home location: {first_gps_msg.Lat}, {first_gps_msg.Lng}')
    print(f'Last known location: {last_gps_msg.Lat}, {last_gps_msg.Lng}')
    print('Total distance: %.2f km' % (total_distance / 1000))
    print('Maximum range: %.2f km' % (max_distance / 1000))
    print('Average efficiency: %.2f mAh/km' % (last_bat_msg.CurrTot * 1000 / total_distance))

    info_html = '<table>' \
                '<tr><th col=2>Flight information</th></tr>' \
                '<tr><td>Total time</td><td>{0:.2f} sec</td></tr>' \
                '<tr><td>Max altitude</td><td>{1:.2f} m</td></tr>' \
                '<tr><td>Battery used</td><td>{2:.2f} mAh</td></tr>' \
                '<tr><td>Total distance</td><td>{3:.2f} km</td></tr>' \
                '<tr><td>Maximum range</td><td>{4:.2f} km</td></tr>' \
                '<tr><td>Average efficiency</td><td>{5:.2f} mAh/km</td></tr>' \
                '</table>'.format((last_bat_msg.TimeUS / 1000000),
                                  max_altitude,
                                  last_bat_msg.CurrTot,
                                  total_distance / 1000,
                                  max_distance / 1000,
                                  last_bat_msg.CurrTot * 1000 / total_distance
                                  )

    draw_map(filename, first_gps_msg, last_gps_msg, longest_distance_gps, points, wps, max_distance, messages,
             info_html)


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
        show_data_and_map(mlog, args.logfile)
