export PATH := x"$PATH:$HOME/.local/bin"

tested_python_versions := "3.10 3.11 3.12 3.13"

default:
	@just --list

[arg("docs",long,value="1")]
install-debian-deps docs="0":
    #!/usr/bin/env bash
    apt-get update -qq
    apt-get install -y --no-install-recommends \
        curl \
        git \
        python3-dev \
        python3-pip \
        python3-venv \
        nodejs \
        npm \
        g++ \
        make \
        antlr4 \
        libantlr4-runtime-dev \
        yosys

    # FIXME: Unpin Chromium once the issues with Chromium 150 running in headless mode are resolved.
    # Relevant Debian bug: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1141571
    if [[ {{docs}} == "1" ]];then apt-get install -y texlive-full imagemagick make chromium=147.0.7727.137-1~deb12u1 chromium-common=147.0.7727.137-1~deb12u1; fi

    curl -LsSf https://astral.sh/uv/install.sh | sh


# Run all checks intended for execution before committing code.
pre-commit:
	#!/usr/bin/env bash
	uv sync --extra lint
	uv run pre-commit install
	uv run pre-commit run --all-files

# Run all configured linting checks with correction.
lint:
	#!/usr/bin/env bash
	uv sync --extra lint
	uv run pre-commit run --all-files

# Run all configured linting checks.
test-lint:
	#!/usr/bin/env bash
	uv sync --extra lint
	source .venv/bin/activate
	uv run pre-commit run check-yaml-extension --all-files
	uv run ruff format --check
	uv run ruff check
	uv run codespell

# Run static type checking using Pyright.
[arg("compare",long,value="1")]
pyright compare="0":
	#!/usr/bin/env bash
	uv sync --extra tests
	if [[ {{compare}} == "1" ]];then uv run scripts/pyright_check.py --compare; else uv run scripts/pyright_check.py; fi

# Execute tests for a specific Python version.
test version="3.10":
	#!/usr/bin/env bash
	uv sync --python python{{version}} --extra tests
	uv run pytest \
		-rs \
		--cov-report html:cov_html \
		--cov=topwrap \
		--cov-config=pyproject.toml \
		tests

# Execute tests on every Python version supported in CI.
test-all-python-versions:
	#!/usr/bin/env bash
	set -e
	for version in {{tested_python_versions}}; do
		just test "$version"
	done

# Update generated dataflow or specification test data.
[arg("dataflow",long,value="1")]
[arg("specification",long,value="1")]
update-testdata dataflow="0" specification="0":
	#!/usr/bin/env bash
	uv sync --extra tests
	if [[ {{dataflow}} == "1" ]];then uv run tests/update_test_data.py --dataflow; fi
	if [[ {{specification}} == "1" ]];then uv run tests/update_test_data.py --specification; fi

# Run tests specific to the KPM server component.
test-kpm-server:
	#!/usr/bin/env bash
	uv run scripts/kpm_server_check.py

# Build the project.
build:
	#!/usr/bin/env bash
	uv sync --extra deploy
	uv run pyproject-build

# Create distributable packages.
package:
	#!/usr/bin/env bash
	uv sync --extra deploy
	source .venv/bin/activate
	uv run .github/scripts/package_cores.py ./build/export

# Run examples
examples:
    #!/usr/bin/env bash
    uv sync
    source .venv/bin/activate
    python3 -m ensurepip
    EXAMPLES=(constant hdmi inout pwm soc)
    for EXAMPLE in "${EXAMPLES[@]}"; do
        pushd "$PWD"/examples/"$EXAMPLE"
        make ci
        popd
    done

# Build docs
docs:
	#!/usr/bin/env bash
	npm install -g @mermaid-js/mermaid-cli

	uv sync --extra docs --extra tests
	source .venv/bin/activate

	shopt -s globstar
	mkdir -p docs/build/kpm_jsons

	for p in ./examples/**/Makefile; do
		if [[ $p == *"/Caliptra/"* ]]; then continue; fi
		DIR="$(dirname $p)"
		NAME=$(echo "$DIR" | sed 's/.\/examples\///' | sed 's/\//_/')
		cd $DIR
		make kpm_spec.json kpm_dataflow.json
		cd -
		mv "$DIR/kpm_spec.json" "docs/build/kpm_jsons/spec_$NAME.json"
		mv "$DIR/kpm_dataflow.json" "docs/build/kpm_jsons/data_$NAME.json"
	done

	make -C docs html
	make -C docs latexpdf
	cp docs/build/latex/topwrap.pdf docs/build/html
