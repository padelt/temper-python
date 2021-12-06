This is a rewrite of a userspace USB driver for TEMPer devices presenting
a USB ID like this: `0c45:7401 Microdia`
My device came from [M-Ware ID7747](http://www.m-ware.de/m-ware-usb-thermometer-40--120-c-emailbenachrichtigung-id7747/a-7747/)
and also reports itself as 'RDing TEMPerV1.2'.

Also provides a passpersist-module for NetSNMP (as found in the `snmpd`
packages of Debian and Ubuntu) to present the temperature of 1-3 USB devices
via SNMP.

### Reported working devices

| USB ID                                                       | Name Reported            | Notes                   |
| ------------------------------------------------------------ | ------------------------ | ----------------------- |
| `0c45:7401 Microdia`                                         | `RDing TEMPerV1.2`       | First supported device  |
| `0c45:7401 Microdia TEMPer Temperature Sensor`               | `RDing TEMPer2_M12_V1.3` | Two sensor device       |
| `0c45:7401 Microdia`                                         | `RDing TEMPer1F_V1.3`    | Single external sensor, but better precision is possible by using "sensor 2" |
| `0c45:7401 Microdia`                                         | `RDing TEMPerV1.4`       |                         |
| `0c45:7402 Microdia TEMPerHUM Temperature & Humidity Sensor` | `RDing TEMPer1F_H1_V1.4` | Single sensor which reports both temperature and relative-humidity |

# Requirements

Basically, `libusb` bindings for python (PyUSB) and `snmp-passpersist` from PyPI.

Under Debian/Ubuntu, treat yourself to some package goodness:

    sudo apt-get install python-usb python-setuptools snmpd # The latter is only necessary for SNMP-usage.
    sudo easy_install snmp-passpersist

# Installation and usage

To install using pip, run

    pip install temperusb

To install from source, clone the repository, cd into its top-level directory, and run

    sudo python setup.py install

you should end up with two scripts conveniently installed:

    /usr/local/bin/temper-poll
    /usr/local/bin/temper-snmp

If your system does not provide access as a normal user to the USB device, you need to run them as root. See "USB device permissions" section for more on this.

temper-poll accepts -p option now, which adds the USB bus and port information each device is plugged on.

without -p option

    $ temper-poll
    Found 1 devices
    Device #0: 22.5°C 72.5°F

with -p option

    $ temper-poll -p
    Found 1 devices
    Device #0 (bus 1 - port 1.3): 22.4°C 72.3°F

Which tells you there is a USB hub plugged (internally or externally) on the port 1 of the bus 1 of the host, and your TEMPer device  is on the port 3 of that hub.

## Tell kernel to leave TEMPer alone 

Regarding errors:

- `usb.core.USBError: [Errno 16] Resource busy`
- `Unknown error`

By default, the Linux kernel claims (e.g. opens/uses) the TEMPer device as a keyboard (HID device).
When that happens, this script is not able to set the configuration and communicate with it.

You will see one of those two errors when running `sudo temper-poll`. Your `dmesg` log will show something similar to this:

    usb 1-1.3: usbfs: interface 0 claimed by usbhid while 'temper-poll' sets config #1

To prevent this, add this to the kernel command line:

    usbhid.quirks=0x0c45:0x7401:0x4

On Raspbian, this will be `/boot/cmdline.txt`. Reboot after saving and retry. Hat tip to and more information from [AndiDog here](http://unix.stackexchange.com/questions/55495/prevent-usbhid-from-claiming-usb-device).

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

Then restart.

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
The highest of all measured temperatures in degrees Celsius as an integer is reported.

    pass_persist    .1.3.6.1.4.1.318.1.1.1.2.2.2 /usr/local/bin/temper-snmp

Alternatively, emulate a Cisco device's temperature information with the following.
The first three detected devices will be reported as ..13.1.3.1.3.1, ..3.2 and ..3.3 .
The value is the temperature in degree Celsius as an integer.

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

# Using MQTT
While temper-python does not directly support MQTT, it is fairly straightforeward to push the temperature values collected to a MQTT broker periodically, so they may be integrated in for example Home-Assistant.

In the below example we will show how to push data to a Mosquitto MQTT broker using a small bash script and a CRON job. The setup was tested with temper-python installed on a RaspberryPi running Rasbian Buster and a Mosquitto MQTT broker installed as part of Home-Assistant.

In this example we will publish one specific temperature value for one specific device, for example the temperatue in Celcius for device 0
To test this, type on your console:
    
    $ /usr/local/bin/temper-poll -c -s 0
    1.9

As you can see because of the "-c" option, temper-poll will present a single temperature value in degrees Celcius. To get degrees Farenheit, use option "-f"
The "-s 0" option makes sure temper-poll only looks at Device #0

We now need to install the Mosquitto client on the device where you installed temper-python. This will provide the mosquitto_pub client which we will use to push towards the MQTT broker
    
     sudo apt-get install mosquitto-clients

To start pushing a value to your MQTT broker, you also need to know the MQTT server IP adress and optionally a username and password.
A mosquitto_pub command looks something like this:
    
     /usr/bin/mosquitto_pub -h MQTT_IP -m "Some message" -t MQTT_TOPIC -u MQTT_USERNAME -P MQTT_PASSWORD

If you need more paramaters, have a look at the output of 
    
     mosquitto_pub --help

If needed, use the "-d" option for mosquitto_pub, which will print debug output about the connection. A successful connection debug print should look like:
    
     pi@raspberrypi:~ $ /usr/bin/mosquitto_pub -h 10.0.0.* -m "foobar" -t home-assistant/temper_schuur/temperature -u ****** -P ****** -d
     Client mosqpub|2107-raspberryp sending CONNECT
     Client mosqpub|2107-raspberryp received CONNACK (0)
     Client mosqpub|2107-raspberryp sending PUBLISH (d0, q0, r0, m1, 'home-assistant/temper_schuur/temperature', ... (0 bytes))
     Client mosqpub|2107-raspberryp sending DISCONNECT

We will now combine the two using a small bash script called "temper-push-mqtt". First create the script, then make it executable. 
    
     sudo touch /usr/local/bin/temper-push-mqtt
     sudo chmod a+x /usr/local/bin/temper-push-mqtt
     sudo nano /usr/local/bin/temper-push-mqtt

The script should contain:
    
     #! /bin/bash
     T=$(/usr/local/bin/temper-poll -c -s 0)
     /usr/bin/mosquitto_pub -h MQTT_IP -m "${T}" -t MQTT_TOPIC -u MQTT_USER -P MQTT_PASSWORD

If you need other parameters for temper-poll, replace them here. Also replace all MQTT_* values with proper values for you local setup. 
If you are using Home-Assistant you should add a sensor to you setup by defining it in configuration.yaml:
    
     sensor:
       - platform: mqtt
         name: "Temperatuur Schuur"
         state_topic: "home-assistant/temper_schuur/temperature"
         unit_of_measurement: "°C"

Make sure the state_topic value matches the MQTT_TOPIC value in the temper-push-mqtt script

Finally, to make sure we get periodic data, we create a cron job to run the script every 5 minutes
    
     sudo crontab -e 

To start a new crontab, which should contain
    
     */5 * * * *  /usr/local/bin/temper-push-mqtt  > /var/log/cron_temper-push-mqtt.log 2>&1

The above cronjob will run the temper-push-mqtt script every 5 minutes and will log any issues to a logfile /var/log/cron_temper-push-mqtt.log

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

## Note by GM3D

Since calibration parameters must be set per each device, we need some way to identify them physically. As mentioned above, the serial number for all TEMPer devices is zero, so there is no true way to tell which is which programmatically. The USB device number does not work either since it changes every time you reboot the machine or plug/unplug the device. The way that possibly can work is identifying them by the combination of the bus number and the USB port (possibly a chain of ports, if you have hubs in between), which is what I am doing for now.

This information is basically the same with what you can get with `lsusb -t` and is based on the information in the sysfs directory `/sys/bus/usb/devices` (see below). So far I am assuming this scheme is persistent enough for regular use cases, but even the bus number may change in some cases like - for example - if your machine is a tablet like machine and you hotplug it to a keyboard dock with a USB root hub in it. In such case you will need to re-run `lsusb` and adjust the bus-port numbers in the configuration file accordingly. At the moment I have no clue about SNMP OID persistence.

# Calibration parameters

You can have parameters in the configuration file `/etc/temper.conf` for each of your TEMPer device to calibrate its value with simple linear formula. If there is not this file on your machine it's fine, calibration is just skipped. The same if the program can't find a matching line with the actual device on the system.

Format of calibration lines in `/etc/temper.conf` is:

    n-m(.m)* : scale = a, offset = b

where `n` is the USB bus number and `m` is (possibly a chain of) the USB port(s) 
which your TEMPer device is plugged on. `a` and `b` are some floating values decided by experiment, we will come back to this later, first let me describe how n and m can be decided for your device.

You will need to use `lsusb` command in usbutils package to decide `n` and `m`. Use `lsusb` with and without `-t` option.

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

Now look at the second output. Looking at this tree, your TEMPer device (Dev 16) on the bus 01 is connected to your pc through two ports, port 4 and port 3.
Don't worry about two devices having the same Dev ID = 16, they both belong to a single TEMPer device (it uses two USB interfaces by default, which is normal).

So in this example, `n = 1` and `m = 4.3`; thus the config file should be like

    1-4.3: scale = a, offset = b

with `a` and `b` replaced with the actual values which you will need to measure and 
calculate for your own TEMPer device. These values are used in the formula

    y = a * x + b

where

* `y`: calibrated temperature (in Celsius),
* `x`: raw temperature read from your TEMPer device (in Celsius).

You will need to find appropriate values for `a` and `b` for your TEMPer device by doing some experiment and basic math. Either comparing it with another thermometer which you can rely on or measuring two temperatures which you already know ... like iced water and boiling water, but make sure in the latter case that you seal your TEMPer device firmly in a plastic bag or something, since it is NOT waterproof!

To find out bus and port numbers, you can also try running temper-poll with -p option, which will contain information in the form (bus 1 - port 4.3) in the above example. This might be actually easier than looking at the `lsusb` outputs, as long as it works.

# Origins

The USB interaction pattern is extracted from [here](http://www.isp-sl.com/pcsensor-1.0.0.tgz)
as seen on [Google+](https://plus.google.com/105569853186899442987/posts/N9T7xAjEtyF).

# Compatibility with Python versions

This should work on Python 3.5 and above. It was tested with Python 3.5, 3.6, 3.7, 3.8, 3.9, 3.10.

# Authors

* Original rewrite by Philipp Adelt <autosort-github@philipp.adelt.net>
* Additional work by Brian Cline
* Calibration code by Joji Monma (@GM3D on Github)
* Munin plugin by Alexander Schier (@allo- on Github)
* PyPI package work and rewrite to `libusb1` by James Stewart (@amorphic on Github)
* Reduced kernel messages, support multiple sensors, and support TEMPer1F_V1.3 by Philip Jay (@ps-jay on Github)
* Python 3 compatibility and rewrite of cli.py to use argparse by Will Furnass (@willfurnass on Github)
* TEMPerV1.4 support by Christian von Roques (@roques on Github)
* Pytest and architecture improvement by Dave Thompson (@davet2001 on Github).
