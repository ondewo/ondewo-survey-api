# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Principles

Behavioral guidelines to reduce common mistakes. They bias toward caution over speed; for trivial tasks, use judgment.

### Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### Simplicity first

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### Surgical changes

Touch only what you must. Clean up only your own mess.

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that _your_ changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: every changed line should trace directly to the user's request.

### Goal-driven execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

These guidelines are working if: fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and
clarifying questions come before implementation rather than after mistakes.

## Logging

```python
from loguru import logger as log
```

- **Levels:** `log.trace()`, `log.debug()`, `log.info()`, `log.warning()`, `log.error()`, `log.exception()`. Choose by
  hotness/verbosity — `trace` for per-token / hot-path detail, `debug` for routine method entry/exit, `info` for notable
  lifecycle events, `warning` / `error` / `exception` for problems.
- **Interpolate with f-strings, not loguru's `{}` positional args.** Consistent with the Code Style rule, use
  `f"…{value}"`; only add the `f` prefix when the string actually interpolates (`"START: …"` with no params stays a
  plain string).
- **`START:` / `DONE:` bracketing.** Wrap a method (or other notable operation) with a `START:` line at entry and a
  `DONE:` line at exit, both naming `ClassName: method_name` (append `: param={value}` context where useful):

  ```python
  log.debug("START: IntentBertClassifier: predict")
  ...
  log.debug(f"DONE: IntentBertClassifier: predict. Elapsed time: {perf_counter() - start_time:.5f}")
  ```

- **Timing uses `perf_counter()`, rendered `:.5f`.** Measure elapsed time with `time.perf_counter()` captured as a start
  value and subtracted at the `DONE:` line; always format the elapsed value with the `:.5f` spec:

  ```python
  from time import perf_counter

  start_time: float = perf_counter()
  ...
  log.info(f"DONE: SESSION SERVICER: DetectIntent. Elapsed time: {perf_counter() - start_time:.5f}")
  ```

  Never measure a duration with `time.time()` — reserve `time.time()` for wall-clock timestamps (epoch seconds persisted
  to a DB / proto, unique-id or filename stamps). `perf_counter()` has an undefined epoch and must not be stored or
  compared across processes.

## Docstrings

Google-style, triple double-quotes:

```python
"""
Short imperative summary line.

Args:
    param_name (type):
        Description of the parameter.

Returns:
    type:
        Description of the return value.

Raises:
    ExceptionType:
        When this exception is raised.
"""
```

## Git Commits

- **Never include Claude as author or co-author** in commit messages, PR descriptions, or any other text. Do not add
  `Co-Authored-By: Claude…` trailers, "Generated with Claude Code" footers, or any similar attribution.
- The user's own git author identity (already configured in git) is the only identity that should appear on commits.
- This rule overrides the default Claude Code commit-template guidance.
- **Never prepend the JIRA ticket ID** (e.g. `[OND211-2386]`) to the commit subject yourself. The `giticket` pre-commit
  hook reads the ticket from the branch name (`(feature|bugfix|support|hotfix)/<TICKET>-…`) and prepends `[<ticket>]`
  (with a trailing space) automatically. Writing the prefix manually produces a duplicate like
  `[OND211-2386] [OND211-2386] feat: …`. Write the subject as plain Conventional Commits (`feat: …`, `fix(scope): …`,
  `docs(types): …`) and let the hook add the prefix on commit.

## General Principles

- Follow existing patterns before introducing new abstractions.
- Keep changes minimal and consistent with surrounding code.
- Validate inputs early with descriptive, context-rich error messages.
- Use context managers for files, sockets, and thread pools.
- Prefer region comments for grouping methods in files that already use them.
- End edited Markdown and YAML files with a trailing newline.

## Client-release orchestration (`release_all_clients`)

- It **fails loudly** on a genuine client-release error: the piped sub-make runs under `bash -c 'set -o pipefail; make -C … | tee …'` (a plain sh pipe returns tee's 0 and masks failures), and a **marker file** distinguishes an "already released" SKIP from a real FAILURE (make flattens recipe exit codes to 2, so the code alone can't tell them apart). Do not regress either.
- Every token-bearing recipe line is `@`-prefixed so make never echoes a secret — `docker run -e <TOKEN>`, `echo $(TOKEN) | gh auth`, `twine … -p${PYPI_PASSWORD}`, and the credential sub-make `make release $(info)` (which expands the token at runtime and is easy to miss).

## Pre-commit upgraded (language-agnostic hook set)

Pre-commit here uses only the language-agnostic hooks — **markdownlint-cli2, pre-commit-hooks hygiene, giticket, conventional-pre-commit** — no ruff/mypy/uv (there is no Python). Generated docs (`docs/`) and any generated code are excluded via the top-level `exclude:`.

- **markdownlint MD053 is disabled** (its auto-fix deletes `[comment]: <>` reference-definition markers).
- **markdownlint RELEASE.md reformatting is content-safe**: it only strips trailing whitespace and adds blank lines around headings — the `## Release … <VERSION>` headings and `*****` separators that `ondewo_release` greps for remain intact. (Confirmed: the 6.5.0 release notes sliced correctly after the reformat.)

