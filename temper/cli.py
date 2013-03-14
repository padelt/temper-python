# encoding: utf-8
from __future__ import print_function
from temper import TemperHandler


def main():
    th = TemperHandler()
    devs = th.get_devices()
    readings = []
    print("Found %i devices" % len(devs))

    for i, dev in enumerate(devs):
        readings.append({'device': i,
                         'temperature_c': dev.get_temperature(),
                         'temperature_f':
                         dev.get_temperature(format="fahrenheit")
                         })

    for reading in readings:
        print('Device #%i: %0.1f°C %0.1f°F' % (reading['device'],
                                               reading['temperature_c'],
                                               reading['temperature_f']))
