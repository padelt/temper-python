This is a rewrite of a userspace USB driver for TEMPer devices presenting
a USB ID like this: `0c45:7401 Microdia`
My device came from [M-Ware ID7747](http://www.m-ware.de/m-ware-usb-thermometer-40--120-c-emailbenachrichtigung-id7747/a-7747/)
and also reports itself as 'RDing TEMPerV1.2'.

Also provides a passpersist-module for NetSNMP (as found in the `snmpd`
packages of Debian and Ubuntu) to present the temperature of 1-3 USB devices
via SNMP.

# Requirements

Basically, `libusb` bindings for python (PyUSB) and `snmp-passpersist` from PyPI.

Under Debian/Ubuntu, treat yourself to some package goodness:

    sudo apt-get install python-usb python-setuptools snmpd # The latter is only necessary for SNMP-usage.
    sudo easy_install snmp-passpersist

# Usage

To print temperatures of all sensors found in the system, just run

    python temper/temper.py

If your udev installation does not provide access as a normal user to the
USB device, you need to run it as root:

    sudo python temper/temper.py

# Installation

After you run

    sudo python setup.py install

you should end up with two scripts conveniently installed:

    /usr/local/bin/temper-poll
    /usr/local/bin/temper-snmp

# Serving via SNMP

Using [NetSNMP](http://www.net-snmp.org/), you can use `temper/snmp.py`
as a `pass_persist` module.
You can choose one of two OIDs to be emulated: [APC's typical](http://www.oidview.com/mibs/318/PowerNet-MIB.html)
internal/battery temperature (.1.3.6.1.4.1.318.1.1.1.2.2.2.0) or
[Cisco's typical temperature
OIDs](http://tools.cisco.com/Support/SNMP/do/BrowseOID.do?local=en&translate=Translate&objectInput=1.3.6.1.4.1.9.9.13.1.3.1.3)
(.1.3.6.1.4.1.9.9.13.1.3.1.3.1 - 3.3).

Note that you _should not activate both_ modes at the same time.
The reason for this limitation is that the script will keep running for each
`pass_persist` entry and they will interfere with each other when updating the
temperature.
This typically leads to syslog entries like this:

    temper-python: Exception while updating data: could not release intf 1: Invalid argument

## USB device permissions

At least on Debian Wheezy, the default USB device node has permissions to only allow
access for root. In the same case, `snmpd` is running as the user `snmpd`. Bam. No access.
You might find a corresponding note in syslog.

To solve that, the file `99-tempsensor.rules` is a udev rule that allows access to the
specific USB devices (with matching VID/PID) by anyone. Install like this:

    sudo cp etc/99-tempsensor.rules /etc/udev/rules.d/

To check for success, find the bus and device IDs of the devices like this:

    pi@raspi-temper1 ~ $ lsusb | grep "0c45:7401"
    Bus 001 Device 004: ID 0c45:7401 Microdia 
    Bus 001 Device 005: ID 0c45:7401 Microdia 

    pi@raspi-temper1 ~ $ ls -l /dev/usb*
    crw------- 1 root root 189, 0 Jan  1  1970 /dev/usbdev1.1
    crw------- 1 root root 189, 1 Jan  1  1970 /dev/usbdev1.2
    crw------- 1 root root 189, 2 Jan  1  1970 /dev/usbdev1.3
    crw-rw-rwT 1 root root 189, 3 Jan  1  1970 /dev/usbdev1.4
    crw-rw-rwT 1 root root 189, 4 Jan  1  1970 /dev/usbdev1.5
    pi@raspi-temper1 ~ $ 

Note that `/dev/usbdev1.4` and `/dev/usbdev1.5` have permissions for read/write
for anyone, including `snmp`. This will work for the passpersist-module running
along with `snmpd`.

## What to add to snmpd.conf

To emulate an APC Battery/Internal temperature value, add something like this to snmpd.conf.
The highest of all measured temperatures in degrees celcius as an integer is reported.

    pass_persist    .1.3.6.1.4.1.318.1.1.1.2.2.2 /usr/local/bin/temper-snmp

Alternatively, emulate a Cisco device's temperature information with the following.
The first three detected devices will be reported as ..13.1.3.1.3.1, ..3.2 and ..3.3 .
The value is the temperature in degree celcius as an integer.

    pass_persist    .1.3.6.1.4.1.9.9.13.1.3 /usr/local/bin/temper-snmp

Add `--testmode` to the line (as an option to `snmp.py` to enable a mode where
APC reports 99°C and Cisco OIDs report 97, 98 and 99°C respectively. No actual devices
need to be installed but `libusb` and its Python bindings are still required.

The path `/usr/local/bin/` is correct if the installation using `python setup.py install`
did install the scripts there. If you prefer not to install them, find and use the
`temper/snmp.py` file.

## Troubleshooting NetSNMP-interaction

The error reporting of NetSNMP is underwhelming to say the least.
Expect every error to fail silently without a chance to find the source.

`snmp.py` reports some simple information to syslog with an ident string
of `temper-python` and a facility of `LOG_DAEMON`. So this should give you the available debug information:

    sudo tail -f /var/log/syslog | grep temper-python

Try stopping the snmpd daemon and starting it with logging to the console:

    sudo service snmpd stop
    sudo snmpd -f

It will _not_ start the passpersist-process for `snmp.py` immediately
but on the first request for the activated OIDs. This also means that the
first `snmpget` you try may fail like this:

    iso.3.6.1.4.1.9.9.13.1.3.1.3.2 = No Such Instance currently exists at this OID

To test the reporting, try this (twice if it first reports No Such Instance):

    snmpget -c public -v 2c localhost .1.3.6.1.4.1.9.9.13.1.3.1.3.1 # Cisco #1
    snmpget -c public -v 2c localhost .1.3.6.1.4.1.9.9.13.1.3.1.3.2 # Cisco #2
    snmpget -c public -v 2c localhost .1.3.6.1.4.1.9.9.13.1.3.1.3.3 # Cisco #3
    snmpget -c public -v 2c localhost .1.3.6.1.4.1.318.1.1.1.2.2.2.0 # APC

When NetSNMP starts the instance (upon first `snmpget`), you should see something like this in syslog:
    
    Jan  6 16:01:51 raspi-temper1 temper-python: Found 2 thermometer devices.
    Jan  6 16:01:51 raspi-temper1 temper-python: Initial temperature of device #0: 22.2 degree celsius
    Jan  6 16:01:51 raspi-temper1 temper-python: Initial temperature of device #1: 10.9 degree celsius

If you don't even see this, maybe the script has a problem and quits with an exception.
Try running it manually and mimik a passpersist-request (`->` means you should enter the rest of the line):

    -> sudo temper/snmp.py 
    -> PING
    <- PONG
    -> get
    -> .1.3.6.1.4.1.318.1.1.1.2.2.2.0
    <- .1.3.6.1.4.1.318.1.1.1.2.2.2.0
    <- INTEGER
    <- 22.25

If you have a problem with the USB side and want to test SNMP, run the script with `--testmode`.

# Note on multiple device usage

The devices I have seen do not have any way to identify them. The serial number is 0.
There is no way (and this driver does not make any attempt) to present a persistent
ordering among the USB devices. The effective order is the one that `libusb` presents.
That seems to be based on the enumeration order of the devices.

That in turn [seems to be](http://osr507doc.sco.com/en/man/html.HW/usb.HW.html#USBdevID)
based primarily on the physical ordering in the root hub -> hub port hierarchy on bootup.
But if you unplug and replug the device (or it gets detached due to a glitch and is
redetected) then the order of the devices may be changed.

If that happens, your temperature readings will change and you cannot say which device
belongs to what OID if you are using SNMP.

Long story short: Only use the device order if the USB bus is stable and you reboot after
any plugging on the device. Even then, you are not safe. Sorry.

# Calibration parameters
You can have parameters in the configuration file /etc/temper.conf for each of your TEMPer device to calibrate it's value with simple linear formula. If there is not this file on your machine it's fine, calibration is just skipped. The same if the program can't find a matching line with the actual device on the system.

Format of calibration lines in /etc/temper.conf is:

n-m(.m)* : scale = a, offset = b

where n is the USB bus number and m is (possibly a chain of) the USB port(s) 
which your TEMPer device is plugged on. a and be are some floating values decided by experiment, we will come back to this later, first let me describe how n and m can be decided for your device.

You will need to use lsusb command in usbutils package to decide n and m. Use lsusb with and without -t option.

For example, assume the following outputs;

$ lsusb
Bus 002 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 016: ID 0c45:7401 Microdia 
Bus 001 Device 015: ID 1a40:0101 TERMINUS TECHNOLOGY INC. USB-2.0 4-Port HUB
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub

$ lsusb -t
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=orion-ehci/1p, 480M
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=orion-ehci/1p, 480M
    |__ Port 4: Dev 15, If 0, Class=hub, Driver=hub/4p, 12M
        |__ Port 3: Dev 16, If 0, Class=HID, Driver=usbhid, 1.5M
        |__ Port 3: Dev 16, If 1, Class=HID, Driver=usbhid, 1.5M

First output tells you your TEMPer device (0c45:7401 Microdia) is on the bus 1 and has (just currently, it may change time to time, even if you don't move it around) device ID = 16.

Now look at the second output. looking this tree, your TEMPer device (Dev 16) on the bus 01 is connected to your pc through two ports, port 4 and port 3.
Don't worry about two devices having the same Dev ID = 16, they both belong to a single TEMPer device (it uses two USB interfaces by default, which is normal).

So in this example, n = 1 and m = 4.3; thus the config file should be like

1-4.3: scale = a, offset = b

with a and b replaced with the actual values which you will need to measure and 
calculate for your own TEMPer device. These values are used in the formula

y = a * x + b

where

y: calibrated temperature (in Celsius),
x: raw temperature read from your TEMPer device (in Celsius).

You will need to find appropriate values for a and b for your TEMPer device by doing some experiment. (Either comparing it with another thermometer which you can rely on or measuring two temperatures which you already know ... like iced water and boiling water, but make sure in the latter case that you seal your TEMPer device firmly in a plastic bag or something, since it is NOT waterproof!)

# Origins

The USB interaction pattern is extracted from [here](http://www.isp-sl.com/pcsensor-1.0.0.tgz)
as seen on [Google+](https://plus.google.com/105569853186899442987/posts/N9T7xAjEtyF).

# Authors

* Original rewrite by Philipp Adelt <autosort-github@philipp.adelt.net>
* Additional work by Brian Cline
* Calibration code by Joji Monma (@GM3D on Github)
