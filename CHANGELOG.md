# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Revamped UI when adding cards:
  - to Google Keep: ![demo](./CHANGELOG_RESOURCES/cards-ui--google-keep.png)
  - to GitHub:
    - with --issue: ![demo](./CHANGELOG_RESOURCES/cards-ui--github-user-project.png)
    - without --issue: ![demo](./CHANGELOG_RESOURCES/cards-ui--github-repo-project.png)

- Revamped "Logging in..." message for Google Keep

## [0.7.0] - 2020-06-19

### Added

- [[#19](https://github.com/ewen-lbh/ideaseed/issues/19)] Option `-l`/`--label`: alias for `--tag`.

### Fixed

- A `KeyError: 'color'` was raised when creating a label.

## [0.6.0] - 2020-06-19

### Added

- [[#5](https://github.com/ewen-lbh/ideaseed/issues/5)] Add `--pin` to pin Google Keep cards

## [0.5.0] - 2020-06-19

### Added

- [[#9](https://github.com/ewen-lbh/ideaseed/issues/9)] Make `--tag` work with `--issue`: When creating an issue, `--tag=TAG` means "Add label `TAG` to the created issue".

## [0.4.1] - 2020-06-19

### Fixed

- Fix error "undeclared variable `Literal`" (from `cli_box`).

## [0.4.0] - 2020-06-18

### Added

- [[#10](https://github.com/ewen-lbh/ideaseed/issues/10)] Add "Update available" notification when a new update is available, and prompts to download the new version, then re-runs the command using the new version.

## [0.3.0] - 2020-06-17

### Added

- [[#15](https://github.com/ewen-lbh/ideaseed/issues/15)] Add aliases for color names: "cyan" means "teal", "magenta" means "purple", etc. (see `ideaseed --help`, section "Color names") Those aliases behave like other colors, and thus `--color cy` expands to `cyan`, which is then resolved to `teal`.

### Fixed

- When using Google Keep, the "Logging in..." message was printed only when the login was finished (at the same time as " Done.").

## [0.2.1] - 2020-06-16

### Fixed

- Fix `AuthenticatedUser has no attribute 'get_projects'` when using user profile projects.

## [0.2.0] - 2020-06-16

### Added

- Add option `-o`/`--open`: Open the relevant URL in your webbrowser (eg. open "https://github.com/owner/repository/issues/issue-number" after creating an issue)

### Fixed

- Fix default color generating a `KeyError`
  
## [0.1.0] - 2020-06-16

Initial release. See <https://pypi.org/project/ideaseed/0.1.0/> for documentation.

[Unreleased]: https://github.com/ewen-lbh/ideaseed/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/ewen-lbh/ideaseed/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/ewen-lbh/ideaseed/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/ewen-lbh/ideaseed/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/ewen-lbh/ideaseed/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/ewen-lbh/ideaseed/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ewen-lbh/ideaseed/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/ewen-lbh/ideaseed/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/ewen-lbh/ideaseed/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ewen-lbh/ideaseed/releases/tag/v0.1.0
