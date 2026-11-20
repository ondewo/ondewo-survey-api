#!/usr/bin/env python3
"""
Tests for the client-release driver: release_client, preflight_all_clients and release_all_clients.

The behavioural tests run the REAL Makefile and scripts against fake client repositories (local bare
repositories whose Makefile stubs release_preflight / ondewo_release / release_verify) and a fake
ondewo-devops-accounts repository, so nothing is cloned from or published to anywhere. They pin:

- a contract client is SKIP only when its tag exists AND its release_verify passes; a release branch
  without a tag, or a tag whose release_verify fails, is INCOMPLETE - never SKIP;
- a LEGACY client (no release_preflight / release_verify, every survey client today) is released through its
  own ondewo_release and TEST as before; the published GitHub release decides SKIP (200), INCOMPLETE (404)
  or FAILED (anything else), and a release whose GitHub release never appears is FAILED;
- every client's preflight runs before ANY client releases, and one failing preflight stops all;
- a client with only one of release_preflight / release_verify fails with that message;
- every exit path removes the client clone, the notes file and every devops-accounts clone;
- the proto compiler is the pinned ONDEWO_PROTO_COMPILER_VERSION, and version matches are anchored;
- the generated heading spells the product as the client's own RELEASE.md does ("ONDEWO Survey" in python
  and the js family, "ONDEWO SURVEY" in cpp/csharp/go/java/php/rust), and an entry for the version in
  EITHER spelling is kept instead of getting a second one.

The static tests pin the Makefile and the release-hygiene workflow.

Usage: python3 scripts/test_release_driver.py [-v]   (needs git, make and perl; stdlib only)
"""

import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
MAKEFILE: str = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
VERSION: str = "7.7.1"

FAKE_CLIENT_MAKEFILE: str = """\
ONDEWO_SURVEY_VERSION=7.5.0
ONDEWO_PROTO_COMPILER_GIT_BRANCH=tags/5.16.0
{api_branch_variable}=tags/7.5.0
# Mentions ONDEWO_SURVEY_VERSION= in a recipe; the anchored rewrite must leave this line alone.
CONTROL=$(FAKE_CLIENT_CONTROL_DIR)/{name}
LOG=$(FAKE_CLIENT_CONTROL_DIR)/{name}.log

release_preflight:
\t@echo "preflight ONDEWO_SURVEY_VERSION=$(ONDEWO_SURVEY_VERSION)" >> $(LOG)
\t@test -f "$$DEVOPS_ACCOUNT_DIR/account_github.env"
\t@! grep -qx fail_preflight $(CONTROL) 2>/dev/null

ondewo_release:
\t@echo "release ONDEWO_SURVEY_VERSION=$(ONDEWO_SURVEY_VERSION)" >> $(LOG)
\t@env > $(FAKE_CLIENT_CONTROL_DIR)/{name}.env
\t@echo "$$(umask) $$(stat -c %a Makefile)" > $(FAKE_CLIENT_CONTROL_DIR)/{name}.modes
\t@test -f "$$DEVOPS_ACCOUNT_DIR/account_github.env"
\t@cp Makefile $(FAKE_CLIENT_CONTROL_DIR)/{name}.Makefile
\t@cp {release_md} $(FAKE_CLIENT_CONTROL_DIR)/{name}.RELEASE.md
\t@git add -A && git commit -q -m "release $(ONDEWO_SURVEY_VERSION)"
\t@git push -q origin HEAD:refs/heads/release/$(ONDEWO_SURVEY_VERSION)
\t@! grep -qx fail_after_branch $(CONTROL) 2>/dev/null
\t@if grep -qx hang $(CONTROL) 2>/dev/null; then touch $(FAKE_CLIENT_CONTROL_DIR)/{name}.hanging; sleep 60; fi
\t@git tag -a $(ONDEWO_SURVEY_VERSION) -m "release/$(ONDEWO_SURVEY_VERSION)" && git push -q origin $(ONDEWO_SURVEY_VERSION)

release_verify:
\t@echo "verify" >> $(LOG)
\t@git ls-remote --exit-code origin refs/tags/$(ONDEWO_SURVEY_VERSION) > /dev/null
\t@! grep -qx fail_verify $(CONTROL) 2>/dev/null
"""

# A legacy client as every ondewo-survey-client-<language> is today: its own ondewo_release clones the devops
# accounts into ./ondewo-devops-accounts (DEVOPS_ACCOUNT_DIR is assigned with `=`, so the driver's value is
# ignored), pushes the release branch and the tag, and creates the GitHub release LAST - simulated by writing
# the HTTP code the fake curl answers for this repository.
LEGACY_CLIENT_MAKEFILE: str = """\
ONDEWO_SURVEY_VERSION=7.5.0
ONDEWO_PROTO_COMPILER_GIT_BRANCH=tags/5.16.0
{api_branch_variable}=tags/7.5.0
CONTROL=$(FAKE_CLIENT_CONTROL_DIR)/{name}
LOG=$(FAKE_CLIENT_CONTROL_DIR)/{name}.log
DEVOPS_ACCOUNT_DIR="./ondewo-devops-accounts"

ondewo_release:
\t@echo "release ONDEWO_SURVEY_VERSION=$(ONDEWO_SURVEY_VERSION)" >> $(LOG)
\t@cp Makefile $(FAKE_CLIENT_CONTROL_DIR)/{name}.Makefile
\t@cp {release_md} $(FAKE_CLIENT_CONTROL_DIR)/{name}.RELEASE.md
\t@git add -A && git commit -q -m "release $(ONDEWO_SURVEY_VERSION)"
\t@git push -q origin HEAD:refs/heads/release/$(ONDEWO_SURVEY_VERSION)
\t@! grep -qx fail_after_branch $(CONTROL) 2>/dev/null
\t@git tag -a $(ONDEWO_SURVEY_VERSION) -m "release/$(ONDEWO_SURVEY_VERSION)" && git push -q origin $(ONDEWO_SURVEY_VERSION)
\t@grep -qx no_github_release $(CONTROL) 2>/dev/null || echo 200 > $(FAKE_CLIENT_CONTROL_DIR)/ondewo-survey-client-{name}.github

TEST:
\t@echo "TEST" >> $(LOG)

release_preflight_only_half_a_contract_when_renamed:
\t@true
"""

