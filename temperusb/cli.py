# encoding: utf-8
from __future__ import print_function, absolute_import
import argparse
import logging

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
    parser.add_argument("-S", "--sensor_count", type=int,
                        help="Override auto-detected number of sensors on the device")
    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    quiet = args.celsius or args.fahrenheit

    logging.basicConfig(level = logging.ERROR if quiet else logging.WARNING)

    th = TemperHandler()
    devs = th.get_devices()
    if not quiet:
        print("Found %i devices" % len(devs))

    readings = []

    for dev in devs:
        if args.sensor_count is not None:
            # Override auto-detection from args
            dev.set_sensor_count(int(args.sensor_count))

        if args.sensor_ids == 'all':
            sensors = range(dev.get_sensor_count())
        else:
            sensors = [int(args.sensor_ids)]

        readings.append(dev.get_temperatures(sensors=sensors))

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
                    portinfo = " (bus %(bus)s - port %(ports)s)" % reading[sensor]
                tempinfo += '%0.1f°C %0.1f°F; ' % (
                    reading[sensor]['temperature_c'],
                    reading[sensor]['temperature_f'],
                )
            tempinfo = tempinfo[0:len(output) - 2]

            output = 'Device #%i%s: %s' % (i, portinfo, tempinfo)
        print(output)


if __name__ == '__main__':
    main()
