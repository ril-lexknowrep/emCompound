.DEFAULT_GOAL = all
# Bash is needed for time, compgen, [[ and other builtin commands
SHELL := /bin/bash -o pipefail
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)
NOCOLOR := $(shell tput sgr0)
PYTHON := python3
VENVDIR := $(CURDIR)/venv
VENVPIP := $(VENVDIR)/bin/python -m pip
VENVPYTHON := $(VENVDIR)/bin/python

# Module specific parameters
MODULE := emCompound
MODULE_PARAMS :=

# These targets do not show as possible target with bash completion
__extra-deps:
	# Do extra stuff (e.g. compiling, downloading) before building the package
	@exit 0
.PHONY: __extra-deps

__clean-extra-deps:
	# e.g. @rm -rf stuff
	@exit 0
.PHONY: __clean-extra-deps

# From here only generic parts

# Parse version string and create new version. Originally from: https://github.com/mittelholcz/contextfun
# Variable is empty in Travis-CI if not git tag present
TRAVIS_TAG ?= ""
OLDVER := $$(grep -P -o "(?<=__version__ = ')[^']+" $(MODULE)/version.py)

MAJOR := $$(echo $(OLDVER) | sed -r s"/([0-9]+)\.([0-9]+)\.([0-9]+)/\1/")
MINOR := $$(echo $(OLDVER) | sed -r s"/([0-9]+)\.([0-9]+)\.([0-9]+)/\2/")
PATCH := $$(echo $(OLDVER) | sed -r s"/([0-9]+)\.([0-9]+)\.([0-9]+)/\3/")

NEWMAJORVER="$$(( $(MAJOR)+1 )).0.0"
NEWMINORVER="$(MAJOR).$$(( $(MINOR)+1 )).0"
NEWPATCHVER="$(MAJOR).$(MINOR).$$(( $(PATCH)+1 ))"

all: clean venv build install test
	@echo
	@echo "$(GREEN)Package $(MODULE) is successfully installed into venv and all tests are OK! :)$(NOCOLOR)"
	@echo

install-dep-packages:
	@echo "Installing needed packages from Aptfile..."
	@command -v apt-get >/dev/null 2>&1 || \
			(echo >&2 "$(RED)Command 'apt-get' could not be found!$(NOCOLOR)"; exit 1)
	# Aptfile can be omited if empty
	@[[ ! -f "$(CURDIR)/Aptfile" ]] || \
	    ([[ $$(dpkg -l | grep -wcf $(CURDIR)/Aptfile) -eq $$(cat $(CURDIR)/Aptfile | wc -l) ]] || \
		(sudo -E apt-get update && \
		sudo -E apt-get -yq --no-install-suggests --no-install-recommends $(travis_apt_get_options) install \
			`cat $(CURDIR)/Aptfile`))
	@echo
	@echo "$(GREEN)2/5 Needed packages are successfully installed!$(NOCOLOR)"
	@echo
.PHONY: install-dep-packages

venv:
	@echo "Creating virtualenv in $(VENVDIR)...$(NOCOLOR)"
	@rm -rf $(VENVDIR)
	@$(PYTHON) -m venv $(VENVDIR)
	@$(VENVPIP) install wheel
	@$(VENVPIP) install -r requirements-dev.txt
	@echo
	@echo "$(GREEN)1/5 Virtualenv is successfully created!$(NOCOLOR)"
	@echo
.PHONY: venv

build: install-dep-packages venv __extra-deps
	@echo "Building package..."
	@[[ -z $$(compgen -G "dist/*.whl") && -z $$(compgen -G "dist/*.tar.gz") ]] || \
		(echo -e "$(RED)dist/*.whl dist/*.tar.gz files exists.\nPlease use 'make clean' before build!$(NOCOLOR)"; \
		exit 1)
	@$(VENVPYTHON) setup.py sdist bdist_wheel
	@echo
	@echo "$(GREEN)3/5 Package $(MODULE) is successfully built!$(NOCOLOR)"
	@echo
