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
    units.add_argument("-H", "--humidity", action='store_true',
                       help="Quiet: just percentage relative humidity as decimal")
    parser.add_argument("-s", "--sensor_ids", choices=['0', '1', 'all'],
                        help="IDs of sensors to use on the device " +
                        "(multisensor devices only)", default='0')
    parser.add_argument("-S", "--sensor_count", type=int,
                        help="Override auto-detected number of sensors on the device")
    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    quiet = args.celsius or args.fahrenheit or args.humidity

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

        temperatures = dev.get_temperatures(sensors=sensors)
        humidities = dev.get_humidity(sensors=sensors)
        combinations = {}
        for k, v in temperatures.items():
            c = v.copy()
            try:
                c.update(humidities[k])
            except:
                pass
            combinations[k] = c
        readings.append(combinations)

    for i, reading in enumerate(readings):
        output = ''
        if quiet:
            if args.celsius:
                dict_key = 'temperature_c'
            elif args.fahrenheit:
                dict_key = 'temperature_f'
            elif args.humidity:
                dict_key = 'humidity_pc'

            for sensor in sorted(reading):
                output += '%0.1f; ' % reading[sensor][dict_key]
            output = output[0:len(output) - 2]
        else:
            portinfo = ''
            tempinfo = ''
            huminfo = ''
            for sensor in sorted(reading):
                if args.disp_ports and portinfo == '':
                    portinfo = " (bus %(bus)s - port %(ports)s)" % reading[sensor]
                try:
                    tempinfo += '%0.1f°C %0.1f°F; ' % (
                        reading[sensor]['temperature_c'],
                        reading[sensor]['temperature_f'],
                    )
                except:
                    pass
                try:
                    huminfo += '%0.1f%%RH; ' % (reading[sensor]['humidity_pc'])
                except:
                    pass
            tempinfo = tempinfo[0:len(output) - 2]
            huminfo = huminfo[0:len(output) - 2]

            output = 'Device #%i%s: %s %s' % (i, portinfo, tempinfo, huminfo)
        print(output)


if __name__ == '__main__':
    main()
