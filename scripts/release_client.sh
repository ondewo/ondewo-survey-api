#!/usr/bin/env bash
# Prepare, preflight, release and verify ONE ondewo-survey-client-<language> repository.
#
# Called by the Makefile (`preflight_<x>_client`, `release_<x>_client`, `preflight_all_clients`,
# `release_all_clients`), never by hand:
#
#   release_client.sh <preflight|release> <name> <git-url> <release-md> <display-name> \
#                     <api-version> <proto-compiler-version>
#
# RELEASE_NOTES_TEMPLATE (environment) holds GENERIC_RELEASE_NOTES exactly as make stores it (literal
# `\n`, `\#`); it is turned into markdown here, in a private temporary directory. DEVOPS_ACCOUNT_DIR must
# name the driver's ondewo-devops-accounts clone (scripts/with_devops_accounts.sh provides it).
#
# The state of the client on origin decides what happens, and a half-finished release is never a SKIP.
# Two kinds of client exist, told apart by their Makefile:
#
# CONTRACT client (has `release_preflight` AND `release_verify`):
#
#   tag <version> on origin  AND  `make release_verify` passes  -> SKIP (already released and verified)
#   tag on origin, release_verify FAILS                          -> INCOMPLETE (half-finished)
#   release/<version> branch on origin, but no tag               -> INCOMPLETE (half-finished)
#   neither                                                      -> preflight: `make release_preflight`
#                                                                   release:   `make ondewo_release`, then
#                                                                              `make release_verify`
#
# LEGACY client (has neither; every ondewo-survey-client-<language> today). Its own `ondewo_release` clones
# the devops accounts, builds, publishes to its registry and creates its GitHub release as the LAST step,
# so the published GitHub release <version> is what tells a finished release from a half-finished one:
#
#   tag or release/<version> branch on origin, GitHub release <version> published (HTTP 200) -> SKIP
#   tag or branch on origin, GitHub answers 404                                                -> INCOMPLETE
#   tag or branch on origin, any other answer (403/429 rate limit, 000 no connection)         -> FAILED
#   neither  -> preflight: only this driver's checks (clone, notes, Makefile pins, origin state)
#               release:   `make ondewo_release`, `make TEST` (diagnostics), then the GitHub release
#                          <version> must be published, or the client is FAILED
#
# A client with only ONE of the two contract targets FAILS with that message: half a contract proves
# nothing. INCOMPLETE leaves .incomplete_marker-<name>, SKIP in release mode .already_released_marker-<name>;
# the Makefile turns them into the summary. The GitHub API is asked unauthenticated (60 calls/hour) at
# GITHUB_API_URL (default https://api.github.com), once per legacy client whose version exists on origin,
# with the caller's GH_TOKEN / GITHUB_TOKEN when one is set (see github_release_http_code).
#
# Every exit path removes the client clone and this client's private temporary directory (the notes and
# its copy of the devops clone) (EXIT trap; INT/TERM/HUP become an exit so the trap runs for them too). No sudo: files a client
# container wrote as root are removed through a throwaway container that mounts only the clone.
set -euo pipefail
# 077 is for what THIS script writes (the notes, the private devops copy, the build log). The client clone
# and the client make run under CLIENT_UMASK instead (clone_client / run_client_target): a client builds
# docker images from its checkout and runs them with `--user $(id -u)`, and COPY keeps file modes, so a
# 0600 checkout made e.g. compile-proto-2-php.sh unreadable in the php proto-compiler image (5.5.2: `bash:
# compile-proto-2-php.sh: Permission denied`). The clone holds only public sources.
umask 077
CLIENT_UMASK=022

[ "$#" -eq 7 ] || { echo "usage: $0 <preflight|release> <name> <git-url> <release-md> <display-name> <api-version> <proto-compiler-version>" >&2; exit 2; }
mode="$1" name="$2" url="$3" release_md="$4" display_name="$5" version="$6" compiler_version="$7"

repo_dir="ondewo-survey-client-${name}"
build_log="build_log_${name}.txt"
skip_marker=".already_released_marker-${name}"
incomplete_marker=".incomplete_marker-${name}"
github_api_url="${GITHUB_API_URL:-https://api.github.com}"
# How often, and how far apart, a legacy release is asked for its GitHub release after ondewo_release.
legacy_verify_attempts="${LEGACY_VERIFY_ATTEMPTS:-6}"
legacy_verify_sleep_s="${LEGACY_VERIFY_SLEEP_S:-10}"
# Removes files a client container left behind as root; pinned by digest, mounts only the clone.
cleanup_image="busybox:1.37.0@sha256:bdf57e528e45e4433820e045b29b4597825a1c9e38353532d90a01445013f82e"
private_root=""

