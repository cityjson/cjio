
# Changelog

## [Unreleased]
### Added
- Convert to Binary glTF (glb)
- Convert to Batched 3D Models (b3dm) - Output is probably incorrect though
- `tiling` module for partitioning a city model - The partitioner needs some attention because the number of partitions are fixed to 16
- Export to 3D Tiles - Due to the b3dm conversion issue, this is also experimental
- Progress bar for the `reproject` command

### Changed
- click messages, warnings got their functions and placed into the `utils` module
- `save`, `info`, `export` commands work with `partition`, thus they process each part
- only EPSG codes are supported for the CRS's URN

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
