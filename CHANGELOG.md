# Change log
All notable changes to this project will be documented in this file.

* This project adheres to [Semantic Versioning](http://semver.org/).
* This project follows the guidelines outlined on [keepachangelog.com](http://keepachangelog.com/).

## [Unreleased]

No changes yet.

## [next-1.6.0]

Major changes:
- A new architecture for supporting different device types.
- Tests using pytest

### Added
- Add support for 3 sensor tempers and TEMPerNTC1.O
- Add support for TemperHUM with si7021 type sensor
- Add support for TEMPer1V1.4

### Fixed
- Fixes for the munin plugin
- Report TEMPerV1.2 devices as having a single sensor
- Fix error message about USB permissions to display correctly on Python 3.6

## [1.5.3] - 2017-04-03 - Commit ID: 4da8be1
### Added
- Support for 0c45:7402 (RDing TEMPer1F_H1_V1.4) including humidity
- Hints for local development
- Add release documentation to `DEVELOPMENT.md`.
### Fixed
- Negative temperature readings incorrectly wrapped around to very high temperatures
- Fixed format string error in the munin plugin (PR#71)

## [1.5.2] - 2016-09-07 - Commit ID: e904dbe
### Fixed
- Clarification of install documentation from eric-s-raymond.
- Workaround for misleading error message when at least one TEMPer USB device node has insufficient permissions. (#63)

## [1.5.1] - 2016-06-12 - Commit ID: ceb0617
### Added
- Support for `TEMPer1F_V1.3`'s behaviour: Only one sensor, data is at offset 4 from ps-jay.

### Fixed
- Comparing only port without bus may lead to calibration being applied to multiple devices instead of one from ps-jay.

## [1.5.0] - 2016-04-20 - Commit ID: 8752b14
### Added
- Changelog file. 
