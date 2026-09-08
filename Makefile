export
# ---------------- BEFORE RELEASE ----------------
# 1 - Update Version Number
# 2 - Update RELEASE.md
# -------------- Release Process Steps --------------
# 1 - Get Credentials from devops-accounts repo
# 2 - Create Release Branch and push
# 3 - Create Release Tag and push
# 4 - GitHub Release
# 5 - PyPI Release

########################################################
# 		Variables
########################################################

# MUST BE THE SAME AS API in Mayor and Minor Version Number
# example: API 2.9.0 --> Client 2.9.X
ONDEWO_SURVEY_API_VERSION=2.0.0

# You need to setup an access token at https://github.com/settings/tokens - permissions are important
GITHUB_GH_TOKEN?=ENTER_YOUR_TOKEN_HERE

# Terminate on the ***** separator that delimits release entries, NOT on /\*\*/ - that matched the first
# markdown **bold** span inside the entry and silently truncated the notes there. It is correct today only
# because no entry yet uses inline bold; the moment one does, every line after it is dropped from
# `gh release create -n "$(CURRENT_RELEASE_NOTES)"` with no error at all.
CURRENT_RELEASE_NOTES=`cat RELEASE.md \
	| perl -ne 'print if /Release ONDEWO Survey Server API ${ONDEWO_SURVEY_API_VERSION}/../^\*{5}/'`

GH_REPO="https://github.com/ondewo/ondewo-survey-api"
DEVOPS_ACCOUNT_GIT="ondewo-devops-accounts"
DEVOPS_ACCOUNT_DIR="./${DEVOPS_ACCOUNT_GIT}"
IMAGE_UTILS_NAME=ondewo-survey-api-utils:${ONDEWO_SURVEY_API_VERSION}
.DEFAULT_GOAL := help

########################################################
#       ONDEWO Standard Make Targets
########################################################

setup_developer_environment_locally: install_python_requirements install_precommit_hooks install_nvm ## Sets up local development environment !! Forcefully closes current terminal

install_nvm: ## Install NVM, node and npm !! Forcefully closes current terminal
	@curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
	@sh install_nvm.sh
	$(eval PID:=$(shell ps -ft $(ps | tail -1 | cut -c 8-13) | head -2 | tail -1 | cut -c 1-8))
	@node --version & npm --version || (kill -KILL ${PID})

install_python_requirements: ## Installs python requirements flak8 and mypy
	wget -q https://raw.githubusercontent.com/ondewo/ondewo-survey-client-python/master/requirements.txt -O requirements.txt
	wget -q https://raw.githubusercontent.com/ondewo/ondewo-survey-client-python/master/requirements-dev.txt -O requirements-dev.txt
	wget -q https://raw.githubusercontent.com/ondewo/ondewo-survey-client-python/master/.flake8 -O .flake8
	wget -q https://raw.githubusercontent.com/ondewo/ondewo-survey-client-python/master/mypy.ini -O mypy.ini
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install_precommit_hooks: ## Installs pre-commit hooks and sets them up for the ondewo-survey-api repo
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg

precommit_hooks_run_all_files: ## Runs all pre-commit hooks on all files and not just the changed ones
	pre-commit run --all-file

flake8: ## Runs flake8
	flake8 --config .flake8 .

mypy: ## Run mypy static code checking
	@echo "---------------------------------------------"
	@echo "START: Run mypy in pre-commit hook ..."
	pre-commit run mypy --all-files
	@echo "DONE: Run mypy in pre-commit hook."
	@echo "---------------------------------------------"
	@echo "START: Run mypy directly ..."
	mypy --config-file=mypy.ini .
	@echo "DONE: Run mypy directly"
	@echo "---------------------------------------------"

help: ## Print usage info about help targets
	# (first comment after target starting with double hashes ##)
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

makefile_chapters: ## Shows all sections of Makefile
	@echo `cat Makefile| grep "########################################################" -A 1 | grep -v "########################################################"`

