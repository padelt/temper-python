# encoding: utf-8
from __future__ import print_function
from temper import TemperHandler
import getopt, sys, os.path

def usage():
    print("%s [-p] [-q] [-c|-f] [-s 0|1|all] [-h|--help]" % os.path.basename(sys.argv[0]))
    print("  -q    quiet: only output temperature as a floating number. Usefull for external program parsing")
    print("        this option requires the use of -c or -f")
    print("  -c    with -q, outputs temperature in celcius degrees.")
    print("  -f    with -q, outputs temperature in fahrenheit degrees.")
    print("  -s    sensor ID 0, 1, or all, to utilize that sensor(s) on the device (multisensor devices only).")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], ":hpcfqs:", ["help"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    degree_unit = False
    sensor_id = 0  # Default to first sensor unless specified
    disp_ports = False
    quiet_output = False
    for o, a in opts:
        if o == "-p":
            disp_ports = True
        elif o == "-c":
            degree_unit = 'c'
        elif o == "-f":
            degree_unit = 'f'
        elif o == "-q":
            quiet_output = True
        elif o == "-s":
            if a == "all":
                sensor_id = "all"
            else:
                try:
                    sensor_id = int(a)
                    if not (sensor_id == 0 or sensor_id == 1):
                        raise ValueError(
                            "sensor_id should be 0 or 1, %d given" % sensor_id
                            )
                except ValueError as err:
                    print(str(err))
                    usage()
                    sys.exit(3)
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    if quiet_output and not degree_unit:
        print('You need to specify unit (-c of -f) when using -q option')
        sys.exit(1)

    th = TemperHandler()
    devs = th.get_devices()
    readings = []
    if not quiet_output:
        print("Found %i devices" % len(devs))

    for i, dev in enumerate(devs):
        readings.append({'device': i,
                         'temperature_c': dev.get_temperature(sensor=sensor_id),
                         'temperature_f':
                         dev.get_temperature(format="fahrenheit",sensor=sensor_id),
                         'ports': dev.get_ports(),
                         'bus': dev.get_bus()
                         })

    for reading in readings:
        if quiet_output:
            if degree_unit == 'c':
                if type(reading['temperature_c']) is float:
                    print('%0.1f'
                        % reading['temperature_c'])
                else:
                    output = ''
                    for sensor in reading['temperature_c']:
                        output += '%0.1f; ' % sensor
                    output = output[0:len(output) - 2]
                    print(output)
            elif degree_unit == 'f':
                if type(reading['temperature_c']) is float:
                    print('%0.1f'
                        % reading['temperature_f'])
                else:
                    output = ''
                    for sensor in reading['temperature_f']:
                        output += '%0.1f; ' % sensor
                    output = output[0:len(output) - 2]
                    print(output)
            else:
                raise ValueError('degree_unit expected to be c or f, got %s' % degree_unit)
        else:
            if disp_ports:
                portinfo = " (bus %s - port %s)" % (reading['bus'],
                                                    reading['ports'])
            else:
                portinfo = ""

            if type(reading['temperature_c']) is float:
                print('Device #%i%s: %0.1f°C %0.1f°F'
                      % (reading['device'],
                         portinfo,
                         reading['temperature_c'],
                         reading['temperature_f']))
            else:
                output = 'Device #%i%s: ' % (
                    reading['device'],
                    portinfo,
                )
                for index in range(0, len(reading['temperature_c'])):
                    output += '%0.1f°C %0.1f°F; ' % (
                        reading['temperature_c'][index],
                        reading['temperature_f'][index],
                    )
                output = output[0:len(output) - 2]
                print(output)

if __name__ == '__main__':
    main()
