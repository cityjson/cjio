# Changelog

## [0.6.0]
### Added
- Convert to Binary glTF (glb)
- Convert to Batched 3D Models (b3dm) - Output is probably incorrect though
- Progress bar for the `reproject` command
- Started a proof of concept for an API. You can read about the first struggles in `docs/design_document.ipynb`. Mainly implemented in `models` and a few additional methods in `cityjson`. Plus a bunch of tests for the API ([#13](https://github.com/cityjson/cjio/pull/13))
- Add tutorials and dedicated documentation 
- Docker image and Travis build for it ([#25](https://github.com/cityjson/cjio/pull/25))
- Generate metadata ([#56](https://github.com/cityjson/cjio/pull/56))
- STL export format ([#66](https://github.com/cityjson/cjio/pull/66))

### Changed
- click messages, warnings got their functions and placed into the `utils` module
- only EPSG codes are supported for the CRS's URN
- When `--indent` is passed to `save`, tabs are used instead of spaces. Results in smaller files.

### Fixes
- Fix precision when removing duplicates ([#50](https://github.com/cityjson/cjio/pull/60))


## [0.5.4] - 2019-06-18
### Changed
- proper schemas are packaged
- clean() operator added

## [0.5.2] - 2019-04-29
### Changed
- CityJSON v1.0.0 supported
- subset() operator: invert --> exclude (clearer for the users)


## [0.5.1] - 2019-02-06
### Changed
- CityJSON schemas v0.9 added
- cjio supports only CityJSON v0.9, there's an operator to upgrade files ('upgrade_version')
- validate supports CityJSON Extensions from v0.9
### Added
- new operators, like 'extract_lod', 'export' (to .obj), 'reproject'


## [0.4.0] - 2018-09-25
### Changed
- CityJSON schemas v08 added
- new operators
- validate now supports CityJSON Extensions


## [0.2.1] - 2018-05-24
### Changed
- schemas were not uploaded to pypi, now they are


## [0.2.0] - 2018-05-24
### Added
- hosted on pypi
- decompress
- fix of bugs
