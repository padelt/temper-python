# encoding: utf-8
from __future__ import print_function
from temper import TemperHandler
import getopt, sys, os.path

def usage():
    print("%s [-p] [-q] [-c|-f] [-h|--help]" % os.path.basename(sys.argv[0]))
    print("  -q    quiet: only output temperature as a floating number. Usefull for external program parsing")
    print("        this option requires the use of -c or -f")
    print("  -c    with -q, outputs temperature in celcius degrees.")
    print("  -f    with -q, outputs temperature in fahrenheit degrees.")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], ":hpcfq", ["help"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    degree_unit = False
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
                         'temperature_c': dev.get_temperature(),
                         'temperature_f':
                         dev.get_temperature(format="fahrenheit"),
                         'ports': dev.get_ports(),
                         'bus': dev.get_bus()
                         })

    for reading in readings:
        if quiet_output:
            if degree_unit == 'c':
                print('%0.1f'
                    % reading['temperature_c'])
            elif degree_unit == 'f':
                print('%0.1f'
                    % reading['temperature_f'])
            else:
                print('how did I end up here?')
                sys.exit(1)
        else:
            if disp_ports:
                portinfo = " (bus %s - port %s)" % (reading['bus'],
                                                    reading['ports'])
            else:
                portinfo = ""
            print('Device #%i%s: %0.1f°C %0.1f°F' 
                  % (reading['device'],
                     portinfo,
                     reading['temperature_c'],
                     reading['temperature_f']))
