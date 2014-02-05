# encoding: utf-8
#
# Run snmp_temper.py as a pass-persist module for NetSNMP.
# See README.md for instructions.
# 
# Copyright 2012-2014 Philipp Adelt <info@philipp.adelt.net>
#
# This code is licensed under the GNU public license (GPL). See LICENSE.md for details.

import os
import sys
import syslog
import threading
import snmp_passpersist as snmp
from temper import TemperHandler, TemperDevice

ERROR_TEMPERATURE = 9999


def _unbuffered_handle(fd):
    return os.fdopen(fd.fileno(), 'w', 0)


class LogWriter():
    def __init__(self, ident='temper-python', facility=syslog.LOG_DAEMON):
        syslog.openlog(ident, 0, facility)
    def write_log(self, message, prio=syslog.LOG_INFO):
        syslog.syslog(prio, message)

class Updater():
    def __init__(self, pp, logger, testmode=False):
        self.logger = logger
        self.pp = pp
        self.testmode = testmode
        self.usb_lock = threading.Lock() # used to stop reinitialization interfering with update-thread
        self._initialize()

    def _initialize(self):
        with self.usb_lock:
            try:
                self.th = TemperHandler()
                self.devs = self.th.get_devices()
                self.logger.write_log('Found %i thermometer devices.' % len(self.devs))
                for i, d in enumerate(self.devs):
                    self.logger.write_log('Initial temperature of device #%i: %0.1f degree celsius' % (i, d.get_temperature()))
            except Exception, e:
                self.logger.write_log('Exception while initializing: %s' % str(e))

    def _reinitialize(self):
        # Tries to close all known devices and starts over.
        self.logger.write_log('Reinitializing devices')
        with self.usb_lock:
            for i,d in enumerate(self.devs):
                try:
                    d.close()
                except Exception, e:
                    self.logger.write_log('Exception closing device #%i: %s' % (i, str(e))) 
        self._initialize()

    def update(self):
        if self.testmode:
            # APC Internal/Battery Temperature
            self.pp.add_int('318.1.1.1.2.2.2.0', 99)
            # Cisco devices temperature OIDs
            self.pp.add_int('9.9.13.1.3.1.3.1', 97)
            self.pp.add_int('9.9.13.1.3.1.3.2', 98)
            self.pp.add_int('9.9.13.1.3.1.3.3', 99)
        else:
            try:
                with self.usb_lock:
                    self.pp.add_int('318.1.1.1.2.2.2.0', int(max([d.get_temperature() for d in self.devs])))
                    for i, dev in enumerate(self.devs[:3]): # use max. first 3 devices
                        self.pp.add_int('9.9.13.1.3.1.3.%i' % (i+1), int(dev.get_temperature()))
            except Exception, e:
                self.logger.write_log('Exception while updating data: %s' % str(e))
                # Report an exceptionally large temperature to set off all alarms.
                # snmp_passpersist does not expose an API to remove an OID.
                for oid in ('318.1.1.1.2.2.2.0', '9.9.13.1.3.1.3.1', '9.9.13.1.3.1.3.2', '9.9.13.1.3.1.3.3'):
                    self.pp.add_int(oid, ERROR_TEMPERATURE)
                self.logger.write_log('Starting reinitialize after error on update')
                self._reinitialize()


def main():
    sys.stdout = _unbuffered_handle(sys.stdout)
    pp = snmp.PassPersist(".1.3.6.1.4.1")
    logger = LogWriter()
    upd = Updater(pp, logger, testmode=('--testmode' in sys.argv))
    pp.start(upd.update, 5) # update every 5s


if __name__ == '__main__':
    main()