build_docs: ## Build documentation locally using the same Docker image as CI/CD
	@echo "Building documentation using ondewo-protoc-gen-doc-action..."
	@if [ ! -d ".tmp-protoc-gen-doc-action" ]; then \
		echo "Cloning ondewo-protoc-gen-doc-action..."; \
		git clone --depth 1 https://github.com/ondewo/ondewo-protoc-gen-doc-action.git .tmp-protoc-gen-doc-action; \
	fi
	@echo "Building Docker image with ONDEWO templates..."
	@docker build -t ondewo-protoc-gen-doc:local .tmp-protoc-gen-doc-action
	@echo "Generating documentation..."
	@docker run --rm \
		--user "$(shell id -u):$(shell id -g)" \
		-v "$(shell pwd):/workspace" \
		-w /workspace \
		ondewo-protoc-gen-doc:local \
		html,md index
	@echo "✓ Documentation generated in docs/ directory"
	@echo "  Open docs/index.html in your browser to view"

clean_docs_builder: ## Remove the cloned protoc-gen-doc-action repo and Docker image
	@echo "Cleaning up documentation builder..."
	@rm -rf .tmp-protoc-gen-doc-action
	@docker rmi ondewo-protoc-gen-doc:local 2>/dev/null || true
	@echo "✓ Cleanup complete"

TEST:
	@echo "----------------------------------------------\nGITHUB_GH_TOKEN\n----------------------------------------------\n$(if $(GITHUB_GH_TOKEN),<set>,<unset>)\n"
	@echo "----------------------------------------------\nCURRENT_RELEASE_NOTES\n----------------------------------------------\n${CURRENT_RELEASE_NOTES}\n"

