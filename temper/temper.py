#!/usr/bin/python
# encoding: utf-8
#
# Handles devices reporting themselves as USB VID/PID 0C45:7401 (mine also says RDing TEMPerV1.2).
#
# Copyright 2012, 2013 Philipp Adelt <info@philipp.adelt.net>
#
# This code is licensed under the GNU public license (GPL). See LICENSE.md for details.

import usb
import sys
import struct

VIDPIDs = [(0x0c45L,0x7401L)]
REQ_INT_LEN = 8
REQ_BULK_LEN = 8
TIMEOUT = 2000

class TemperDevice():
    def __init__(self, device):
        self._device = device
        self._handle = None

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
            self._devices.extend([TemperDevice(x) for x in bus.devices if (x.idVendor,x.idProduct) in VIDPIDs])

    def get_devices(self):
        return self._devices

if __name__ == '__main__':
    th = TemperHandler()
    devs = th.get_devices()
    print "Found %i devices" % len(devs)
    for i, dev in enumerate(devs):
        print "Device #%i: %0.1f°C %0.1f°F" % (i, dev.get_temperature(), dev.get_temperature(format="fahrenheit"))
