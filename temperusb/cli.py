# encoding: utf-8
from __future__ import print_function, absolute_import
import argparse

from .temper import TemperHandler


def parse_args():
    descr = "Temperature data from a TEMPer v1.2 sensor."

    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument("-p", "--disp_ports", action='store_true',
                        help="Display ports")
    units = parser.add_mutually_exclusive_group(required=False)
    units.add_argument("-c", "--celsius", action='store_true',
                       help="Quiet: just degrees celcius as decimal")
    units.add_argument("-f", "--fahrenheit", action='store_true',
                       help="Quiet: just degrees fahrenheit as decimal")
    parser.add_argument("-s", "--sensor_ids", choices=['0', '1', 'all'],
                        help="IDs of sensors to use on the device " +
                        "(multisensor devices only)", default='0')
    parser.add_argument("-S", "--sensor_count", choices=[1, 2], type=int,
                        help="Specify the number of sensors on the device",
                        default='1')
    args = parser.parse_args()

    args.sensor_ids = list(range(args.sensor_count)) if args.sensor_ids == 'all' \
        else [int(args.sensor_ids)]
    return args


def main():
    args = parse_args()
    quiet = args.celsius or args.fahrenheit

    th = TemperHandler()
    devs = th.get_devices()
    if not quiet:
        print("Found %i devices" % len(devs))

    readings = []

    for dev in devs:
        dev.set_sensor_count(args.sensor_count)
        readings.append(dev.get_temperatures(sensors=args.sensor_ids))

    for i, reading in enumerate(readings):
        output = ''
        if quiet:
            if args.celsius:
                dict_key = 'temperature_c'
            elif args.fahrenheit:
                dict_key = 'temperature_f'

            for sensor in sorted(reading):
                output += '%0.1f; ' % reading[sensor][dict_key]
            output = output[0:len(output) - 2]
        else:
            portinfo = ''
            tempinfo = ''
            for sensor in sorted(reading):
                if args.disp_ports and portinfo == '':
                    portinfo = " (bus %s - port %s)" % (reading['bus'],
                                                        reading['ports'])
                tempinfo += '%0.1f°C %0.1f°F; ' % (
                    reading[sensor]['temperature_c'],
                    reading[sensor]['temperature_f'],
                )
            tempinfo = tempinfo[0:len(output) - 2]

            output = 'Device #%i%s: %s' % (i, portinfo, tempinfo)
        print(output)


if __name__ == '__main__':
    main()