say() { printf 'release_client[%s]: %s\n' "${name}" "$*"; }
fail() { say "FAILED: $*" >&2; exit 1; }
incomplete() { touch "${incomplete_marker}"; say "INCOMPLETE: $*" >&2; exit 1; }

remove_clone() {
    [ -e "${repo_dir}" ] || return 0
    rm -rf "${repo_dir}" 2>/dev/null && return 0
    say "plain rm could not remove ${repo_dir} (files written as root by a container); removing them through ${cleanup_image}"
    docker run --rm -v "${PWD}/${repo_dir}:/clone" "${cleanup_image}" \
        sh -c 'rm -rf /clone/..?* /clone/.[!.]* /clone/*' && rm -rf "${repo_dir}"
}

cleanup() {
    local status=$?
    remove_clone || { say "could not remove ${repo_dir}" >&2; status=1; }
    [ -z "${private_root}" ] || rm -rf "${private_root}"
    exit "${status}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

case "${mode}" in preflight | release) ;; *) fail "unknown mode '${mode}'" ;; esac
semver='^[0-9]+\.[0-9]+\.[0-9]+$'
[[ "${version}" =~ ${semver} ]] || fail "API version '${version}' is not MAJOR.MINOR.PATCH"
[[ "${compiler_version}" =~ ${semver} ]] || fail "ONDEWO_PROTO_COMPILER_VERSION '${compiler_version}' is not MAJOR.MINOR.PATCH"
if [ -z "${DEVOPS_ACCOUNT_DIR:-}" ] || [ ! -d "${DEVOPS_ACCOUNT_DIR}" ]; then
    fail "DEVOPS_ACCOUNT_DIR is not a directory; run this through the Makefile targets, which provide it"
fi
[ -n "${RELEASE_NOTES_TEMPLATE:-}" ] || fail "RELEASE_NOTES_TEMPLATE is empty; run this through the Makefile targets, which provide it"
rm -f "${skip_marker}" "${incomplete_marker}"
remove_clone

# Absolute (the client runs as `make -C <client>`, where a relative path would not resolve).
private_root="$(cd "$(mktemp -d)" && pwd -P)"
notes="${private_root}/release-notes.md"
printf '%s' "${RELEASE_NOTES_TEMPLATE}" > "${notes}"

# Exit 0: the ref exists on origin; 1: it does not; anything else is an error and fails closed.
# `git ls-remote --exit-code` matches whole trailing ref components, so refs/tags/5.5.1 is not found by
# refs/tags/15.5.1 nor by refs/tags/5.5.10 (and the dots are not regex wildcards).
origin_has_ref() {
    local rc=0
    git ls-remote --exit-code "${url}" "$1" >/dev/null || rc=$?
    case "${rc}" in
        0) return 0 ;;
        2) return 1 ;;
        *) fail "cannot read ${url} (git ls-remote exit ${rc})" ;;
    esac
}

# Nothing of this driver's make reaches a client: make hands every command-line variable (CLIENT=...,
# ONDEWO_SURVEY_API_VERSION=..., ...) to its children BOTH in MAKEFLAGS and as an environment variable, and
# a client Makefile that reads one with `?=` would silently take the driver's value. So the client make
# starts without MAKEFLAGS and without each variable named in it.
# The caller's own GitHub credentials do not reach a client either: a legacy client logs gh in with the
# devops token (`gh auth login --with-token`), and gh refuses that while GH_TOKEN is set ("The value of the
# GH_TOKEN environment variable is being used for authentication"), which stranded ondewo-s2t-client-rust
# 7.6.0 between its pushed tag and its GitHub release. Without them, the same login would have rewritten the
# caller's gh configuration, so the client also gets a private GH_CONFIG_DIR (see run_client_target).
caller_github_token="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
driver_variables=(MAKEFLAGS MFLAGS MAKELEVEL MAKEOVERRIDES RELEASE_NOTES_TEMPLATE
    GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN GH_HOST GH_CONFIG_DIR)
if [[ "${MAKEFLAGS:-}" == *"-- "* ]]; then
    while read -r variable; do
        driver_variables+=("${variable}")
    done < <(printf '%s\n' "${MAKEFLAGS#*-- }" | grep -oE '(^| )[A-Za-z_][A-Za-z0-9_]*:?=' | tr -d ' :=')
fi
unset_driver_variables=()
for variable in "${driver_variables[@]}"; do unset_driver_variables+=(-u "${variable}"); done

