# encoding: utf-8
#
# Handles devices reporting themselves as USB VID/PID 0C45:7401 (mine also says
# RDing TEMPerV1.2).
#
# Copyright 2012-2014 Philipp Adelt <info@philipp.adelt.net>
#
# This code is licensed under the GNU public license (GPL). See LICENSE.md for
# details.

import usb
import sys
import struct
import os
import re
import logging

VIDPIDS = [
    (0x0c45L, 0x7401L),
]
REQ_INT_LEN = 8
ENDPOINT = 0x82
INTERFACE = 1
CONFIG_NO = 1
TIMEOUT = 5000
USB_PORTS_STR = '^\s*(\d+)-(\d+(?:\.\d+)*)'
CALIB_LINE_STR = USB_PORTS_STR +\
    '\s*:\s*scale\s*=\s*([+|-]?\d*\.\d+)\s*,\s*offset\s*=\s*([+|-]?\d*\.\d+)'
USB_SYS_PREFIX = '/sys/bus/usb/devices/'
COMMANDS = {
    'temp': '\x01\x80\x33\x01\x00\x00\x00\x00',
    'ini1': '\x01\x82\x77\x01\x00\x00\x00\x00',
    'ini2': '\x01\x86\xff\x01\x00\x00\x00\x00',
}
LOGGER = logging.getLogger(__name__)


def readattr(path, name):
    """
    Read attribute from sysfs and return as string
    """
    try:
        f = open(USB_SYS_PREFIX + path + "/" + name)
        return f.readline().rstrip("\n")
    except IOError:
        return None


def find_ports(device):
    """
    Find the port chain a device is plugged on.

    This is done by searching sysfs for a device that matches the device
    bus/address combination.

    Useful when the underlying usb lib does not return device.port_number for
    whatever reason.
    """
    bus_id = device.bus
    dev_id = device.address
    for dirent in os.listdir(USB_SYS_PREFIX):
        matches = re.match(USB_PORTS_STR + '$', dirent)
        if matches:
            bus_str = readattr(dirent, 'busnum')
            if bus_str:
                busnum = float(bus_str)
            else:
                busnum = None
            dev_str = readattr(dirent, 'devnum')
            if dev_str:
                devnum = float(dev_str)
            else:
                devnum = None
            if busnum == bus_id and devnum == dev_id:
                return str(matches.groups()[1])


class TemperDevice(object):
    """
    A TEMPer USB thermometer.
    """
    def __init__(self, device):
        self._device = device
        self._bus = device.bus
        self._ports = getattr(device, 'port_number', None)
        if self._ports == None:
            self._ports = find_ports(device)
        self.set_calibration_data()
        LOGGER.debug('Found device | Bus:{0} Ports:{1}'.format(
            self._bus, self._ports))

    def set_calibration_data(self):
        """
        Set device calibration data based on settings in /etc/temper.conf.
        """
        self._scale = 1.0
        self._offset = 0.0
        try:
            f = open('/etc/temper.conf', 'r')
        except IOError:
            f = None
        if f:
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                matches = re.match(CALIB_LINE_STR, line)
                if matches:
                    bus = int(matches.groups()[0])
                    ports = matches.groups()[1]
                    scale = float(matches.groups()[2])
                    offset = float(matches.groups()[3])
                    if ports == self._ports:
                        self._scale = scale
                        self._offset = offset

    def get_ports(self):
        """
        Get device USB ports.
        """
        if self._ports:
            return self._ports
        return '' 

    def get_bus(self):
        """
        Get device USB bus.
        """
        if self._bus:
            return self._bus
        return ''

    def get_temperature(self, format='celsius'):
        """
        Get device temperature reading.
        """
        try:
            # Take control of device if required
            if self._device.is_kernel_driver_active:
                LOGGER.debug('Taking control of device on bus {0} ports '
                    '{1}'.format(self._bus, self._ports))
                for interface in [0, 1]:
                    try:
                        self._device.detach_kernel_driver(interface)
                    except usb.USBError as err:
                        LOGGER.debug(err)
                self._device.set_configuration()
                self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
                    wValue=0x0201, wIndex=0x00, data_or_wLength='\x01\x01',
                    timeout=TIMEOUT)
            # Get temperature
            self._control_transfer(COMMANDS['temp'])
            self._interrupt_read()
            self._control_transfer(COMMANDS['ini1'])
            self._interrupt_read()
            self._control_transfer(COMMANDS['ini2'])
            self._interrupt_read()
            self._interrupt_read()
            self._control_transfer(COMMANDS['temp'])
            data = self._interrupt_read()
            self._device.reset()
        except usb.USBError as err:
            # Catch the permissions exception and add our message
            if "not permitted" in str(err):
                raise Exception(
                    "Permission problem accessing USB. "
                    "Maybe I need to run as root?")
            else:
                LOGGER.error(err)
                raise
        # Interpret device response
        data_s = "".join([chr(byte) for byte in data])
        temp_c = 125.0/32000.0*(struct.unpack('>h', data_s[2:4])[0])
        temp_c = temp_c * self._scale + self._offset
        if format == 'celsius':
            return temp_c
        elif format == 'fahrenheit':
            return temp_c*1.8+32.0
        elif format == 'millicelsius':
            return int(temp_c*1000)
        else:
            raise ValueError("Unknown format")

    def _control_transfer(self, data):
        """
        Send device a control request with standard parameters and <data> as
        payload.
        """
        LOGGER.debug('Ctrl transfer: {0}'.format(data))
        self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
            wValue=0x0200, wIndex=0x01, data_or_wLength=data, timeout=TIMEOUT)

    def _interrupt_read(self):
        """
        Read data from device.
        """
        data = self._device.read(ENDPOINT, REQ_INT_LEN, timeout=TIMEOUT)
        LOGGER.debug('Read data: {0}'.format(data))
        return data


class TemperHandler(object):
    """
    Handler for TEMPer USB thermometers.
    """

    def __init__(self):
        self._devices = []
        for vid, pid in VIDPIDS:
            self._devices += [TemperDevice(device) for device in \
                usb.core.find(find_all=True, idVendor=vid, idProduct=pid)]
	LOGGER.info('Found {0} TEMPer devices'.format(len(self._devices)))

    def get_devices(self):
        """
        Get a list of all devices attached to this handler
        """
        return self._devices
