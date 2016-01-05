# encoding: utf-8
from __future__ import print_function
from temperusb.temper import TemperHandler
import getopt, sys, os.path

def usage():
    print("%s [-p] [-q] [-c|-f] [-s 0|1|all] [-S 1|2] [-h|--help]" % os.path.basename(sys.argv[0]))
    print("  -q    quiet: only output temperature as a floating number. Usefull for external program parsing")
    print("        this option requires the use of -c or -f")
    print("  -c    with -q, outputs temperature in celcius degrees.")
    print("  -f    with -q, outputs temperature in fahrenheit degrees.")
    print("  -s    sensor ID 0, 1, or all, to utilize that sensor(s) on the device (multisensor devices only).  Default: 0")
    print("  -S    specify the number of sensors on the device.  Default: 1")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], ":hpcfqs:S:", ["help"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    degree_unit = False
    sensor_count = 1  # Default unless specified otherwise
    sensor_id = [0,]  # Default to first sensor unless specified
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
                    # convert to list
                    sensor_id = [sensor_id,]
                except ValueError as err:
                    print(str(err))
                    usage()
                    sys.exit(3)
        elif o == "-S":
            try:
                sensor_count = int(a)
                if not (sensor_count == 1 or sensor_count == 2):
                    raise ValueError(
                        "sensor_count should be 1 or 2, %d given" % sensor_count
                        )
            except ValueError as err:
                print(str(err))
                usage()
                sys.exit(4)
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            raise RuntimeError("Unhandled option '%s'" % o)

    if quiet_output and not degree_unit:
        print('You need to specify unit (-c of -f) when using -q option')
        sys.exit(1)

    # handle the sensor_id "all" option - convert to number of sensors
    if sensor_id == "all":
        sensor_id = range(0, sensor_count)

    if not set(sensor_id).issubset(range(0, sensor_count)):
        print('You specified a sensor_id (-s), without specifying -S with an appropriate number of sensors')
        sys.exit(5)

    th = TemperHandler()
    devs = th.get_devices()
    readings = []
    if not quiet_output:
        print("Found %i devices" % len(devs))

    for dev in devs:
        dev.set_sensor_count(sensor_count)
        readings.append(dev.get_temperatures(sensors=sensor_id))

    for i, reading in enumerate(readings):
        output = ''
        if quiet_output:
            if degree_unit == 'c':
                dict_key = 'temperature_c'
            elif degree_unit == 'f':
                dict_key = 'temperature_f'
            else:
                raise ValueError('degree_unit expected to be c or f, got %s' % degree_unit)

            for sensor in sorted(reading):
                output += '%0.1f; ' % reading[sensor][dict_key]
            output = output[0:len(output) - 2]
        else:
            portinfo = ''
            tempinfo = ''
            for sensor in sorted(reading):
                if disp_ports and portinfo == '':
                    portinfo = " (bus %s - port %s)" % (reading['bus'],
                                                        reading['ports'])
                tempinfo += '%0.1f°C %0.1f°F; ' % (
                    reading[sensor]['temperature_c'],
                    reading[sensor]['temperature_f'],
                )
            tempinfo = tempinfo[0:len(output) - 2]

            output = 'Device #%i%s: %s' % (
                i,
                portinfo,
                tempinfo,
            )
        print(output)

if __name__ == '__main__':
    main()
