# Changelog


## [0.7.4] - 2022-06-20
### Fixed
- crash wiht new version of Click (>=8.1) (#140)
### Added
- templates for bug reporting

## [0.7.3] - 2021-12-15
### Fixed
- STL export (#127)

## [0.7.2] - 2021-12-02
### Fixed
- String representation of the CityJSON class works again

## [0.7.1] - 2021-12-01
### Fixed
- save operator was crashing for unknown reasons sometimes, this is fixed


## [0.7.0] - 2021-12-01
### Changed
- Minimum required CityJSON version is 1.1
- Many operators names changed, it's now "property-verb", so that all the operators related to textures for instance are together
- The metadata are only updated (with lineage) when there is a [metadata-extended](https://github.com/cityjson/metadata-extended) property in the file, otherwise nothing is modified
- The schema validator (operator `validate`) is not written in Python anymore and part of cjio, it's using [cjval](https://github.com/cityjson/cjval) and its [Python binding](https://github.com/cityjson/cjvalpy) (which needs to be installed). The validator is several orders of magniture faster too

### Added
- A new operator `triangulate` that triangulates each surface of the input (de-triangulate coming soon)

### Fixed
- Several bugs were fixed

### API
- Loading a file with `cityjson.load()` removes the `transform` property from the file


## [0.6.10] - 2021-10-18
### Changed
- Minimum required Python is 3.6

### Fixed
- Click option is set to None when empty (#99)
- Loading breaks on inconsistent semantics (#102)
- extract_lod doesn't work with the improved LoD (#80)

### API changes
- Added `CityJSON.load_from_j`
- Make transformation the default on loading a cityjson
- `CityJSON.add_to_j` includes `reference_geometry`, no need to call it separately

## [0.6.9] - 2021-07-06
### Changed
- version with schemas 1.0.3 (where metadata schema is fixed)
- fix bugs with operators `update_metadata_cmd()` and `get_metadata_cmd()` crashing


## [0.6.8] - 2021-03-19
### Changed
- fix bug about datetime in schema but not put in metadata


## [0.6.7] - 2021-03-12
### Changed
- fix bug: crash when validating files containing Extensions under Windows


## [0.6.0] - 2020-10-27
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