.PHONY: build

install: build
	@echo "Installing package to user..."
	$(VENVPIP) install --upgrade dist/*.whl
	@echo
	@echo "$(GREEN)4/5 Package $(MODULE) is successfully installed!$(NOCOLOR)"
	@echo
.PHONY: install

test:
	@echo "Running tests..."
	@[[ $$(compgen -G "$(CURDIR)/tests/inputs/*.in") ]] || (echo "$(RED)No input testfiles found!$(NOCOLOR)"; exit 1)
	r=0; \
	for test_input in $(CURDIR)/tests/inputs/*.in; do \
		test_output=$(CURDIR)/tests/outputs/$$(basename $${test_input%in}out) ; \
		echo; \
		time (cd /tmp && $(VENVPYTHON) -m $(MODULE) $(MODULE_PARAMS) -i $${test_input} | sed "s/	$$/	./" | \
		diff -sy --suppress-common-lines - $${test_output} 2>&1 | head -n100) || r=$($$r+$$?); \
	done; \
	[[ $$r == 0 ]] && echo && echo "$(GREEN)5/5 The test was completed successfully!$(NOCOLOR)" && echo || exit $$r
	@echo "Comparing GIT TAG (\"$(TRAVIS_TAG)\") with package version (\"v$(OLDVER)\")..."
	@[[ "$(TRAVIS_TAG)" == "v$(OLDVER)" || "$(TRAVIS_TAG)" == "" ]] && \
	  echo "$(GREEN)OK!$(NOCOLOR)" || \
	  (echo "$(RED)Versions do not match!$(NOCOLOR)"; exit 1)
.PHONY: test

uninstall:
	@echo "Uninstalling..."
	@[[ ! -d "$(VENVDIR)" || -z $$($(VENVPIP) list | grep -w $(MODULE)) ]] || $(VENVPIP) uninstall -y $(MODULE)
	@echo "$(GREEN)Package $(MODULE) was uninstalled successfully!$(NOCOLOR)"
.PHONY: uninstall

clean: __clean-extra-deps
	@rm -rf $(VENVDIR) dist/ build/ $(MODULE).egg-info/
.PHONY: clean

# Do actual release with new version. Originally from: https://github.com/mittelholcz/contextfun
release-major:
	@make -s __release NEWVER=$(NEWMAJORVER)
.PHONY: release-major

release-minor:
	@make -s __release NEWVER=$(NEWMINORVER)
.PHONY: release-minor

release-patch:
	@make -s __release NEWVER=$(NEWPATCHVER)
.PHONY: release-patch

__release:
	@[[ ! -z "$(NEWVER)" ]] || \
		(echo -e "$(RED)Do not call this target!\nUse 'release-major', 'release-minor' or 'release-patch'!$(NOCOLOR)"; \
		 exit 1)
	@[[ -z $$(git status --porcelain) ]] || (echo "$(RED)Working dir is dirty!$(NOCOLOR)"; exit 1)
	@echo "NEW VERSION: $(NEWVER)"
	# Clean install, test and tidy up
	@make clean uninstall install test uninstall clean
	@sed -i -r "s/__version__ = '$(OLDVER)'/__version__ = '$(NEWVER)'/" $(MODULE)/version.py
	@git add $(MODULE)/version.py
	@git commit -m "Release $(NEWVER)"
	@git tag -a "v$(NEWVER)" -m "Release $(NEWVER)"
	@git push
	@git push --tags
.PHONY: __release

# ===== emCompound-specific part

MODULE=emCompound

FILE=11341_prev
INFILE=tests/inputs/$(FILE).in
OUTFILE=tests/outputs/$(FILE).out

analyse_compounds:
	cat $(INFILE) | python3 $(MODULE) | sed "s/	$$/	./" > $(OUTFILE)
# using a sed hack for patch xtsv
# not to strip empty fields at the end of line.PHONY: connect_preverbs connect_preverbs_withcompound evaluate
.PHONY: analyse_compounds
