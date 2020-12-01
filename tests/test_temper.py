"""
pytests for temperusb

run from the project root with:
pytest --cov=temperusb --cov-report term-missing
"""

import os
import pytest
import usb
from unittest.mock import MagicMock, patch, Mock

import temperusb
from temperusb.temper import TIMEOUT


@pytest.mark.parametrize(
    [
        "productname",  # the faked usb device product name
        "vid",  # faked vendor ID
        "pid",  # faked vendor ID
        "count",  # number of sensors we are expect to be reported
        "ctrl_data_in_expected",  # the ctrl data we expect to be sent to the (faked) usb device
        "data_out_raw",  # the bytes that the usb device will return (our encoded temp/RHs needs to be in here)
        "temperature_out_expected",  # array of temperatures that we are expecting to see decoded.
        "humidity_out_expected",  # array of humidities that we are expecting to see decoded
    ],
    [
        [
            "generic_unmatched",  # Default is to assume 2 fm75 style temperature sensors
            0x0C45,
            0x7401,
            2,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A\x2B\x33",  # 0x201A,0x2B33 converts to 32.1C, 43.2C (fm75)
            [32.1, 43.2],
            None,
        ],
        [
            "TEMPerV1.2",
            0x0C45,
            0x7401,
            1,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A",  # 0x201A converts to 32.1C (fm75)
            [32.1],
            None,
        ],
        [
            "TEMPer1F_V1.3",  # Has 1 sensor at offset 4
            0x0C45,
            0x7401,
            1,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x00\x00\x20\x1A",  # 0x201A converts to 32.1C (fm75)
            [32.1],
            None,
        ],
        [
            "TEMPERHUM1V1.3",
            0x0C45,
            0x7401,
            1,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x56\x2C\xBF\xB1",  # 0x562C,0xBFB1 converts to 12.3C,87.6% (si7021)
            [12.3],
            [87.6],
        ],
        [
            "TEMPer1F_H1_V1.4",
            0x0C45,
            0x7401,
            1,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A\x0C\x0C",  # 0x201A,0x0C0C converts to 32.1C,98.7% (fm75)
            [32.1],
            [98.7],
        ],
        [
            "TEMPerNTC1.O",
            0x0C45,
            0x7401,
            3,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A\x2B\x33\x36\x4D",  # 0x201A,0x2B33,0x364D converts to 32.1,43.2,54.3C (fm75)
            [32.1, 43.2, 54.3],
            None,
        ],
    ],
)
def test_TemperDevice(
    productname,
    vid,
    pid,
    count,
    ctrl_data_in_expected,
    data_out_raw,
    temperature_out_expected,
    humidity_out_expected,
):
    """
    Patches the underlying usb port call to allow us to verify the data
    we would be sending, and fake the return data so that we can test the
    conversion coming back.
    """
    usbdev = Mock(bus="fakebus", product=productname)
    usbdev.is_kernel_driver_active = MagicMock(return_value=False)

    def ctrl_transfer_dummy(
        bmRequestType, bRequest, wValue, wIndex, data_or_wLength, timeout
    ):
        assert data_or_wLength == ctrl_data_in_expected
        assert timeout == TIMEOUT

    usbdev.ctrl_transfer = MagicMock(
        bmRequestType=0x21,
        bRequest=0x09,
        wValue=0x0200,
        wIndex=0x01,
        data_or_wLength=None,
        timeout=None,
        side_effect=ctrl_transfer_dummy,
    )
    usbdev.read = Mock(return_value=data_out_raw)

    def match_pids(find_all, idVendor, idProduct):
        if idVendor == vid and idProduct == pid:
            return [usbdev]
        else:
            return []

    with patch("usb.core.find", side_effect=match_pids, return_value=[usbdev]):
        th = temperusb.TemperHandler()
    devs = th.get_devices()
    # Check that we actually got any devices
    assert devs != None
    # Check that we only found one sensor
    assert len(devs) == 1, "Should be only one sensor type matching"

    dev = devs[0]

    # check that the sensor count reported is what we expect
    assert dev.get_sensor_count() == count
    # read a temperature
    results = dev.get_temperatures(None)

    for i, temperature in enumerate(temperature_out_expected):
        # check the temperature is what we were expecting.
        assert results[i]["temperature_c"] == pytest.approx(temperature, 0.01)

    # if the device is expected to also report humidty
    if humidity_out_expected:
        for i, humidity in enumerate(humidity_out_expected):
            results_h = dev.get_humidity(None)
            assert results_h[i]["humidity_pc"] == pytest.approx(humidity, 0.1)
