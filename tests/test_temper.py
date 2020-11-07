"""
pytests for temperusb

run from the project root with:
pytest --cov=temperusb
"""

import os

import pytest
import usb
from unittest.mock import MagicMock, patch, Mock

import temperusb

from temperusb.temper import TIMEOUT


@pytest.mark.parametrize(
    [
        "productname",
        "vid",
        "pid",
        "ctrl_data_in_expected",
        "data_out_raw",
        "temperature_out_expected",
    ],
    [
        [
            "TEMPerV1.2",
            0x0C45,
            0x7401,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A",  # 0x201A converts to 32.1C (fm75)
            32.1,
        ],
        # [
        #     "TEMPer1F_V1.3",  # Has 2 sensors
        #     0x0C45,
        #     0x7401,
        #     b"\x01\x80\x33\x01\x00\x00\x00\x00",
        #     b"\x00\x00\x20\x1A\x2B\x33",  # 0x201A,0x2B33 converts to 32.1C, 43.2C (fm75)
        #     32.1,
        # ],
        [
            "TEMPERHUM1V1.3",
            0x0C45,
            0x7401,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x56\x2C",  # 0x562C converts to 12.3C (si7021)
            12.3,
        ],
        [
            "TEMPer1F_H1_V1.4",
            0x0C45,
            0x7401,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A",  # 0x201A converts to 32.1C (fm75)
            32.1,
        ],
        [
            "TEMPerNTC1.O",
            0x0C45,
            0x7401,
            b"\x01\x80\x33\x01\x00\x00\x00\x00",
            b"\x00\x00\x20\x1A\x2B\x33\x36\x4D",  # 0x201A,0x2B33,0x364D converts to 32.1,43.2,54.3C (fm75)
            32.1,
        ],
    ],
)
def test_TemperDevice(
    productname, vid, pid, ctrl_data_in_expected, data_out_raw, temperature_out_expected
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
    # print("usbdev.bus=%s" % usbdev.bus)
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

    # read a temperature
    results = devs[0].get_temperatures(None)
    # check the temperature is what we were expecting.
    assert results[0]["temperature_c"] == pytest.approx(temperature_out_expected, 0.01)
