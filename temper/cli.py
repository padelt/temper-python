# encoding: utf-8
from __future__ import print_function
from temper import TemperHandler
import getopt, sys, os.path

def usage():
    print("%s [-p] [-h|--help]" % os.path.basename(sys.argv[0]))

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], ":hp", ["help"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    disp_ports = False
    for o, a in opts:
        if o == "-p":
            disp_ports = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    th = TemperHandler()
    devs = th.get_devices()
    readings = []
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