githubio_logic_pre:
	$(eval REPO_NAME:= $(shell echo ${GH_REPO} | cut -d "-" -f 2 ))
	$(eval REPO_NAME_UPPER:= $(shell echo ${GH_REPO} | cut -d "-" -f 2 | perl -pe 's/(.*)/\U$$1/'))
	$(eval DOCS_DIR:=ondewo.github.io/docs/ondewo-${REPO_NAME}-api/${ONDEWO_SURVEY_API_VERSION})
	@perl -i -ne "print unless /{ number: '${ONDEWO_SURVEY_API_VERSION}', link: 'ondewo-${REPO_NAME}-api\/${ONDEWO_SURVEY_API_VERSION}\/' },/" ondewo.github.io/data.js
	@rm -rf ${DOCS_DIR}
	@mkdir "${DOCS_DIR}"
	@cp docs/* ${DOCS_DIR}
	@perl -i -pe "s/h1>Protocol Documentation/h1>${REPO_NAME_UPPER} ${ONDEWO_SURVEY_API_VERSION} Documentation/" ${DOCS_DIR}/index.html

githubio_logic: | githubio_logic_pre
	$(eval REPO_NAME:= $(shell echo ${GH_REPO} | cut -d "-" -f 2 ))
	$(eval REPO_NAME_UPPER:= $(shell echo ${GH_REPO} | cut -d "-" -f 2 | perl -pe 's/(.*)/\U$$1/'))
	@git branch | grep "*" | grep -q "master" || (echo "Not on master branch"  & rm -rf ondewo.github.io && exit 1)
	@! cat ondewo.github.io/data.js | perl -ne "print if /name\: '${REPO_NAME_UPPER}'/../end\: ''/" | grep -q "number: '${ONDEWO_SURVEY_API_VERSION}'" || (echo "Already Released" && exit 1)
	$(eval VERSION_LINE:= $(shell cat -n ondewo.github.io/data.js | perl -ne "print if /name\: '${REPO_NAME_UPPER}'/../end\: ''/" | grep "versions: " -A 1 | tail -1 | grep -o -E '[0-9]+' | head -1 | perl -pe 's/^0+//'))
	@TEMP_TEXT="$$(cat ondewo.github.io/script_object.txt | perl -pe 's/VERSION/${ONDEWO_SURVEY_API_VERSION}/g; s/TECHNOLOGY/${REPO_NAME}/g')" perl -i -pe 'print "$$ENV{TEMP_TEXT}\n" if $$. == ${VERSION_LINE}' ondewo.github.io/data.js
	@npm install prettier && cd ondewo.github.io && npx prettier -w --single-quote data.js
	$(eval DOCS_DIR:=ondewo.github.io/docs/ondewo-${REPO_NAME}-api/${ONDEWO_SURVEY_API_VERSION})
	@rm -rf ${DOCS_DIR}
	@mkdir "${DOCS_DIR}"
	@cp docs/* ${DOCS_DIR}
	@perl -i -pe "s/h1>Protocol Documentation/h1>${REPO_NAME_UPPER} ${ONDEWO_SURVEY_API_VERSION} Documentation/" ${DOCS_DIR}/index.html
	$(eval HEADER_LINE:= $(shell cat ${DOCS_DIR}/index.html | grep -n "${REPO_NAME_UPPER} ${ONDEWO_SURVEY_API_VERSION} Documentation" | grep -o -E '[0-9]+' | head -1 | perl -pe 's/^0+//'))
	@TEMP_IMG="$$(cat ondewo.github.io/script_image.txt)" perl -i -pe 'print "$$ENV{TEMP_IMG}\n" if $$. == ${HEADER_LINE}' ${DOCS_DIR}/index.html
	head -30 ${DOCS_DIR}/index.html
	cat ondewo.github.io/data.js | perl -ne "print if /name\: '${REPO_NAME_UPPER}'/../end\: ''/"
	@git -C ondewo.github.io status
	@git -C ondewo.github.io add data.js
	@git -C ondewo.github.io add docs
	@git -C ondewo.github.io status
	@git -C ondewo.github.io commit -m "Added ${REPO_NAME} Documentation for ${ONDEWO_SURVEY_API_VERSION}"
	@git -C ondewo.github.io push

update_githubio:
	@if [ -d "ondewo.github.io" ]; then \
		echo "Removing existing directory ondewo.github.io"; \
		rm -rf ondewo.github.io; sleep 3s; \
	fi
	@git clone git@github.com:ondewo/ondewo.github.io.git
	. ~/.nvm/nvm.sh && make githubio_logic || (echo "Done")
	@rm -rf ondewo.github.io

########################################################
#       Repo Specific Make Targets
########################################################
#		Release

release: create_release_branch create_release_tag build_and_release_to_github_via_docker ## Automate the entire release process
	@echo "Release Finished"

create_release_branch: ## Create Release Branch and push it to origin
	git checkout -b "release/${ONDEWO_SURVEY_API_VERSION}"
	git push -u origin "release/${ONDEWO_SURVEY_API_VERSION}"

create_release_tag: ## Create Release Tag and push it to origin
	git tag -a ${ONDEWO_SURVEY_API_VERSION} -m "release/${ONDEWO_SURVEY_API_VERSION}"
	git push origin ${ONDEWO_SURVEY_API_VERSION}

login_to_gh: ## Login to Github CLI with Access Token
	@echo $(GITHUB_GH_TOKEN) | gh auth login -p ssh --with-token

build_gh_release: ## Generate Github Release with CLI
	gh release create --repo $(GH_REPO) "$(ONDEWO_SURVEY_API_VERSION)" -n "$(CURRENT_RELEASE_NOTES)" -t "Release ${ONDEWO_SURVEY_API_VERSION}"

CLIENTS := python nodejs typescript angular js

release_all_clients: ## Release all clients IN PARALLEL; one failing client does not abort the others
	@echo "Releasing all clients in parallel for ${ONDEWO_SURVEY_API_VERSION} ..."; \
	rm -f .already_released_marker-* .client_status-*; \
	for c in $(CLIENTS); do \
		( if make release_$${c}_client > release_run_$${c}.log 2>&1; then echo RELEASED > .client_status-$$c; \
		  elif [ -f .already_released_marker-$$c ]; then echo SKIP > .client_status-$$c; \
		  else echo FAILED > .client_status-$$c; fi ) & \
	done; \
	wait; \
	echo ""; echo "=============== CLIENT RELEASE SUMMARY (${ONDEWO_SURVEY_API_VERSION}) ==============="; \
	failed=0; \
	for c in $(CLIENTS); do \
		s=$$(cat .client_status-$$c 2>/dev/null || echo NO_STATUS); \
		echo "  $$c : $$s"; \
		if [ "$$s" = FAILED ] || [ "$$s" = NO_STATUS ]; then failed=1; echo "      -> see release_run_$$c.log"; fi; \
	done; \
	echo "==============================================================="; \
	rm -f .already_released_marker-* .client_status-*; \
	if [ "$$failed" = 1 ]; then echo "RESULT: one or more clients FAILED (the others released independently)."; exit 1; fi; \
	echo "RESULT: all clients released or already up-to-date."

GENERIC_CLIENT?=
RELEASEMD?=
# The section heading is driven by GENERIC_RELEASE_SECTION so a breaking API release does not publish five
# client majors under "Improvements". On a major bump, override it and describe the break:
#   make release_all_clients GENERIC_RELEASE_SECTION='Breaking Changes' \
#     GENERIC_RELEASE_EXTRA='* `<Message>` is renamed to `<NewMessage>`.\n'
GENERIC_RELEASE_SECTION?=Improvements
GENERIC_RELEASE_EXTRA?=
# Emitted markdownlint-clean, and deliberately on ONE line. Every ` \n` used to leave a trailing space on
# each generated line and a leading space on the list item, and make's line-continuation collapses
# `\<newline><tab>` to a further space, so the block tripped MD009/MD007/MD022/MD012/MD032 in EVERY client
# and the first pre-commit run of every release `Failed - files were modified by this hook` (10 auto-fixes
# in the Python client, measured on a lint-clean RELEASE.md). It self-healed on the re-run, but it also
# left the heading as `\#\# Release ... <VERSION> ` WITH a trailing space, which the release_client guard
# below cannot match because that grep anchors on `$$` - so the duplicate-entry guard would only ever have
# matched entries a previous markdownlint run had already stripped. Keep this byte-identical to what
# markdownlint normalises to: no trailing spaces, a blank line around the heading and around the list.
GENERIC_RELEASE_NOTES=\n*****************\n\n\\\#\\\# Release ONDEWO Survey REPONAME Client ${ONDEWO_SURVEY_API_VERSION}\n\n\\\#\\\#\\\# ${GENERIC_RELEASE_SECTION}\n\n* Tracking API Version [${ONDEWO_SURVEY_API_VERSION}](https://github.com/ondewo/ondewo-survey-api/releases/tag/${ONDEWO_SURVEY_API_VERSION}) ( [Documentation](https://ondewo.github.io/ondewo-survey-api/) )\n${GENERIC_RELEASE_EXTRA}

release_client:
	$(eval REPO_NAME:= $(shell echo ${GENERIC_CLIENT} | cut -d "-" -f 4 | cut -d '.' -f 1))
	$(eval REPO_DIR:= $(shell echo "ondewo-survey-client-${REPO_NAME}"))
	$(eval UPPER_REPO_NAME:= $(shell echo ${REPO_NAME} | perl -pe 's/.*/\u$$&/'))
