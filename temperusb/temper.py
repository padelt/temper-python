# encoding: utf-8
#
# Handles devices reporting themselves as USB VID/PID 0C45:7401 (mine also says RDing TEMPerV1.2).
#
# Copyright 2012-2014 Philipp Adelt <info@philipp.adelt.net>
#
# This code is licensed under the GNU public license (GPL). See LICENSE.md for details.

import usb
import sys
import struct
import os
import re

VIDPIDs = [(0x0c45L,0x7401L)]
REQ_INT_LEN = 8
REQ_BULK_LEN = 8
TIMEOUT = 2000
USB_PORTS_STR = '^\s*(\d+)-(\d+(?:\.\d+)*)'
CALIB_LINE_STR = USB_PORTS_STR +\
    '\s*:\s*scale\s*=\s*([+|-]?\d*\.\d+)\s*,\s*offset\s*=\s*([+|-]?\d*\.\d+)'

USB_SYS_PREFIX='/sys/bus/usb/devices/'

def readattr(path, name):
    """Read attribute from sysfs and return as string"""
    try:
        f = open(USB_SYS_PREFIX + path + "/" + name);
        return f.readline().rstrip("\n");
    except IOError:
        return None

def find_ports(bus, device):
    """look into sysfs and find a device that matches given\
    bus/device ID combination, then returns the port chain it is\
    plugged on."""
    bus_id = int(bus.dirname)
    dev_id = int(device.filename)
    for dirent in os.listdir(USB_SYS_PREFIX):
        matches = re.match(USB_PORTS_STR + '$', dirent)
        if matches:
            bus_str = readattr(dirent, 'busnum')
            if bus_str:
                busnum = int(bus_str)
            else:
                busnum = None
            dev_str = readattr(dirent, 'devnum')
            if dev_str:
                devnum = int(dev_str)
            else:
                devnum = None
            if busnum == bus_id and devnum == dev_id:
                return matches.groups()[1]

class TemperDevice():
    def __init__(self, device, bus):
        self._device = device
        self._bus = bus
        self._handle = None
        self._ports = find_ports(bus, device)
        self.set_calibration_data()

    def set_calibration_data(self):
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
        if self._ports:
            return self._ports
        else:
            return ""

    def get_bus(self):
        if self._bus and hasattr(self._bus, 'dirname'):
            return str(int(self._bus.dirname))
        else:
            return ""

    def get_temperature(self, format='celsius'):
        try:
            if not self._handle:
                self._handle = self._device.open()
                try:
                    self._handle.detachKernelDriver(0)
                except usb.USBError:
                    pass
                try:
                    self._handle.detachKernelDriver(1)
                except usb.USBError:
                    pass
                self._handle.setConfiguration(1)
                self._handle.claimInterface(0)
                self._handle.claimInterface(1)
                self._handle.controlMsg(requestType=0x21, request=0x09, value=0x0201, index=0x00, buffer="\x01\x01", timeout=TIMEOUT) # ini_control_transfer

            self._control_transfer(self._handle, "\x01\x80\x33\x01\x00\x00\x00\x00") # uTemperatura
            self._interrupt_read(self._handle)
            self._control_transfer(self._handle, "\x01\x82\x77\x01\x00\x00\x00\x00") # uIni1
            self._interrupt_read(self._handle)
            self._control_transfer(self._handle, "\x01\x86\xff\x01\x00\x00\x00\x00") # uIni2
            self._interrupt_read(self._handle)
            self._interrupt_read(self._handle)
            self._control_transfer(self._handle, "\x01\x80\x33\x01\x00\x00\x00\x00") # uTemperatura
            data = self._interrupt_read(self._handle)
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
        except usb.USBError, e:
            self.close()
            if "not permitted" in str(e):
                raise Exception("Permission problem accessing USB. Maybe I need to run as root?")
            else:
                raise

    def close(self):
        if self._handle:
            try:
                self._handle.releaseInterface()
            except ValueError:
                pass
            self._handle = None

    def _control_transfer(self, handle, data):
        handle.controlMsg(requestType=0x21, request=0x09, value=0x0200, index=0x01, buffer=data, timeout=TIMEOUT)

    def _interrupt_read(self, handle):
        return handle.interruptRead(0x82, REQ_INT_LEN)


class TemperHandler():
    def __init__(self):
        busses = usb.busses()
        self._devices = []
        for bus in busses:
            self._devices.extend([TemperDevice(x, bus) for x in bus.devices if (x.idVendor,x.idProduct) in VIDPIDs])

    def get_devices(self):
        return self._devices
