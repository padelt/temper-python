# Change log
All notable changes to this project will be documented in this file.

* This project adheres to [Semantic Versioning](http://semver.org/).
* This project follows the guidelines outlined on [keepachangelog.com](http://keepachangelog.com/).

## [Unreleased]
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