# Answers the driver's GitHub API question from control/<repository>.github (default 404), and records it.
FAKE_CURL: str = """\
#!/usr/bin/env bash
url="${@: -1}"
repository="$(printf '%s' "${url}" | sed -E 's#.*/repos/ondewo/([^/]+)/releases/tags/.*#\\1#')"
echo "${url}" >> "${FAKE_CLIENT_CONTROL_DIR}/curl.log"
echo "$*" >> "${FAKE_CLIENT_CONTROL_DIR}/curl.argv"
case " $* " in *" -K - "*) cat >> "${FAKE_CLIENT_CONTROL_DIR}/curl.stdin" ;; esac
cat "${FAKE_CLIENT_CONTROL_DIR}/${repository}.github" 2>/dev/null || printf 404
"""

# How each client family spells the product in its RELEASE.md headings, as the real clients do.
UPPERCASE_PRODUCT_CLIENTS: List[str] = ["cpp", "csharp", "go", "java", "php", "rust"]


def product_spelling(name: str) -> str:
    """
    Return how the RELEASE.md headings of the real ondewo-survey-client-<name> spell the product.

    Args:
        name (str):
            Client name as in CLIENTS.

    Returns:
        str:
            "SURVEY" for cpp/csharp/go/java/php/rust, "Survey" for python and the js family.
    """
    return "SURVEY" if name in UPPERCASE_PRODUCT_CLIENTS else "Survey"


RELEASE_MD: str = """\
# Release History

*****************

## Release ONDEWO {product} {display} Client 7.7.10

### Improvements

* a later patch mentioned only to prove the heading match is anchored

*****************
"""


def generated_notes(display: str, version: str, product: str) -> str:
    """
    Return the release notes the driver generates for a client.

    Args:
        display (str):
            The language as the client's RELEASE.md headings spell it.
        version (str):
            The API version.
        product (str):
            The product as the client's RELEASE.md headings spell it ("Survey" or "SURVEY").

    Returns:
        str:
            The generated block, byte for byte.
    """
    return (
        f"\n*****************\n\n## Release ONDEWO {product} {display} Client {version}\n\n### Improvements\n\n"
        f"* Tracking API Version [{version}](https://github.com/ondewo/ondewo-survey-api/releases/tag/{version}) "
        "( [Documentation](https://ondewo.github.io/ondewo-survey-api/) )\n"
    )


