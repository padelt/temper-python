# encoding: utf-8
#
# TEMPer USB temperature/humidty sensor device driver settings.
# Handles devices reporting themselves as USB VID/PID 0C45:7401 (mine also says
# RDing TEMPerV1.2).
#
# Copyright 2012-2020 Philipp Adelt <info@philipp.adelt.net> and contributors.
#
# This code is licensed under the GNU public license (GPL). See LICENSE.md for
# details.

from enum import Enum

class TemperType(Enum):
    FM75 = 0
    SI7021 = 1

class TemperConfig:
    def __init__(
        self,
        temp_sens_offsets: list,
        hum_sens_offsets: list = None,
        type: TemperType = TemperType.FM75,
    ):
        self.temp_sens_offsets = temp_sens_offsets
        self.hum_sens_offsets = hum_sens_offsets
        self.type = type


DEVICE_LIBRARY = {
    "TEMPerV1.2": TemperConfig(
        temp_sens_offsets=[2],
        hum_sens_offsets=None,
        type=TemperType.FM75,
    ),
    "TEMPer1F_V1.3": TemperConfig(
        # Has only 1 sensor at offset 4
        temp_sens_offsets=[4],
        hum_sens_offsets=None,
        type=TemperType.FM75,
    ),
    "TEMPERHUM1V1.3": TemperConfig(
        temp_sens_offsets=[2],
        hum_sens_offsets=[4],
        type=TemperType.SI7021,
    ),
    "TEMPer1F_H1_V1.4": TemperConfig(
        temp_sens_offsets=[2],
        hum_sens_offsets=[4],
        type=TemperType.FM75,
    ),
    "TEMPerNTC1.O": TemperConfig(
        temp_sens_offsets=[2, 4, 6],
        hum_sens_offsets=None,
        type=TemperType.FM75,
    ),
    "TEMPer1V1.4": TemperConfig(
        temp_sens_offsets=[2],
        hum_sens_offsets=None,
        type=TemperType.FM75,
    ),
    # The config used if the sensor type is not recognised.
    # If your sensor is working but showing as unrecognised, please
    # add a new entry above based on "generic_fm75" below, and submit 
    # a PR to https://github.com/padelt/temper-python/pulls
    "generic_fm75": TemperConfig(
        temp_sens_offsets=[2, 4],
        hum_sens_offsets=None,
        type=TemperType.FM75,
    ),
}
