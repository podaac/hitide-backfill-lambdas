# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

### Added
- Poetry Update
### Deprecated
### Removed
### Fixed
### Security


## [0.4.0]

### Added
- Migrated into public Github [hitide-backfill-lambdas](https://github.com/podaac/hitide-backfill-lambdas) repo
  - Combined hitide-backfill-post-step lambda and hitide-backfill-sqs-to-step into one repo
### Deprecated
### Removed
### Fixed
### Security


## [0.3.0] hitide-backfill-post-step

### Added
- Update lambda use arm architecture
### Deprecated
### Removed
### Fixed
- Fixed lambdas to make to python 3.9
### Security


## [0.3.0] hitide-backfill-sqs-to-step

### Added
 - Update lambda to use arm architechture
### Deprecated
### Removed
### Fixed
### Security


## [0.2.2] hitide-backfill-post-step

### Added
  - Updated python version to 3.9, poetry version to 1.5.1, and dependency libraries
### Deprecated
### Removed
### Fixed
### Security


## [0.2.1] hitide-backfill-post-step

### Added
### Deprecated
### Removed
### Fixed
- **PODAAC-5274
  - Change orm query into raw sql query to get step execution count
  - Added cron job to calculate db counts
### Security


## [0.2.1] hitide-backfill-sqs-to-step

### Added
  - Updated python version to 3.9, poetry version to 1.5.1, and dependency libraries
### Deprecated
### Removed
### Fixed
### Security


## [0.2.0] hitide-backfill-post-step

### Added
- **PODAAC-5229
  - Added Dmrpp columns to tables
  - Change way we count how many success and failures
### Deprecated
### Removed
### Fixed
### Security


## [0.2.0] hitide-backfill-sqs-to-step

### Added
- **PODAAC-5127**
  - Added in ability to create dmrpp workflows and parallelized step function creation.
### Deprecated
### Removed
### Fixed
### Security


## [0.1.0] hitide-backfill-post-step

### Added
- **PODAAC-4424**
  - Implementation of hitide backfill post step function lambda.
  - add mysql db
### Deprecated
### Removed
### Fixed
### Security


## [0.1.0] hitide-backfill-sqs-to-step

### Added
- **PODAAC-4424**
  - Implementation of hitide backfill sqs to step function lambda.
### Deprecated
### Removed
### Fixed
### Security