# Get newest Proto-Compiler Version
	$(eval PROTO_COMPILER:= $(shell curl https://api.github.com/repos/ondewo/ondewo-proto-compiler/tags | grep "\"name\"" | head -1 | cut -d '"' -f 4))
# Clone Repo
	rm -rf ${REPO_DIR}
	rm -f build_log_${REPO_NAME}.txt

	@# printf '%b', not echo: echo appends a newline of its own on top of the trailing \n, which left a
	@# second blank line before the previous entry's separator (markdownlint MD012 used to eat it).
	@# Read through the environment (line 1 is a bare `export`) rather than interpolating the value into
	@# the command text: the value used to carry its own double quotes, so a backtick in
	@# GENERIC_RELEASE_EXTRA would be command-substituted by the shell before printf ever saw it.
	@# The final perl normalises the file to exactly ONE trailing newline: printf '%b' adds none, so a
	@# GENERIC_RELEASE_EXTRA that does not end in \n would leave the file without a final newline, and the
	@# insert below would then swallow the blank line before the next ***** separator (MD032).
	@printf '%b' "$$GENERIC_RELEASE_NOTES" > temp-notes-${REPO_NAME} && perl -i -pe 's/\\//g' temp-notes-${REPO_NAME} && perl -i -pe 's/REPONAME/${UPPER_REPO_NAME}/g' temp-notes-${REPO_NAME} && perl -0777 -i -pe 's/\n*\z/\n/' temp-notes-${REPO_NAME}
	git clone ${GENERIC_CLIENT}
# Check if Client is already uptodate with API Version
	@! git -C ${REPO_DIR} branch -a | grep -q ${ONDEWO_SURVEY_API_VERSION} || (echo "Already Released ${ONDEWO_SURVEY_API_VERSION} \n\n\n"  && touch .already_released_marker-${REPO_NAME} && rm -rf ${REPO_DIR} && rm -f temp-notes-${REPO_NAME} && exit 1)

# Change Version Number and RELEASE NOTES
# Only insert the generated boilerplate when the client does not already document this version. A client
# whose RELEASE.md was written by hand ahead of the release would otherwise get a SECOND
# "Release ONDEWO Survey <Name> Client <VERSION>" heading, which buries the curated entry (the notes slice
# takes the FIRST match) and trips markdownlint MD025/MD024 - neither of which auto-fixes, so the client's
# own pre-commit fails the build and the release aborts. ondewo-nlu-client-angular carries two
# byte-identical "## Release ONDEWO NLU Angular Client 3.5.0" blocks from exactly this failure.
	cd ${REPO_DIR} && if grep -qE "^#+ Release ONDEWO Survey ${UPPER_REPO_NAME} Client ${ONDEWO_SURVEY_API_VERSION}$$" ${RELEASEMD}; then \
		echo "${RELEASEMD} already documents ${ONDEWO_SURVEY_API_VERSION} - keeping the curated entry, not inserting the generated notes"; \
	else \
		perl -i -ne 'print; if(/Release History/){open my $$fh,"<","../temp-notes-${REPO_NAME}"; print while <$$fh>; close $$fh}' ${RELEASEMD}; \
	fi
	cd ${REPO_DIR} && head -20 ${RELEASEMD}
	cd ${REPO_DIR} && perl -i -pe 's/ONDEWO_SURVEY_VERSION.*=.*/ONDEWO_SURVEY_VERSION=${ONDEWO_SURVEY_API_VERSION}/' Makefile
	cd ${REPO_DIR} && perl -i -pe 's/ONDEWO_PROTO_COMPILER_GIT_BRANCH.*=.*/ONDEWO_PROTO_COMPILER_GIT_BRANCH=tags\/${PROTO_COMPILER}/' Makefile
	cd ${REPO_DIR} && perl -i -pe 's/SURVEY_API_GIT_BRANCH.*=.*/SURVEY_API_GIT_BRANCH=tags\/${ONDEWO_SURVEY_API_VERSION}/' Makefile && head -30 Makefile

# Build new code
	bash -c 'set -o pipefail; make -C ${REPO_DIR} ondewo_release | tee build_log_${REPO_NAME}.txt'
	make -C ${REPO_DIR} TEST
# Remove everything from Release
	sudo rm -rf ${REPO_DIR}
	rm -f temp-notes-${REPO_NAME}

PYTHON_CLIENT="git@github.com:ondewo/ondewo-survey-client-python.git"

release_python_client: ## Release Python Client
	@echo "Start releasing Python Client"
	make release_client GENERIC_CLIENT=${PYTHON_CLIENT} RELEASEMD="RELEASE.md"
	@echo "End releasing Python Client \n \n \n"

NODEJS_CLIENT="git@github.com:ondewo/ondewo-survey-client-nodejs.git"

release_nodejs_client: ## Release NodeJs Client
	@echo "Start releasing Nodejs Client"
	make release_client GENERIC_CLIENT=${NODEJS_CLIENT} RELEASEMD="src/RELEASE.md"
	@echo "End releasing Nodejs Client \n \n \n"

TYPESCRIPT_CLIENT="git@github.com:ondewo/ondewo-survey-client-typescript.git"

release_typescript_client: ## Release Typescript Client
	@echo "Start releasing Typescript Client"
	make release_client GENERIC_CLIENT=${TYPESCRIPT_CLIENT} RELEASEMD="src/RELEASE.md"
	@echo "End releasing Typescript Client \n \n \n"

ANGULAR_CLIENT="git@github.com:ondewo/ondewo-survey-client-angular.git"

release_angular_client:
	@echo "Start releasing Angular Client"
	make release_client GENERIC_CLIENT=${ANGULAR_CLIENT} RELEASEMD="src/RELEASE.md"
	@echo "End releasing Angular Client \n \n \n"

JS_CLIENT="git@github.com:ondewo/ondewo-survey-client-js.git"

release_js_client: ## Release JS Client
	@echo "Start releasing Js Client"
	make release_client GENERIC_CLIENT=${JS_CLIENT} RELEASEMD="src/RELEASE.md"
	@echo "End releasing Js Client \n \n \n"

########################################################
#		GITHUB

build_and_release_to_github_via_docker: build_utils_docker_image release_to_github_via_docker_image ## Release automation for building and releasing on GitHub via a docker image

build_utils_docker_image: ## Build utils docker image
	docker build -f Dockerfile.utils -t ${IMAGE_UTILS_NAME} .

push_to_gh: login_to_gh build_gh_release ## Logs into GitHub CLI and Releases
	@echo 'Released to Github'

release_to_github_via_docker_image: ## Release to Github via docker
	@docker run --rm \
		-e GITHUB_GH_TOKEN=${GITHUB_GH_TOKEN} \
		${IMAGE_UTILS_NAME} make push_to_gh

########################################################
#		DEVOPS-ACCOUNTS

ondewo_release: spc clone_devops_accounts run_release_with_devops ## Release with credentials from devops-accounts repo
	@rm -rf ${DEVOPS_ACCOUNT_GIT}

clone_devops_accounts: ## Clones devops-accounts repo
	@if [ -d $(DEVOPS_ACCOUNT_GIT) ]; then rm -Rf $(DEVOPS_ACCOUNT_GIT); fi
	git clone git@bitbucket.org:ondewo/${DEVOPS_ACCOUNT_GIT}.git

run_release_with_devops: ## Gets Credentials from devops-repo and runs release with them
	$(eval info:= $(shell cat ${DEVOPS_ACCOUNT_DIR}/account_github.env | grep GITHUB_GH))
	@make release $(info)

spc: ## Checks if the Release Branch, Tag and Pypi version already exist
	$(eval filtered_branches:= $(shell git branch --all | grep "release/${ONDEWO_SURVEY_API_VERSION}"))
	$(eval filtered_tags:= $(shell git tag --list | grep "${ONDEWO_SURVEY_API_VERSION}"))
	@if test "$(filtered_branches)" != ""; then echo "-- Test 1: Branch exists!!" & exit 1; else echo "-- Test 1: Branch is fine";fi
	@if test "$(filtered_tags)" != ""; then echo "-- Test 2: Tag exists!!" & exit 1; else echo "-- Test 2: Tag is fine";fi

########################################################
#		UNRELEASE

unrelease: build_utils_docker_image unrelease_to_github_via_docker_image ## Undo a release: delete the GitHub release, release branch, and release tag
	@echo "Unrelease Finished"

delete_gh_release: ## Delete GitHub Release, release branch and release tag via gh CLI
	gh release delete --repo $(GH_REPO) "$(ONDEWO_SURVEY_API_VERSION)" --yes
	git branch -D "release/${ONDEWO_SURVEY_API_VERSION}" || true
	git push origin --delete "release/${ONDEWO_SURVEY_API_VERSION}" || true
	git tag -d ${ONDEWO_SURVEY_API_VERSION} || true
	git push origin --delete ${ONDEWO_SURVEY_API_VERSION} || true

unrelease_to_github_via_docker_image: ## Execute unrelease through Docker container
	@docker run --rm \
		-e GITHUB_GH_TOKEN=${GITHUB_GH_TOKEN} \
		${IMAGE_UTILS_NAME} make delete_gh_release

ondewo_unrelease: clone_devops_accounts run_unrelease_with_devops ## Unrelease with credentials from devops-accounts repo
	@rm -rf ${DEVOPS_ACCOUNT_GIT}

run_unrelease_with_devops: ## Gets Credentials from devops-repo and runs unrelease with them
	$(eval info:= $(shell cat ${DEVOPS_ACCOUNT_DIR}/account_github.env | grep GITHUB_GH))
	@make unrelease $(info)