# Runs a client target with a private copy of the devops clone, so a client that deletes "its" clone
# cannot pull it from under a client releasing in parallel, and with a private gh configuration
# directory, so the token a client's `gh auth login` stores is removed with private_root on exit.
run_client_target() {
    local devops_copy="${private_root}/ondewo-devops-accounts"
    local gh_config="${private_root}/gh-config"
    rm -rf "${devops_copy}"
    cp -R "${DEVOPS_ACCOUNT_DIR}" "${devops_copy}"
    mkdir -p "${gh_config}"
    (umask "${CLIENT_UMASK}" && exec env "${unset_driver_variables[@]}" DEVOPS_ACCOUNT_DIR="${devops_copy}" \
        GH_CONFIG_DIR="${gh_config}" make -C "${repo_dir}" "$1")
}

client_has_target() {
    grep -Eq "^$1[[:space:]]*:([^=]|\$)" "${repo_dir}/Makefile"
}

# ---------------------------------------------------------------- clone and prepare
say "${mode} ${display_name} client ${version} (proto compiler ${compiler_version}) from ${url}"
(umask "${CLIENT_UMASK}" && exec git clone --quiet "${url}" "${repo_dir}")

client_has_target ondewo_release || fail "client ${name} lacks ondewo_release"
if client_has_target release_preflight && client_has_target release_verify; then
    contract=yes
elif client_has_target release_preflight || client_has_target release_verify; then
    fail "client ${name} has only one of release_preflight / release_verify: provide both (the release contract) or neither (legacy)"
else
    contract=no
    say "legacy client: no release_preflight / release_verify, so the published GitHub release ${version} tells a finished release from a half-finished one"
fi

# How this client's RELEASE.md spells the product in its headings. The two client families disagree: the
# python and js-family clients write "Release ONDEWO Survey <Name> Client", the cpp / csharp / go / java /
# php / rust clients "Release ONDEWO SURVEY <Name> Client". The spelling of the newest existing heading
# wins, so a generated entry matches the entries around it; a RELEASE.md with no entry yet gets "Survey".
product_name="$(perl -ne 'if (/^#+ Release ONDEWO (Survey|SURVEY) /) { print $1; exit }' "${repo_dir}/${release_md}")"
product_name="${product_name:-Survey}"

# GENERIC_RELEASE_NOTES -> markdown: `\n` is a newline, every other backslash goes, exactly ONE final newline.
DISPLAY_NAME="${display_name}" PRODUCT_NAME="${product_name}" perl -0777 -i -pe \
    's/\\n/\n/g; s/\\//g; s/PRODUCTNAME/$ENV{PRODUCT_NAME}/g; s/REPONAME/$ENV{DISPLAY_NAME}/g; s/\n*\z/\n/' "${notes}"

# Insert the generated notes only when the client does not document this version yet: a second heading
# would bury a curated entry and trips markdownlint MD024, which does not auto-fix. Anchored and quoted:
# a `5.5.10` heading does not count as `5.5.1`. EITHER product spelling counts, so a client whose entry was
# written as "ONDEWO SURVEY" never gets a second "ONDEWO Survey" entry for the same version (and vice versa).
if DISPLAY_NAME="${display_name}" VERSION="${version}" perl -ne \
    'if (/^#+ Release ONDEWO (?:Survey|SURVEY) \Q$ENV{DISPLAY_NAME}\E Client \Q$ENV{VERSION}\E$/) { $found = 1; last } END { exit($found ? 0 : 1) }' \
    "${repo_dir}/${release_md}"; then
    say "${release_md} already documents ${version} - keeping the curated entry"
