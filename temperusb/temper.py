# encoding: utf-8
#
# Handles devices reporting themselves as USB VID/PID 0C45:7401 (mine also says
# RDing TEMPerV1.2).
#
# Copyright 2012-2020 Philipp Adelt <info@philipp.adelt.net> and contributors.
#
# This code is licensed under the GNU public license (GPL). See LICENSE.md for
# details.

import usb
import os
import re
import logging
import struct

from .device_library import DEVICE_LIBRARY, TemperType, TemperConfig

VIDPIDS = [
    (0x0c45, 0x7401),
    (0x0c45, 0x7402),
]
REQ_INT_LEN = 8
ENDPOINT = 0x82
INTERFACE = 1
CONFIG_NO = 1
TIMEOUT = 5000
USB_PORTS_STR = r'^\s*(\d+)-(\d+(?:\.\d+)*)'
CALIB_LINE_STR = USB_PORTS_STR +\
    r'\s*:\s*scale\s*=\s*([+|-]?\d*\.\d+)\s*,\s*offset\s*=\s*([+|-]?\d*\.\d+)'
USB_SYS_PREFIX = '/sys/bus/usb/devices/'
COMMANDS = {
    'temp': b'\x01\x80\x33\x01\x00\x00\x00\x00',
    'ini1': b'\x01\x82\x77\x01\x00\x00\x00\x00',
    'ini2': b'\x01\x86\xff\x01\x00\x00\x00\x00',
}
LOGGER = logging.getLogger(__name__)
CONTRIBUTE_URL = "https://github.com/padelt/temper-python/issues"


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
    def __init__(self, device, sensor_count=1):
        self.set_sensor_count(sensor_count)

        self._device = device
        self._bus = device.bus
        self._ports = getattr(device, 'port_number', None)
        if self._ports == None:
            self._ports = find_ports(device)
        self.set_calibration_data()
        try:
            # Try to trigger a USB permission issue early so the
            # user is not presented with seemingly unrelated error message.
            # https://github.com/padelt/temper-python/issues/63
            productname = self._device.product
        except ValueError as e:
            if 'langid' in str(e):
                raise usb.core.USBError("Error reading langids from device. "+
                "This might be a permission issue. Please check that the device "+
                "node for your TEMPer devices can be read and written by the "+
                "user running this code. The temperusb README.md contains hints "+
                "about how to fix this. Search for 'USB device permissions'.")

        config = DEVICE_LIBRARY.get(productname)
        if config is None:
            LOGGER.warning(
                "Unrecognised sensor type '%s'. "
                "Trying to guess communication format. "
                "Please add the configuration to 'device_library.py' "
                "and submit to %s to benefit other users."
                % (self._device.product, CONTRIBUTE_URL)
            )
            config = DEVICE_LIBRARY["generic_fm75"]
        self.temp_sens_offsets = config.temp_sens_offsets
        self.hum_sens_offsets = config.hum_sens_offsets
        self.type = config.type

        self.set_sensor_count(self.lookup_sensor_count())
        LOGGER.debug('Found device | Bus:{0} Ports:{1} SensorCount:{2}'.format(
            self._bus, self._ports, self._sensor_count))

    def set_calibration_data(self, scale=None, offset=None):
        """
        Set device calibration data based on settings in /etc/temper.conf.
        """
        if scale is not None and offset is not None:
            self._scale = scale
            self._offset = offset
        elif scale is None and offset is None:
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
                        if (str(ports) == str(self._ports)) and (str(bus) == str(self._bus)):
                            self._scale = scale
                            self._offset = offset
        else:
            raise RuntimeError("Must set both scale and offset, or neither")

    def lookup_offset(self, sensor):
        """
        Lookup the number of sensors on the device by product name.
        """
        return self.temp_sens_offsets[sensor]

    def lookup_humidity_offset(self, sensor):
        """
        Get the offset of the humidity data.
        """
        if self.hum_sens_offsets:
            return self.hum_sens_offsets[sensor]
        else:
            return None

    def lookup_sensor_count(self):
        """
        Lookup the number of sensors on the device by product name.
        """
        return len(self.temp_sens_offsets)

    def get_sensor_count(self):
        """
        Get number of sensors on the device.
        """
        return self._sensor_count

    def set_sensor_count(self, count):
        """
        Set number of sensors on the device.

        To do: revamp /etc/temper.conf file to include this data.
        """
        # Currently this only supports 1 and 2 sensor models.
        # If you have the 8 sensor model, please contribute to the
        # discussion here: https://github.com/padelt/temper-python/issues
        if count not in [1, 2, 3]:
            raise ValueError('Only sensor_count of 1-3 supported')

        self._sensor_count = int(count)

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

    def get_data(self, reset_device=False):
        """
        Get data from the USB device.
        """
        try:
            if reset_device:
                self._device.reset()

            # detach kernel driver from both interfaces if attached, so we can set_configuration()
            for interface in [0,1]:
                if self._device.is_kernel_driver_active(interface):
                    LOGGER.debug('Detaching kernel driver for interface %d '
                        'of %r on ports %r', interface, self._device, self._ports)
                    self._device.detach_kernel_driver(interface)

            self._device.set_configuration()

            # Prevent kernel message:
            # "usbfs: process <PID> (python) did not claim interface x before use"
            # This will become unnecessary once pull-request #124 for
            # PyUSB has been accepted and we depend on a fixed release
            # of PyUSB.  Until then, and even with the fix applied, it
            # does not hurt to explicitly claim the interface.
            usb.util.claim_interface(self._device, INTERFACE)

            # Turns out we don't actually need that ctrl_transfer.
            # Disabling this reduces number of USBErrors from ~7/30 to 0!
            #self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
            #    wValue=0x0201, wIndex=0x00, data_or_wLength='\x01\x01',
            #    timeout=TIMEOUT)


            # Magic: Our TEMPerV1.4 likes to be asked twice.  When
            # only asked once, it get's stuck on the next access and
            # requires a reset.
            self._control_transfer(COMMANDS['temp'])
            self._interrupt_read()

            # Turns out a whole lot of that magic seems unnecessary.
            #self._control_transfer(COMMANDS['ini1'])
            #self._interrupt_read()
            #self._control_transfer(COMMANDS['ini2'])
            #self._interrupt_read()
            #self._interrupt_read()

            # Get temperature
            self._control_transfer(COMMANDS['temp'])
            temp_data = self._interrupt_read()

            # Get humidity
            LOGGER.debug("ID='%s'" % self._device.product)
            if self.hum_sens_offsets:
                humidity_data = temp_data
            else:
                humidity_data = None

            # Combine temperature and humidity data
            data = {'temp_data': temp_data, 'humidity_data': humidity_data}

            # Be a nice citizen and undo potential interface claiming.
            # Also see: https://github.com/walac/pyusb/blob/master/docs/tutorial.rst#dont-be-selfish
            usb.util.dispose_resources(self._device)
            return data
        except usb.USBError as err:
            if not reset_device:
                LOGGER.warning("Encountered %s, resetting %r and trying again.", err, self._device)
                return self.get_data(True)

            # Catch the permissions exception and add our message
            if "not permitted" in str(err):
                raise Exception(
                    "Permission problem accessing USB. "
                    "Maybe I need to run as root?")
            else:
                LOGGER.error(err)
                raise

    def get_temperature(self, format='celsius', sensor=0):
        """
        Get device temperature reading.
        """
        results = self.get_temperatures(sensors=[sensor,])

        if format == 'celsius':
            return results[sensor]['temperature_c']
        elif format == 'fahrenheit':
            return results[sensor]['temperature_f']
        elif format == 'millicelsius':
            return results[sensor]['temperature_mc']
        else:
            raise ValueError("Unknown format")

    def get_temperatures(self, sensors=None):
        """
        Get device temperature reading.

        Params:
        - sensors: optional list of sensors to get a reading for, examples:
          [0,] - get reading for sensor 0
          [0, 1,] - get reading for sensors 0 and 1
          None - get readings for all sensors
        """
        _sensors = sensors
        if _sensors is None:
            _sensors = list(range(0, self._sensor_count))

        if not set(_sensors).issubset(list(range(0, self._sensor_count))):
            raise ValueError(
                'Some or all of the sensors in the list %s are out of range '
                'given a sensor_count of %d.  Valid range: %s' % (
                    _sensors,
                    self._sensor_count,
                    list(range(0, self._sensor_count)),
                )
            )

        data = self.get_data()
        data = data['temp_data']

        results = {}

        # Interpret device response
        for sensor in _sensors:
            offset = self.lookup_offset(sensor)
            if self.type == TemperType.SI7021: 
                celsius = struct.unpack_from('>h', data, offset)[0] * 175.72 / 65536 - 46.85
            else: # fm75 (?) type device
                celsius = struct.unpack_from('>h', data, offset)[0] / 256.0
            # Apply scaling and offset (if any)
            celsius = celsius * self._scale + self._offset
            results[sensor] = {
                'ports': self.get_ports(),
                'bus': self.get_bus(),
                'sensor': sensor,
                'temperature_f': celsius * 1.8 + 32.0,
                'temperature_c': celsius,
                'temperature_mc': celsius * 1000,
                'temperature_k': celsius + 273.15,
            }

        return results

    def get_humidity(self, sensors=None):
        """
        Get device humidity reading.

        Params:
        - sensors: optional list of sensors to get a reading for, examples:
          [0,] - get reading for sensor 0
          [0, 1,] - get reading for sensors 0 and 1
          None - get readings for all sensors
        """
        _sensors = sensors
        if _sensors is None:
            _sensors = list(range(0, self._sensor_count))

        if not set(_sensors).issubset(list(range(0, self._sensor_count))):
            raise ValueError(
                'Some or all of the sensors in the list %s are out of range '
                'given a sensor_count of %d.  Valid range: %s' % (
                    _sensors,
                    self._sensor_count,
                    list(range(0, self._sensor_count)),
                )
            )
        data = self.get_data()
        data = data['humidity_data']
        results = {}

        # Interpret device response
        for sensor in _sensors:
            offset = self.lookup_humidity_offset(sensor)
            if offset is None:
                continue
            if self.type == TemperType.SI7021:
                humidity = (struct.unpack_from('>H', data, offset)[0] * 125) / 65536 -6
            else:  #fm75 (?) type device
                humidity = (struct.unpack_from('>H', data, offset)[0] * 32) / 1000.0
            results[sensor] = {
                'ports': self.get_ports(),
                'bus': self.get_bus(),
                'sensor': sensor,
                'humidity_pc': humidity,
            }

        return results

    def _control_transfer(self, data):
        """
        Send device a control request with standard parameters and <data> as
        payload.
        """
        LOGGER.debug('Ctrl transfer: %r', data)
        self._device.ctrl_transfer(bmRequestType=0x21, bRequest=0x09,
            wValue=0x0200, wIndex=0x01, data_or_wLength=data, timeout=TIMEOUT)

    def _interrupt_read(self):
        """
        Read data from device.
        """
        data = self._device.read(ENDPOINT, REQ_INT_LEN, timeout=TIMEOUT)
        LOGGER.debug('Read data: %r', data)
        return data

    def close(self):
        """Does nothing in this device. Other device types may need to do cleanup here."""
        pass


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
