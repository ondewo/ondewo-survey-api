<p align="center">
    <a href="https://www.ondewo.com">
      <img alt="ONDEWO Logo" src="https://raw.githubusercontent.com/ondewo/ondewo-logos/master/github/ondewo_logo_github_2.png"/>
    </a>
</p>

# ONDEWO SURVEY APIs

This repository contains the original interface definitions of public ONDEWO APIs that support gRPC protocols. Reading the original interface definitions can provide a better understanding of ONDEWO APIs and help you to utilize them more efficiently. You can also use these definitions with open source tools to generate client libraries, documentation, and other artifacts.

The core components of all the client libraries are built directly from files in this repo using [the proto compiler.](https://github.com/ondewo/ondewo-proto-compiler)

For an end-user, the APIs in this repo function mostly as documentation for the endpoints. For specific implementations, look in the following repos for working implementations:

* [Python](https://github.com/ondewo/ondewo-survey-client-python)
* [Angular](https://github.com/ondewo/ondewo-survey-client-angular)
* [JavaScript](https://github.com/ondewo/ondewo-survey-client-javascript)
* [TypeScript](https://github.com/ondewo/ondewo-survey-client-typescript)
* [NodeJS](https://github.com/ondewo/ondewo-survey-client-nodejs)
* [C++](https://github.com/ondewo/ondewo-survey-client-cpp)
* [C#](https://github.com/ondewo/ondewo-survey-client-csharp)
* [Go](https://github.com/ondewo/ondewo-survey-client-go)
* [Java](https://github.com/ondewo/ondewo-survey-client-java)
* [PHP](https://github.com/ondewo/ondewo-survey-client-php)
* [Rust](https://github.com/ondewo/ondewo-survey-client-rust)

Please note that some of these implementations are works-in-progress. The repo will make clear the status of the implementation.

## Overview

ONDEWO APIs use [Protocol Buffers](https://github.com/google/protobuf) version 3 (proto3) as their Interface Definition Language (IDL) to define the API interface and the structure of the payload messages. The same interface definition is used for gRPC versions of the API in all languages.

There are several ways of accessing APIs:

1. Protocol Buffers over gRPC: You can access APIs published in this repository through [GRPC](https://github.com/grpc), which is a high-performance binary RPC protocol over HTTP/2. It offers many useful features, including request/response multiplex and full-duplex streaming.

2. ONDEWO Client Libraries:
You can use these libraries to access ONDEWO Cloud APIs. They are based on gRPC for better performance and provide idiomatic client surface for better developer experience.

## Discussions

Please use the issue tracker in this repo for discussions about this API, or the issue tracker in the relevant client if it is language-specific.

## Repository Structure

```
.
├── CONTRIBUTING.md
├── Dockerfile.utils
├── docs
│   ├── index.html
│   ├── index.md
│   └── style.css
├── install_nvm.sh
├── LICENSE
├── Makefile
├── googleapis
├── ondewo
│   └── survey
│       ├── fhir.proto
│       └── survey.proto
├── README.md
└── RELEASE.md
```

## Generate gRPC Source Code

API client libraries can be built directly from files in this repo using [the proto compiler.](https://github.com/ondewo/ondewo-proto-compiler)

## Automatic Release Process

The entire process is automated to make development easier. The actual steps are simple:

TODOs after Pull Request was merged in:

* Checkout master:
    >git checkout master
* Pull the new stuff:
    >git pull
* (If not already, run the `setup_developer_environment_locally` command):
   >make setup_developer_environment_locally
* Update the `ONDEWO_SURVEY_API_VERSION` in the `Makefile`
* Add the new Release Notes in `RELEASE.md` in the format:

   ```
   ## Release ONDEWO Survey Server API X.X.X       <---- Beginning of Notes

      ...<NOTES>...

   *****************                      <---- End of Notes
   ```

* `Commit and push` the changes made in `RELEASE.md` and `Makefile`
* Release:
   >make ondewo_release

---
The `make ondewo_release` command can be divided into 4 steps:

* cloning the devops-accounts repository into a private temporary directory, reading the GitHub token
  into the environment and deleting the clone (`scripts/with_devops_accounts.sh --github-token`)
* creating and pushing the release branch
* creating and pushing the release tag
* creating the GitHub release

The variable for the GitHub Access Token is inside the Makefile, but the value is overwritten during
`make ondewo_release`, because it is passed from the devops-accounts repo in the environment of the actual
`release` command (never on its command line).

## Automatic Release Process - Clients

All eleven `ondewo-survey-client-<language>` SDKs (`CLIENTS` in the Makefile: python nodejs typescript
angular js cpp csharp go java php rust) are released from this repository, after the API itself, by one
driver, `scripts/release_client.sh`:

```bash
make preflight_all_clients                  # read-only: every client's preflight, serially
make release_all_clients                    # preflight_all_clients, then all clients in parallel
make preflight_client CLIENT=python         # one client's preflight (likewise preflight_<language>_client)
make release_client CLIENT=python           # one client (likewise release_<language>_client)
```

What `release_all_clients` does:

1. Clones ondewo-devops-accounts **once** into a private `mktemp -d` directory outside every
   repository (`scripts/with_devops_accounts.sh`) and hands each client its own copy as
   `DEVOPS_ACCOUNT_DIR`; every copy and the clone are deleted on every exit path, Ctrl-C included.
2. Runs `preflight_all_clients`. **A single failing preflight stops the run before any client is
   released.**
3. Releases the clients in parallel, each into a fresh `release_run_<language>.log`, and prints a
   `RELEASED` / `SKIP` / `INCOMPLETE` / `FAILED` summary. One failing client does not abort the others;
   the run fails if any client is not `RELEASED` or `SKIP`.

For every client, in preflight and release alike, the driver clones the client, inserts the generated
release notes into its `RELEASE.md` (`src/RELEASE.md` for nodejs, typescript, angular and js) unless it
already documents the version, and rewrites the anchored `ONDEWO_SURVEY_VERSION=`,
`ONDEWO_PROTO_COMPILER_GIT_BRANCH=tags/<ONDEWO_PROTO_COMPILER_VERSION>` and `(ONDEWO_)SURVEY_API_GIT_BRANCH=`
assignments of its Makefile. The client families spell the product differently in their headings --
`## Release ONDEWO Survey <Name> Client <version>` in python and the js family,
`## Release ONDEWO SURVEY <Name> Client <version>` in cpp, csharp, go, java, php and rust (`<Name>` is the
capitalised language, except `C++` and `PHP`). The generated heading takes the spelling of the client's own
newest entry, and an entry for the version in EITHER spelling counts as "already documented", so a client
never gets a second entry. Then the client's Makefile and what origin already has decide.

A **contract** client has the read-only targets `release_preflight` (credentials valid, version new on
origin and registry) and `release_verify` (tag, GitHub release and registry serve the version):

| On the client's origin | Result |
| --- | --- |
| tag `<version>` and `release_verify` passes | **SKIP**: already released and verified |
| tag `<version>` but `release_verify` fails | **INCOMPLETE**: a half-finished release; finish it by hand |
| branch `release/<version>` but no tag | **INCOMPLETE**: a half-finished release; finish or undo it by hand |
| neither | preflight: `release_preflight`; release: `ondewo_release`, then `release_verify` |

A **legacy** client has neither target -- every survey client today. It is released exactly as before,
through its own `ondewo_release` (which clones the devops accounts itself) followed by `make TEST`, and
the GitHub release `<version>`, which its `ondewo_release` creates last, tells the states apart:

| On the client's origin | Result |
| --- | --- |
| tag or `release/<version>`, GitHub release published (HTTP 200) | **SKIP**: already released |
| tag or `release/<version>`, no GitHub release (HTTP 404) | **INCOMPLETE**: a half-finished release |
| tag or `release/<version>`, any other answer (403/429 rate limit) | **FAILED**: nothing changed, re-run later |
| neither | preflight: the driver's own checks only; release: `ondewo_release`, `TEST`, then the GitHub release must appear |

A client with only one of `release_preflight` / `release_verify` fails with that message. The client
clone is removed on every exit path; files a client container wrote as root are removed through a
digest-pinned busybox container, never `sudo`. The proto compiler is pinned exactly in
`ONDEWO_PROTO_COMPILER_VERSION`; move it deliberately.

The generated notes come from these variables:

* `ONDEWO_SURVEY_API_VERSION` -- Current API version
* `GENERIC_RELEASE_NOTES` -- template text of client release notes
* `GENERIC_RELEASE_SECTION` -- heading the generated notes are filed under (default `Improvements`)
* `GENERIC_RELEASE_EXTRA` -- optional extra bullet appended to the generated notes

`python3 scripts/test_release_driver.py` runs the real Makefile and driver against fake client and devops
repositories (nothing is cloned from or published to anywhere).

## Proto Documentation

The documentation for this, and all other APIs and their available versions, can be found on [ondewo.github.io](https://ondewo.github.io). For Offline usage, it can also be found in the `docs` folder.

As part of the `pre-commit` hooks, `update_githubio` is run. It will preemptively stop if:

* The command is not run on the `master` branch
* There already exists a version-object with the specified version in the `data.js` of the `ondewo.github.io` repository

> :warning:  This command is dependent on your installation of NPM and NodeJS -- Make sure to install both, or run `make setup_developer_environment_locally`