class DriverFixture(unittest.TestCase):
    """A scratch driver checkout, fake clients, a fake devops repository and a private TMPDIR."""

    def setUp(self) -> None:
        self.root: Path = Path(tempfile.mkdtemp(prefix="release-driver-test-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.driver: Path = self.root / "driver"
        self.origins: Path = self.root / "origins"
        self.control: Path = self.root / "control"
        self.tmpdir: Path = self.root / "tmp"
        for directory in (self.driver, self.origins, self.control, self.tmpdir):
            directory.mkdir()
        shutil.copy(REPO_ROOT / "Makefile", self.driver / "Makefile")
        shutil.copytree(REPO_ROOT / "scripts", self.driver / "scripts")
        gitconfig: Path = self.root / "gitconfig"
        gitconfig.write_text(
            "[user]\n\tname = Release Driver Test\n\temail = test@example.invalid\n"
            "[init]\n\tdefaultBranch = master\n[advice]\n\tdetachedHead = false\n",
            encoding="utf-8",
        )
        fake_bin: Path = self.root / "bin"
        fake_bin.mkdir()
        (fake_bin / "curl").write_text(FAKE_CURL, encoding="utf-8")
        (fake_bin / "curl").chmod(0o755)
        self.env: Dict[str, str] = {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "GITHUB_API_URL": "https://api.github.invalid",
            "LEGACY_VERIFY_ATTEMPTS": "2",
            "LEGACY_VERIFY_SLEEP_S": "0",
            "HOME": str(self.root),
            "TMPDIR": str(self.tmpdir),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "FAKE_CLIENT_CONTROL_DIR": str(self.control),
        }
        self.make_bare_repository("ondewo-devops-accounts", {"account_github.env": "GITHUB_GH_TOKEN=fake-token\n"})

    def git(self, *args: str, cwd: Optional[Path] = None) -> str:
        """
        Run git in the fixture environment.

        Args:
            *args (str):
                git arguments.
            cwd (Optional[Path]):
                Working directory.

        Returns:
            str:
                stdout.
        """
        return subprocess.run(
            ["git", *args], cwd=cwd, env=self.env, check=True, capture_output=True, text=True
        ).stdout

    def make_bare_repository(self, name: str, files: Dict[str, str]) -> Path:
        """
        Create origins/<name>.git holding one commit on master with the given files.

        Args:
            name (str):
                Repository name.
            files (Dict[str, str]):
                Relative path -> content.

        Returns:
            Path:
                The bare repository.
        """
        work: Path = self.root / "work" / name
        work.mkdir(parents=True)
        for relative, content in files.items():
            (work / relative).parent.mkdir(parents=True, exist_ok=True)
            (work / relative).write_text(content, encoding="utf-8")
        self.git("init", "-q", cwd=work)
        self.git("add", "-A", cwd=work)
        self.git("commit", "-q", "-m", "initial", cwd=work)
        bare: Path = self.origins / f"{name}.git"
        self.git("clone", "-q", "--bare", str(work), str(bare))
        return bare

    def make_client(self, name: str, display: str, release_md: str = "RELEASE.md", contract: bool = True) -> Path:
        """
        Create a fake ondewo-survey-client-<name> origin.

        Args:
            name (str):
                Client name as in CLIENTS.
            display (str):
                Spelling of the language in its RELEASE.md headings.
            release_md (str):
                Where the client keeps its RELEASE.md.
            contract (bool):
                False makes a legacy client: no release_preflight and no release_verify.

        Returns:
            Path:
                The bare repository.
        """
        api_branch_variable: str = "SURVEY_API_GIT_BRANCH" if release_md.startswith("src/") else "ONDEWO_SURVEY_API_GIT_BRANCH"
        template: str = FAKE_CLIENT_MAKEFILE if contract else LEGACY_CLIENT_MAKEFILE
        makefile: str = template.format(name=name, release_md=release_md, api_branch_variable=api_branch_variable)
        return self.make_bare_repository(
            f"ondewo-survey-client-{name}", {"Makefile": makefile, release_md: RELEASE_MD.format(display=display, product=product_spelling(name))}
        )

    def github_answers(self, name: str, code: str) -> None:
        """
        Make the fake GitHub API answer `code` for the release of ondewo-survey-client-<name>.

        Args:
            name (str):
                Client name.
            code (str):
                HTTP code, e.g. 200, 404 or 403.
        """
        (self.control / f"ondewo-survey-client-{name}.github").write_text(code, encoding="utf-8")

    def push_release_refs(self, name: str, tag: bool = True) -> None:
        """
        Put release/<VERSION> (and the tag) on a fake client's origin, as an earlier release run would.

        Args:
            name (str):
                Client name.
            tag (bool):
                Also create the tag.
        """
        origin: Path = self.origins / f"ondewo-survey-client-{name}.git"
        head: str = self.git("rev-parse", "HEAD", cwd=origin).strip()
        self.git("update-ref", f"refs/heads/release/{VERSION}", head, cwd=origin)
        if tag:
            self.git("update-ref", f"refs/tags/{VERSION}", head, cwd=origin)

    def control_file(self, name: str, *words: str) -> None:
        """
        Make the fake client <name> fail where the words say (fail_preflight, fail_after_branch, fail_verify).

        Args:
            name (str):
                Client name.
            *words (str):
                Failure switches; none clears them.
        """
        (self.control / name).write_text("".join(f"{word}\n" for word in words), encoding="utf-8")

    def run_make(self, *targets: str, clients: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Run the driver Makefile against the fakes.

        Args:
            *targets (str):
                make targets.
            clients (Optional[str]):
                A CLIENTS override; None keeps the Makefile's list.

        Returns:
            subprocess.CompletedProcess:
                The finished make, output in stdout.
        """
        return subprocess.run(
            [
                "make",
                "--no-print-directory",
                *targets,
                f"ONDEWO_SURVEY_API_VERSION={VERSION}",
                *([f"CLIENTS={clients}"] if clients else []),
                f"CLIENT_GIT_URL_PREFIX=file://{self.origins}/ondewo-survey-client-",
                f"DEVOPS_ACCOUNT_GIT_URL=file://{self.origins}/ondewo-devops-accounts.git",
            ],
            cwd=self.driver,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300,
        )

    def origin_refs(self, name: str) -> List[str]:
        """
        Return the ref names of a fake client's origin.

        Args:
            name (str):
                Client name.

        Returns:
            List[str]:
                Ref names.
        """
        output: str = self.git("ls-remote", str(self.origins / f"ondewo-survey-client-{name}.git"))
        return [line.split("\t")[1] for line in output.splitlines()]

    def assert_everything_cleaned_up(self, result: subprocess.CompletedProcess) -> None:
        """
        Assert no client clone, notes file, status file or devops clone survived the run.

        Args:
            result (subprocess.CompletedProcess):
                The run, for the failure message.
        """
        leftovers: List[str] = [
            path.name
            for path in self.driver.iterdir()
            if re.match(
                r"ondewo-survey-client-|temp-notes-|\.already_released_marker-|\.incomplete_marker-|\.client_status-|ondewo-devops",
                path.name,
            )
        ]
        self.assertEqual(leftovers, [], result.stdout)
        self.assertEqual(sorted(path.name for path in self.tmpdir.iterdir()), [], f"devops clone left in TMPDIR\n{result.stdout}")


class TestReleaseClient(DriverFixture):
    """release_client: release, SKIP, FAILED and cleanup."""

    def test_a_new_release_is_released_verified_and_cleaned_up(self) -> None:
        self.make_client("python", "Python")
        result = self.run_make("release_python_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"RELEASED {VERSION}", result.stdout)
        self.assertIn(f"refs/tags/{VERSION}", self.origin_refs("python"))
        log: str = (self.control / "python.log").read_text(encoding="utf-8")
        self.assertEqual(log.split("\n")[:2], [f"release ONDEWO_SURVEY_VERSION={VERSION}", "verify"], log)
        self.assert_everything_cleaned_up(result)

    def test_the_client_makefile_is_prepared_with_anchored_rewrites_and_the_pinned_compiler(self) -> None:
        self.make_client("nodejs", "Nodejs", release_md="src/RELEASE.md")
        result = self.run_make("release_nodejs_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        makefile: str = (self.control / "nodejs.Makefile").read_text(encoding="utf-8")
        compiler: str = re.search(r"^ONDEWO_PROTO_COMPILER_VERSION=(\S+)$", MAKEFILE, re.M).group(1)  # type: ignore[union-attr]
        self.assertIn(f"\nONDEWO_PROTO_COMPILER_GIT_BRANCH=tags/{compiler}\n", makefile)
        self.assertIn(f"ONDEWO_SURVEY_VERSION={VERSION}\n", makefile)
        self.assertIn(f"\nSURVEY_API_GIT_BRANCH=tags/{VERSION}\n", makefile)
        self.assertIn("# Mentions ONDEWO_SURVEY_VERSION= in a recipe;", makefile)

    def test_generated_notes_are_inserted_once_and_a_5_5_10_heading_does_not_count_as_5_5_1(self) -> None:
        self.make_client("cpp", "C++")
        result = self.run_make("release_cpp_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        release_md: str = (self.control / "cpp.RELEASE.md").read_text(encoding="utf-8")
        self.assertTrue(release_md.startswith("# Release History\n" + generated_notes("C++", VERSION, "SURVEY")), release_md)
        self.assertEqual(release_md.count(f"Client {VERSION}\n"), 1)

    def test_a_curated_entry_for_the_version_is_kept(self) -> None:
        curated: str = f"# Release History\n\n*****************\n\n## Release ONDEWO SURVEY Go Client {VERSION}\n\n* curated\n"
        self.make_bare_repository(
            "ondewo-survey-client-go",
            {"Makefile": FAKE_CLIENT_MAKEFILE.format(name="go", release_md="RELEASE.md", api_branch_variable="ONDEWO_SURVEY_API_GIT_BRANCH"), "RELEASE.md": curated},
        )
        result = self.run_make("release_go_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((self.control / "go.RELEASE.md").read_text(encoding="utf-8"), curated)

    def test_python_and_the_js_family_get_the_mixed_case_product_spelling(self) -> None:
        self.make_client("python", "Python")
        self.make_client("js", "Js", release_md="src/RELEASE.md")
        for name, display in (("python", "Python"), ("js", "Js")):
            result = self.run_make(f"release_{name}_client")
            self.assertEqual(result.returncode, 0, result.stdout)
            release_md: str = (self.control / f"{name}.RELEASE.md").read_text(encoding="utf-8")
            self.assertTrue(
                release_md.startswith("# Release History\n" + generated_notes(display, VERSION, "Survey")), release_md
            )

    def test_an_entry_in_either_product_spelling_is_kept_and_never_duplicated(self) -> None:
        # The release this guard exists for: an "ONDEWO SURVEY" client documented by hand as "ONDEWO Survey"
        # (or the other way round) must not get a second entry for the same version.
        cases: List[List[str]] = [["go", "Go", "Survey"], ["python", "Python", "SURVEY"]]
        for name, display, spelling in cases:
            curated: str = (
                f"# Release History\n\n*****************\n\n## Release ONDEWO {spelling} {display} Client {VERSION}\n\n"
                "* curated\n"
            )
            api_branch_variable: str = "ONDEWO_SURVEY_API_GIT_BRANCH"
            self.make_bare_repository(
                f"ondewo-survey-client-{name}",
                {
                    "Makefile": FAKE_CLIENT_MAKEFILE.format(
                        name=name, release_md="RELEASE.md", api_branch_variable=api_branch_variable
                    ),
                    "RELEASE.md": curated,
                },
            )
            result = self.run_make(f"release_{name}_client")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn(f"RELEASE.md already documents {VERSION} - keeping the curated entry", result.stdout)
            self.assertEqual((self.control / f"{name}.RELEASE.md").read_text(encoding="utf-8"), curated)

    def test_a_release_md_without_any_entry_gets_the_mixed_case_spelling(self) -> None:
        self.make_bare_repository(
            "ondewo-survey-client-rust",
            {
                "Makefile": FAKE_CLIENT_MAKEFILE.format(
                    name="rust", release_md="RELEASE.md", api_branch_variable="ONDEWO_SURVEY_API_GIT_BRANCH"
                ),
                "RELEASE.md": "# Release History\n",
            },
        )
        result = self.run_make("release_rust_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        release_md: str = (self.control / "rust.RELEASE.md").read_text(encoding="utf-8")
        self.assertEqual(release_md, "# Release History\n" + generated_notes("Rust", VERSION, "Survey"))

    def test_a_released_and_verified_client_is_skip(self) -> None:
        self.make_client("python", "Python")
        self.assertEqual(self.run_make("release_python_client").returncode, 0)
        result = self.run_make("release_all_clients", clients="python")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("python : SKIP", result.stdout)
        self.assertEqual((self.control / "python.log").read_text(encoding="utf-8").count("release "), 1)
        self.assert_everything_cleaned_up(result)

    def test_a_branch_without_a_tag_is_failed_not_skip_and_cleaned_up(self) -> None:
        self.make_client("python", "Python")
        self.control_file("python", "fail_after_branch")
        first = self.run_make("release_python_client")
        self.assertNotEqual(first.returncode, 0, first.stdout)
        self.assertIn(f"refs/heads/release/{VERSION}", self.origin_refs("python"))
        self.assertNotIn(f"refs/tags/{VERSION}", self.origin_refs("python"))
        self.assert_everything_cleaned_up(first)
        self.control_file("python")
        rerun = self.run_make("release_all_clients", clients="python")
        self.assertNotEqual(rerun.returncode, 0, rerun.stdout)
        self.assertIn("HALF-FINISHED", rerun.stdout)
        self.assertIn("INCOMPLETE:", rerun.stdout)
        self.assertNotIn("SKIP", rerun.stdout)
        self.assert_everything_cleaned_up(rerun)

    def test_a_tag_whose_release_verify_fails_is_incomplete_not_skip(self) -> None:
        self.make_client("python", "Python")
        self.assertEqual(self.run_make("release_python_client").returncode, 0)
        self.control_file("python", "fail_verify")
        result = self.run_make("release_python_client")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("HALF-FINISHED", result.stdout)
        self.assertNotIn("SKIP", result.stdout)
        self.assertTrue((self.driver / ".incomplete_marker-python").is_file(), result.stdout)

    def test_a_release_that_fails_verify_right_after_releasing_is_failed(self) -> None:
        self.make_client("python", "Python")
        self.control_file("python", "fail_verify")
        result = self.run_make("release_python_client")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("release_verify fails", result.stdout)
        self.assert_everything_cleaned_up(result)

    def test_other_versions_on_origin_do_not_make_a_skip(self) -> None:
        origin: Path = self.make_client("python", "Python")
        head: str = self.git("rev-parse", "HEAD", cwd=origin).strip()
        for ref in (f"refs/heads/release/1{VERSION}", f"refs/heads/release/{VERSION}0", f"refs/tags/{VERSION}0", f"refs/tags/1{VERSION}"):
            self.git("update-ref", ref, head, cwd=origin)
        result = self.run_make("release_python_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"RELEASED {VERSION}", result.stdout)

    def test_relative_tmpdir_and_devops_dir_reach_the_client_as_absolute_paths(self) -> None:
        self.make_client("python", "Python")
        devops: Path = self.driver / "given-devops"
        self.git("clone", "-q", str(self.origins / "ondewo-devops-accounts.git"), str(devops))
        for variable, value in (("TMPDIR", os.path.relpath(self.tmpdir, self.driver)), ("DEVOPS_ACCOUNT_DIR", "./given-devops")):
            with self.subTest(variable=variable):
                self.env[variable] = value
                result = self.run_make("release_python_client")
                del self.env[variable]
                self.env["TMPDIR"] = str(self.tmpdir)
                self.assertEqual(result.returncode, 0, result.stdout)
                given: str = dict(
                    line.split("=", 1) for line in (self.control / "python.env").read_text(encoding="utf-8").splitlines() if "=" in line
                )["DEVOPS_ACCOUNT_DIR"]
                self.assertTrue(os.path.isabs(given), given)
                for ref in self.origin_refs("python"):
                    if VERSION in ref:
                        self.git("update-ref", "-d", ref, cwd=self.origins / "ondewo-survey-client-python.git")
        self.assertTrue((devops / "account_github.env").is_file(), "a DEVOPS_ACCOUNT_DIR the driver did not create was deleted")

    def test_an_interrupted_release_still_cleans_up(self) -> None:
        self.make_client("python", "Python")
        self.control_file("python", "hang")
        for interrupt in (signal.SIGINT, signal.SIGTERM):
            with self.subTest(interrupt=interrupt.name):
                process = subprocess.Popen(
                    [
                        "make", "--no-print-directory", "release_python_client", f"ONDEWO_SURVEY_API_VERSION={VERSION}",
                        f"CLIENT_GIT_URL_PREFIX=file://{self.origins}/ondewo-survey-client-",
                        f"DEVOPS_ACCOUNT_GIT_URL=file://{self.origins}/ondewo-devops-accounts.git",
                    ],
                    cwd=self.driver, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    start_new_session=True,
                )
                hanging: Path = self.control / "python.hanging"
                deadline: float = time.monotonic() + 60
                while not hanging.exists() and time.monotonic() < deadline and process.poll() is None:
                    time.sleep(0.05)
                self.assertTrue(hanging.exists(), "the fake release never started")
                os.killpg(process.pid, interrupt)
                output, _ = process.communicate(timeout=60)
                self.assertNotEqual(process.returncode, 0, output)
                self.assert_everything_cleaned_up(subprocess.CompletedProcess(process.args, process.returncode, output))
                hanging.unlink()
                for ref in self.origin_refs("python"):
                    if VERSION in ref:
                        self.git("update-ref", "-d", ref, cwd=self.origins / "ondewo-survey-client-python.git")

    def test_a_client_with_only_half_the_contract_fails_with_a_clear_message(self) -> None:
        makefile: str = LEGACY_CLIENT_MAKEFILE.format(
            name="php", release_md="RELEASE.md", api_branch_variable="ONDEWO_SURVEY_API_GIT_BRANCH"
        ).replace("release_preflight_only_half_a_contract_when_renamed:", "release_preflight:")
        self.make_bare_repository("ondewo-survey-client-php", {"Makefile": makefile, "RELEASE.md": RELEASE_MD.format(display="PHP", product="SURVEY")})
        result = self.run_make("release_php_client")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("client php has only one of release_preflight / release_verify", result.stdout)
        self.assertFalse((self.control / "php.log").exists(), "ondewo_release ran with half a contract")
        self.assert_everything_cleaned_up(result)

    def test_generic_release_section_and_extra_reach_the_notes_verbatim(self) -> None:
        self.make_client("python", "Python")
        result = self.run_make(
            "release_python_client",
            "GENERIC_RELEASE_SECTION=Breaking Changes",
            "GENERIC_RELEASE_EXTRA=* `SurveyRequest` is renamed to `SurveyCreateRequest`.\\n",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        release_md: str = (self.control / "python.RELEASE.md").read_text(encoding="utf-8")
        self.assertIn("\n### Breaking Changes\n", release_md)
        self.assertIn("\n* `SurveyRequest` is renamed to `SurveyCreateRequest`.\n\n*****", release_md)

    def test_the_client_gets_a_private_devops_dir_and_nothing_of_the_driver_make(self) -> None:
        self.make_client("python", "Python")
        result = self.run_make("release_python_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        env: Dict[str, str] = dict(
            line.split("=", 1) for line in (self.control / "python.env").read_text(encoding="utf-8").splitlines() if "=" in line
        )
        self.assertTrue(os.path.isabs(env["DEVOPS_ACCOUNT_DIR"]), env["DEVOPS_ACCOUNT_DIR"])
        self.assertTrue(env["DEVOPS_ACCOUNT_DIR"].startswith(str(self.tmpdir.resolve())), env["DEVOPS_ACCOUNT_DIR"])
        self.assertNotIn("CLIENT=", env.get("MAKEFLAGS", ""))
        for leaked in (
            "GITHUB_GH_TOKEN", "GENERIC_RELEASE_NOTES", "CURRENT_RELEASE_NOTES", "ONDEWO_SURVEY_API_VERSION", "CLIENT",
            "CLIENT_GIT_URL_PREFIX", "DEVOPS_ACCOUNT_GIT_URL",
        ):
            self.assertNotIn(leaked, env, f"{leaked} leaked into the client release")


    def test_the_callers_github_credentials_never_reach_a_client_and_gh_gets_a_private_config(self) -> None:
        # A set GH_TOKEN made the legacy rust client's `gh auth login --with-token` refuse AFTER its tag was
        # pushed (ondewo-s2t-client-rust 7.6.0); without it, that login would rewrite the caller's gh config.
        self.make_client("python", "Python")
        caller_gh_config: Path = self.root / "caller-gh-config"
        self.env.update(
            {
                "GH_TOKEN": "caller-token",
                "GITHUB_TOKEN": "caller-token",
                "GH_ENTERPRISE_TOKEN": "caller-token",
                "GITHUB_ENTERPRISE_TOKEN": "caller-token",
                "GH_HOST": "github.invalid",
                "GH_CONFIG_DIR": str(caller_gh_config),
            }
        )
        result = self.run_make("release_python_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        env: Dict[str, str] = dict(
            line.split("=", 1) for line in (self.control / "python.env").read_text(encoding="utf-8").splitlines() if "=" in line
        )
        for leaked in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_HOST"):
            self.assertNotIn(leaked, env, f"{leaked} leaked into the client release")
        self.assertNotEqual(env["GH_CONFIG_DIR"], str(caller_gh_config))
        self.assertTrue(env["GH_CONFIG_DIR"].startswith(str(self.tmpdir.resolve())), env["GH_CONFIG_DIR"])
        self.assertFalse(caller_gh_config.exists(), "the caller's gh config directory was touched")
        self.assert_everything_cleaned_up(result)

    def test_the_client_clone_and_make_are_not_under_the_drivers_private_umask(self) -> None:
        # A client builds docker images from its checkout and runs them as the caller's uid; a 0600 checkout
        # made the php proto-compiler entrypoint unreadable there (ondewo-sip-api 5.5.2). release_all_clients sets umask 077.
        self.make_client("php", "PHP")
        result = self.run_make("release_all_clients", clients="php")
        self.assertEqual(result.returncode, 0, result.stdout)
        client_umask, makefile_mode = (self.control / "php.modes").read_text(encoding="utf-8").split()
        self.assertEqual(client_umask, "0022", result.stdout)
        self.assertEqual(makefile_mode, "644", result.stdout)


class TestLegacyClient(DriverFixture):
    """A client without release_preflight / release_verify: released as before, judged by its GitHub release."""

    def test_a_new_legacy_release_runs_ondewo_release_and_test_and_is_released(self) -> None:
        self.make_client("cpp", "C++", contract=False)
        result = self.run_make("release_cpp_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(f"RELEASED {VERSION} (GitHub release {VERSION} is published)", result.stdout)
        log: str = (self.control / "cpp.log").read_text(encoding="utf-8")
        self.assertEqual(log.split("\n")[:2], [f"release ONDEWO_SURVEY_VERSION={VERSION}", "TEST"], log)
        release_md: str = (self.control / "cpp.RELEASE.md").read_text(encoding="utf-8")
        self.assertTrue(release_md.startswith("# Release History\n" + generated_notes("C++", VERSION, "SURVEY")), release_md)
        makefile: str = (self.control / "cpp.Makefile").read_text(encoding="utf-8")
        self.assertIn(f"\nONDEWO_SURVEY_API_GIT_BRANCH=tags/{VERSION}\n", makefile)
        self.assert_everything_cleaned_up(result)

    def test_a_legacy_preflight_runs_no_client_target(self) -> None:
        self.make_client("go", "Go", contract=False)
        result = self.run_make("preflight_go_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PREFLIGHT OK (legacy client", result.stdout)
        self.assertFalse((self.control / "go.log").exists(), result.stdout)
        self.assertFalse((self.control / "curl.log").exists(), "the GitHub API was asked about a version origin does not have")
        self.assert_everything_cleaned_up(result)

    def test_a_published_legacy_release_is_skip_and_not_released_again(self) -> None:
        self.make_client("java", "Java", contract=False)
        self.push_release_refs("java")
        self.github_answers("java", "200")
        result = self.run_make("release_all_clients", clients="java")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("java : SKIP", result.stdout)
        self.assertFalse((self.control / "java.log").exists(), result.stdout)
        self.assert_everything_cleaned_up(result)

    def test_a_release_branch_alone_with_a_published_release_is_skip(self) -> None:
        # The old rule: an existing release/<version> branch meant "already released".
        self.make_client("js", "Js", release_md="src/RELEASE.md", contract=False)
        self.push_release_refs("js", tag=False)
        self.github_answers("js", "200")
        result = self.run_make("release_js_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("SKIP:", result.stdout)

    def test_a_legacy_version_on_origin_without_a_github_release_is_incomplete(self) -> None:
        self.make_client("php", "PHP", contract=False)
        self.push_release_refs("php")
        result = self.run_make("release_php_client")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("INCOMPLETE:", result.stdout)
        self.assertNotIn("SKIP", result.stdout)
        self.assertFalse((self.control / "php.log").exists(), result.stdout)
        self.assertTrue((self.driver / ".incomplete_marker-php").is_file(), result.stdout)

    def test_an_unanswered_github_api_is_failed_not_skip_and_changes_nothing(self) -> None:
        self.make_client("rust", "Rust", contract=False)
        self.push_release_refs("rust")
        self.github_answers("rust", "403")
        result = self.run_make("release_all_clients", clients="rust")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("HTTP 403", result.stdout)
        self.assertNotIn("SKIP", result.stdout)
        self.assertFalse((self.control / "rust.log").exists(), result.stdout)
        self.assert_everything_cleaned_up(result)

    def test_the_github_api_is_asked_with_the_callers_token_on_stdin_never_on_argv(self) -> None:
        # The unauthenticated quota (60/hour per address) ran out mid-release and reported a published
        # ondewo-s2t-client-php 7.6.0 as FAILED on HTTP 403.
        self.make_client("php", "PHP", contract=False)
        self.github_answers("php", "200")
        self.env["GH_TOKEN"] = "caller-secret-token"
        result = self.run_make("release_php_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('header = "Authorization: Bearer caller-secret-token"', (self.control / "curl.stdin").read_text(encoding="utf-8"))
        self.assertNotIn("caller-secret-token", (self.control / "curl.argv").read_text(encoding="utf-8"))
        self.assertNotIn("caller-secret-token", result.stdout)

    def test_without_a_caller_token_the_github_api_is_asked_unauthenticated(self) -> None:
        self.make_client("php", "PHP", contract=False)
        self.github_answers("php", "200")
        result = self.run_make("release_php_client")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.control / "curl.stdin").exists(), result.stdout)

    def test_a_legacy_release_whose_github_release_never_appears_is_failed(self) -> None:
        self.make_client("csharp", "Csharp", contract=False)
        self.control_file("csharp", "no_github_release")
        result = self.run_make("release_all_clients", clients="csharp")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("csharp : FAILED", result.stdout)
        self.assertIn("GitHub has no published release", (self.driver / "release_run_csharp.log").read_text(encoding="utf-8"))
        self.assert_everything_cleaned_up(result)

    def test_legacy_and_contract_clients_release_side_by_side(self) -> None:
        self.make_client("python", "Python")
        self.make_client("angular", "Angular", release_md="src/RELEASE.md", contract=False)
        result = self.run_make("release_all_clients", clients="python angular")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("python : RELEASED", result.stdout)
        self.assertIn("angular : RELEASED", result.stdout)
        self.assertIn(f"refs/tags/{VERSION}", self.origin_refs("angular"))
        self.assert_everything_cleaned_up(result)


class TestDryRun(DriverFixture):
    """`make -n` must not clone credentials or write files: make executes $(MAKE) lines even under -n."""

    def test_a_dry_run_clones_nothing_and_writes_nothing(self) -> None:
        self.make_client("python", "Python")
        before: List[str] = sorted(path.name for path in self.driver.iterdir())
        for target in ("release_all_clients", "preflight_all_clients", "ondewo_release", "release_python_client", "release_client"):
            extra: List[str] = ["CLIENT=python"] if target == "release_client" else []
            result = self.run_make("-n", target, *extra, clients="python")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("Cloning", result.stdout, target)
        self.assertEqual(sorted(path.name for path in self.driver.iterdir()), before)
        self.assertEqual(list(self.tmpdir.iterdir()), [])
        self.assertFalse((self.control / "python.log").exists())


class TestPreflightBeforeAnyRelease(DriverFixture):
    """preflight_all_clients gates release_all_clients."""

    def test_one_failing_preflight_releases_nothing(self) -> None:
        self.make_client("python", "Python")
        self.make_client("nodejs", "Nodejs", release_md="src/RELEASE.md")
        self.control_file("nodejs", "fail_preflight")
        result = self.run_make("release_all_clients", clients="python nodejs")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("PREFLIGHT FAILED for: nodejs", result.stdout)
        for name in ("python", "nodejs"):
            self.assertEqual([ref for ref in self.origin_refs(name) if VERSION in ref], [], name)
            self.assertNotIn("release ", (self.control / f"{name}.log").read_text(encoding="utf-8"))
        self.assert_everything_cleaned_up(result)

    def test_a_half_finished_legacy_client_stops_everything(self) -> None:
        self.make_client("python", "Python")
        self.make_client("rust", "Rust", contract=False)
        self.push_release_refs("rust", tag=False)
        result = self.run_make("release_all_clients", clients="python rust")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("PREFLIGHT FAILED for: rust", result.stdout)
        self.assertIn("INCOMPLETE:", result.stdout)
        self.assertEqual([ref for ref in self.origin_refs("python") if VERSION in ref], [])
        self.assert_everything_cleaned_up(result)

    def test_all_preflights_pass_then_all_release_in_parallel_with_one_devops_clone(self) -> None:
        self.make_client("python", "Python")
        self.make_client("js", "Js", release_md="src/RELEASE.md")
        result = self.run_make("release_all_clients", clients="python js")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.count("Cloning ondewo-devops-accounts"), 1, result.stdout)
        self.assertIn("python : RELEASED", result.stdout)
        self.assertIn("js : RELEASED", result.stdout)
        self.assertLess(result.stdout.index("PREFLIGHT OK"), result.stdout.index("Releasing all clients"))
        for name in ("python", "js"):
            log: str = (self.control / f"{name}.log").read_text(encoding="utf-8")
            self.assertLess(log.index("preflight"), log.index("release "))
        self.assert_everything_cleaned_up(result)


class TestOwnReleaseCredentials(DriverFixture):
    """The survey-api's own ondewo_release: one temporary clone, deleted before the release runs."""

    def test_the_token_reaches_the_release_and_the_clone_is_gone_before_it(self) -> None:
        probe: Path = self.root / "probe"
        (self.driver / "probe.mk").write_text(
            f"probe:\n\t@printf '%s|' \"$${{GITHUB_GH_TOKEN}}\" > {probe}; ls -A $${{TMPDIR}} >> {probe}\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["scripts/with_devops_accounts.sh", "--github-token", "make", "-s", "-f", "probe.mk", "probe"],
            cwd=self.driver,
            env={**self.env, "DEVOPS_ACCOUNT_GIT_URL": f"file://{self.origins}/ondewo-devops-accounts.git"},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(probe.read_text(encoding="utf-8").strip(), "fake-token|")
        self.assertEqual(list(self.tmpdir.iterdir()), [])

    def test_a_failing_command_still_removes_the_clone(self) -> None:
        result = subprocess.run(
            ["scripts/with_devops_accounts.sh", "sh", "-c", 'test -f "$DEVOPS_ACCOUNT_DIR/account_github.env" && exit 7'],
            cwd=self.driver,
            env={**self.env, "DEVOPS_ACCOUNT_GIT_URL": f"file://{self.origins}/ondewo-devops-accounts.git"},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(list(self.tmpdir.iterdir()), [])


class TestStaticPins(unittest.TestCase):
    """Properties of the Makefile and the release-hygiene workflow."""

    def test_all_eleven_clients_are_released_with_their_heading_spelling(self) -> None:
        output: str = subprocess.run(
            ["make", "-s", "-f", str(REPO_ROOT / "Makefile"), "--eval",
             "print_names:\n\t@$(foreach c,$(CLIENTS),echo '$(c)=$(call CLIENT_DISPLAY_NAME,$(c))=$(call CLIENT_RELEASE_MD,$(c))';)",
             "print_names"],
            cwd=REPO_ROOT, check=True, capture_output=True, text=True,
        ).stdout
        self.assertEqual(
            output.split(),
            [
                "python=Python=RELEASE.md", "nodejs=Nodejs=src/RELEASE.md", "typescript=Typescript=src/RELEASE.md",
                "angular=Angular=src/RELEASE.md", "js=Js=src/RELEASE.md", "cpp=C++=RELEASE.md",
                "csharp=Csharp=RELEASE.md", "go=Go=RELEASE.md", "java=Java=RELEASE.md", "php=PHP=RELEASE.md",
                "rust=Rust=RELEASE.md",
            ],
        )

    def test_no_bare_export_and_no_sudo(self) -> None:
        self.assertIsNone(re.search(r"^export\s*$", MAKEFILE, re.M), "a bare `export` leaks every variable into the clients")
        self.assertNotIn("sudo", MAKEFILE)

    def test_no_wrapper_line_uses_dollar_make(self) -> None:
        for line in MAKEFILE.splitlines():
            if line.startswith("\t") and "$(WITH_DEVOPS_ACCOUNTS)" in line:
                self.assertNotIn("$(MAKE)", line, "make runs $(MAKE) lines under -n: a dry run would clone the credentials")

    def test_the_proto_compiler_is_pinned_exactly(self) -> None:
        self.assertRegex(MAKEFILE, r"(?m)^ONDEWO_PROTO_COMPILER_VERSION=[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertNotIn("api.github.com/repos/ondewo/ondewo-proto-compiler", MAKEFILE)

    def test_release_all_clients_runs_preflight_first(self) -> None:
        self.assertRegex(MAKEFILE, r"(?m)^release_all_clients_after_preflight: preflight_all_clients$")
        self.assertRegex(MAKEFILE, r"(?m)^\.NOTPARALLEL:$")

    def test_the_release_hygiene_workflow_runs_this_test(self) -> None:
        hygiene: str = (REPO_ROOT / ".github" / "workflows" / "release-hygiene.yml").read_text(encoding="utf-8")
        self.assertIn("'release/**'", hygiene)
        self.assertIn("scripts/test_release_driver.py", hygiene)


if __name__ == "__main__":
    unittest.main()