## GitHub Actions (`Generate API Documentation`) is a REQUIRED gate

`.github/workflows/generate-doc-and-deploy.yaml` is the **only** workflow in this repo, and it is a gate, not a
reporting job: it runs on every push and every PR against `master`, and its Deploy step **writes back to
`master:docs`**. Treat a red run as blocking.

The job has exactly three authored steps (`Set up job`, `Build …-action`, `Post Checkout` and `Complete job` are
runner-generated):

1. **`Checkout 🛎️`** — `actions/checkout@v5` with `submodules: true`.
2. **`Generate documentation from ONDEWO proto files 🔧`** — `ondewo/ondewo-protoc-gen-doc-action@master`, a **Docker**
   action (`FROM pseudomuto/protoc-gen-doc`) whose entrypoint is one `protoc` invocation per requested format:

   ```bash
   protoc -I. -Igoogleapis \
     --doc_opt=/resources/templates/<fmt>.tmpl,index.<fmt> \
     --doc_out=docs $(find ondewo -name '*.proto' | sort)
   ```

3. **`Deploy 🚀`** — `JamesIves/github-pages-deploy-action@v4`, `folder: docs` → `target-folder: docs` on `master`.

### Reproducing it locally

- **There is no `uv` / `ruff` / `mypy` / `pytest` step to reproduce, and no `pyproject.toml` or `uv.lock` to be stale
  against.** This is a `.proto` + generated-docs repo with **zero** Python files; the fleet-standard
  `uv run --frozen …` reproduction that the client SDK repos document simply does not exist here. Do not go looking
  for it, and do not add one to make this repo "match" the others.
- Step 2 — the only step that can actually fail on our content — is reproduced by `make build_docs`, which clones the
  action repo, builds **the same `Dockerfile`/image the action builds**, and runs the same entrypoint args:

  ```bash
  make build_docs          # clone + docker build + generate html,md into docs/
  git status --porcelain -- docs/   # MUST be empty: committed docs == regenerated docs
  make clean_docs_builder  # drop the clone and the local image
  ```

- **Verify it non-vacuously.** `make build_docs` prints its cheerful `✓ Documentation generated` line whether or not
  `protoc` did anything meaningful, and a no-op leaves the committed files in place, so "clean `git status`" alone
  proves nothing. Delete the outputs first and require them to come back byte-identical:

  ```bash
  rm -f docs/index.html docs/index.md docs/style.css && make build_docs && git status --porcelain -- docs/
  ```

  Confirmed at `995d193`: all three files regenerate with identical checksums.
- **Step 3 cannot be run here at all** — it needs GitHub Pages and the runner's `GITHUB_TOKEN`. The step even carries
  `if: ${{ !env.ACT }}` so it self-skips under `act`. Do not claim it "passes locally"; it is unreproducible off the
  runner, and its correctness is only ever observed in a real run.
- Ask the API what actually happened rather than guessing; there is no `gh` CLI on this machine:

  ```bash
  SHA=$(git rev-parse HEAD)
  curl -s "https://api.github.com/repos/ondewo/ondewo-survey-api/actions/runs?head_sha=$SHA"
  curl -s "https://api.github.com/repos/ondewo/ondewo-survey-api/actions/runs/<run_id>/jobs"
  ```

  The `/jobs` call is the one worth making: it prints a per-step `conclusion`, which is what distinguishes "the docs
  step passed" from "the whole run was skipped".

### Sharp edges found while running it

- **`submodules: true` on the checkout is currently INERT.** There is no `.gitmodules` and not one gitlink
  (`git ls-files -s | awk '$1=="160000"'` is empty); `googleapis/` is **690 ordinary tracked files**, vendored. So
  `-Igoogleapis` works because those files are in the commit, _not_ because a submodule was initialised — and a fresh
  clone needs no `--recursive`. Do not read that flag as evidence that `googleapis/` is a submodule.
- **`google/protobuf/{empty,field_mask,struct}.proto` are NOT in this repo.** They resolve from the well-known types
  bundled inside the `pseudomuto/protoc-gen-doc` image. Only `google/api/annotations.proto` (from `googleapis/`) and
  `ondewo/survey/survey.proto` (from `-I.`) come from the checkout, so grepping the repo for a missing import will
  mislead you about which include path is at fault.
- **CI OVERWRITES `docs/`, so a hand-edit there is silently reverted.** The Deploy step pushes the regenerated folder
  back onto `master`, which is the same reason pre-commit carries `exclude: '^(docs/|googleapis/)'`. If the rendered
  documentation is wrong, fix the `.proto` comments — never `docs/index.md`.
- **Both actions float on a moving ref** (`…-doc-action@master`, `github-pages-deploy-action@v4`). A green run is
  evidence about the bits that ran that day, not about the bits that will run tomorrow; when the docs step breaks with
  no change on our side, check the action before the protos.
- `make build_docs` leaves a full nested git repo at `.tmp-protoc-gen-doc-action/`. It is now gitignored — untracked,
  it made `git add -A` record a phantom gitlink. Prefer `make clean_docs_builder` when you are done.