else
    NOTES="${notes}" perl -i -ne 'BEGIN { open my $f, "<", $ENV{NOTES} or die "$ENV{NOTES}: $!"; @notes = <$f>; close $f }
        print; if (!$done && /^#+ Release History\s*$/) { print @notes; $done = 1 } END { exit($done ? 0 : 1) }' \
        "${repo_dir}/${release_md}" || fail "${release_md} has no '# Release History' heading to insert the notes under"
fi

# Anchored on the ASSIGNMENT at the start of a line; unanchored, the rewrite also hit lines that merely
# mention the variable (it cut quotes off echo lines in the go client and truncated a comment in csharp).
makefile="${repo_dir}/Makefile"
perl -i -pe "s/^ONDEWO_SURVEY_VERSION\\s*=.*/ONDEWO_SURVEY_VERSION=${version}/" "${makefile}"
perl -i -pe "s{^ONDEWO_PROTO_COMPILER_GIT_BRANCH\\s*=.*}{ONDEWO_PROTO_COMPILER_GIT_BRANCH=tags/${compiler_version}}" "${makefile}"
perl -i -pe "s{^((?:ONDEWO_)?SURVEY_API_GIT_BRANCH)\\s*=.*}{\$1=tags/${version}}" "${makefile}"
grep -qxF "ONDEWO_SURVEY_VERSION=${version}" "${makefile}" || fail "Makefile has no ONDEWO_SURVEY_VERSION= assignment"
grep -qxF "ONDEWO_PROTO_COMPILER_GIT_BRANCH=tags/${compiler_version}" "${makefile}" \
    || fail "Makefile has no ONDEWO_PROTO_COMPILER_GIT_BRANCH= assignment"
grep -qxE "(ONDEWO_)?SURVEY_API_GIT_BRANCH=tags/${version//./\\.}" "${makefile}" \
    || fail "Makefile has no (ONDEWO_)SURVEY_API_GIT_BRANCH= assignment"

# The HTTP code of GET <api>/repos/ondewo/<client>/releases/tags/<version>: 200 published, 404 not.
# The REST API, not the github.com page, which answers 200 for a bare tag without any release.
# Authenticated with the caller's GH_TOKEN / GITHUB_TOKEN when one is set: the unauthenticated quota is 60
# calls an hour PER ADDRESS, shared with every other release running on the host, and ondewo-s2t-client-php
# 7.6.0 was published completely and still reported FAILED on six HTTP 403s. The token reaches curl as a
# config read from stdin (`-K -`), never on its command line, which /proc/<pid>/cmdline shows to every user.
github_release_http_code() {
    local endpoint="${github_api_url}/repos/ondewo/${repo_dir}/releases/tags/${version}"
    if [ -n "${caller_github_token}" ]; then
        printf 'header = "Authorization: Bearer %s"\n' "${caller_github_token}" \
            | curl -s -K - -o /dev/null -w '%{http_code}' -L "${endpoint}" || true
    else
        curl -s -o /dev/null -w '%{http_code}' -L "${endpoint}" || true
    fi
}

# ---------------------------------------------------------------- what origin already has
if [ "${contract}" = no ]; then
    if origin_has_ref "refs/tags/${version}" || origin_has_ref "refs/heads/release/${version}"; then
        code="$(github_release_http_code)"
        case "${code}" in
            200)
                say "SKIP: ${version} is already released (tag or release branch on origin, GitHub release ${version} published)"
                [ "${mode}" = release ] && touch "${skip_marker}"
                exit 0 ;;
            404) incomplete "${version} has a tag or release branch on origin but no published GitHub release: a HALF-FINISHED release. Finish or undo it by hand in the client, then re-run" ;;
            *) fail "${version} has a tag or release branch on origin, and the GitHub API did not say whether release ${version} is published (HTTP ${code}; 403/429 = rate limit, 000 = no connection). Nothing was changed - re-run later" ;;
        esac
    fi
    if [ "${mode}" = preflight ]; then
        say "PREFLIGHT OK (legacy client: only this driver's checks ran - clone, notes, Makefile pins, ${version} new on origin)"
        exit 0
    fi
    rm -f "${build_log}"
    run_client_target ondewo_release 2>&1 | tee "${build_log}" || fail "ondewo_release failed (see ${build_log})"
    run_client_target TEST || say "WARNING: make TEST failed (diagnostics only; the release itself finished)"
    for attempt in $(seq 1 "${legacy_verify_attempts}"); do
        code="$(github_release_http_code)"
        if [ "${code}" = 200 ]; then
            say "RELEASED ${version} (GitHub release ${version} is published)"
            exit 0
        fi
        say "GitHub release ${version} not visible yet (HTTP ${code}, attempt ${attempt}/${legacy_verify_attempts})"
        [ "${attempt}" -lt "${legacy_verify_attempts}" ] && sleep "${legacy_verify_sleep_s}"
    done
    fail "ondewo_release finished but GitHub has no published release ${version} (last HTTP ${code})"
fi

if origin_has_ref "refs/tags/${version}"; then
    say "tag ${version} exists on origin - running release_verify to tell a finished release from a half-finished one"
    if run_client_target release_verify; then
        say "SKIP: ${version} is already released and release_verify passes"
        [ "${mode}" = release ] && touch "${skip_marker}"
        exit 0
    fi
    incomplete "tag ${version} exists on origin but release_verify fails: a HALF-FINISHED release. Finish it by hand (the client README names the remaining steps); a re-run reports it as already released once release_verify passes"
fi
if origin_has_ref "refs/heads/release/${version}"; then
    incomplete "branch release/${version} exists on origin but tag ${version} does not: a HALF-FINISHED release. Finish or undo it by hand, then re-run"
fi

# ---------------------------------------------------------------- preflight / release
if [ "${mode}" = preflight ]; then
    run_client_target release_preflight || fail "release_preflight failed"
    say "PREFLIGHT OK"
    exit 0
fi

rm -f "${build_log}"
run_client_target ondewo_release 2>&1 | tee "${build_log}" || fail "ondewo_release failed (see ${build_log})"
run_client_target release_verify || fail "ondewo_release finished but release_verify fails"
say "RELEASED ${version}"
