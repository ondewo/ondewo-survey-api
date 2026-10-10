# Release History

*****************

## Release ONDEWO Survey Server API 2.0.1

### Improvements

* [[OND211-2333]](https://ondewo.atlassian.net/browse/OND211-2333) - Document every service, RPC, message and field in `survey.proto` and `fhir.proto` (HTML-formatted comments for the generated API documentation; trailing inline field comments moved into the field documentation). Comment-only: no service, RPC, message, field or field number changed, so the API is wire-compatible with 2.0.0
* Add `make build_docs` / `make clean_docs_builder` to reproduce the documentation workflow locally, and `unrelease` targets to undo a release (GitHub release, release branch and tag)
* Release tooling: the release-notes slice ends at the `*****` separator instead of the first `**`; `release_all_clients` runs the clients in parallel, isolates per-client failures and fails loudly instead of reporting them as already released; the generated client release notes are markdownlint-clean and are not inserted twice; secret values are masked in echoed recipe lines; `update_githubio` no longer corrupts `data.js`
* Utils Docker image on `python:3.12-slim`, portable (GNU/BSD) Makefile edits with `perl` instead of `sed`, `actions/checkout@v5` in the documentation workflow
* Pre-commit: language-agnostic hook set (markdownlint-cli2, pre-commit-hooks, conventional-pre-commit before giticket)

*****************

## Release ONDEWO Survey Server API 2.0.0

### Improvements

* Synchronize API Client Versions

*****************

## Release ONDEWO Survey Server API 1.1.0

### Improvements

* [[OND211-2039]](https://ondewo.atlassian.net/browse/OND211-2039) - added pre-commit hooks and adjusted files to them

*****************

## Release ONDEWO Survey Server API 1.0.1

### Improvements

* Documentation Updated

*****************

## Release ONDEWO Survey Server API 1.0.0

### Improvements

* [[OND211-2039]](https://ondewo.atlassian.net/browse/OND211-2039) - Automated Release Process

*****************

## Release ONDEWO Survey Server API 0.6.0

### New Features

* [[OND214-24]](https://ondewo.atlassian.net/browse/OND214-24) - Addition of the FHIR compatibility servicer
* [[OND214-24]](https://ondewo.atlassian.net/browse/OND214-24) - Addition of the User Identifier to the UserInformation message
* [[OND214-24]](https://ondewo.atlassian.net/browse/OND214-24) - Additional filters on GetSurveyAnswersRequest: "user_id" and "phone_number"

*****************

## Release ONDEWO Survey Server API 0.5.0

### Improvements

* [[OND214-14]](https://ondewo.atlassian.net/browse/OND214-14) - Add Agent Status
* [[OND214-13]](https://ondewo.atlassian.net/browse/OND214-13) - Add user information to the extracted answers

*****************

## Release ONDEWO Survey Server API 0.4.1

### Bug Fixes

* [[OND214-7]](https://ondewo.atlassian.net/browse/OND214-7) - Add missing google proto dependencies

*****************

## Release ONDEWO Survey Server API 0.4.0

### Improvements

* [[OND214-5]](https://ondewo.atlassian.net/browse/OND214-5) - CRUD support for Surveys
* [[OND214-6]](https://ondewo.atlassian.net/browse/OND214-6) - Adapt to new API definition of NLU 3.x.x

*****************

## Release ONDEWO Survey Server API 0.3.0

### New Features

* Survey. Add update survey endpoint with field mask support

### Improvements

* Questions. Add field 'value' to choices that represents the canonical value of the synonyms

### Bug Fixes

* Set protobuf syntax to proto 3

*****************

## Release ONDEWO Survey Server API 0.2.2

### Improvements

* Updated README

*****************

## Release ONDEWO Survey Server API 0.2.1

### Bug fixes

* Updated licenses.

*****************

## Release ONDEWO Survey Server API 0.2.0

### New Features

* Move to GitHub!

### Improvements

* No longer closed source.

### Bug fixes

### Breaking Changes

### Known issues not covered in this release

### Migration Guide

* [Replace submodule](https://stackoverflow.com/a/1260982/7756727) in the client.

*****************

## Release ONDEWO APIS 0.1.0

### New Features

* Refactored individual project APIs into seperate repos.

### Improvements

* Easier to develop independently.

### Bug fixes

### Breaking Changes

### Known issues not covered in this release

* Harder to install apis under one heading-- this will be addressed at a later date.

### Migration Guide

* [Replace submodule](https://stackoverflow.com/a/1260982/7756727) in the client.

*****************
