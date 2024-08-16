#!/bin/bash
# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

set -e

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")"/../.. &>/dev/null && pwd)
EXAMPLES=(hdmi inout pwm soc hierarchy)

begin_command_group() {
    if [[ -n "${GITHUB_WORKFLOW:-}" ]]; then
        echo "::group::$*"
    else
        echo -e "\n\033[1;92mRunning step: $1\033[0m\n"
    fi
}

end_command_group() {
    if [[ -n "${GITHUB_WORKFLOW:-}" ]]; then
        echo "::endgroup::"
    fi
}

log_cmd() {
    printf '\033[1;96m'
    printf '%s ' "$*"
    printf '\033[0m\n'
    eval "$*"
}

install_common_system_packages() {
    begin_command_group "Install system packages"
    log_cmd apt-get update -qq
    log_cmd apt-get install -y --no-install-recommends \
        git \
        python3-dev \
        python3-pip \
        python3-venv
    end_command_group
}

enter_venv() {
    begin_command_group "Configure Python virtual environment"
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_cmd python3 -m venv venv
    fi
    log_cmd source venv/bin/activate
    end_command_group
}

install_topwrap_system_deps() {
    enter_venv

    begin_command_group "Installing topwrap dependencies"
    log_cmd apt-get install -y --no-install-recommends \
        g++ \
        make \
        antlr4 \
        libantlr4-runtime-dev \
        yosys
    end_command_group
}

install_interconnect_test_system_deps() {
    begin_command_group "Installing system packages for the interconnect test"
    log_cmd apt-get install -y --no-install-recommends \
        make \
        meson \
        ninja-build \
        gcc-riscv64-unknown-elf \
        bsdextrautils \
        verilator
    end_command_group
}

install_nox() {
    begin_command_group "Installing nox"
    enter_venv
    log_cmd pip3 install nox
    end_command_group
}

install_pyenv() {
    begin_command_group "Install pyenv"
    log_cmd apt-get install -y --no-install-recommends \
        curl \
        wget \
        libssl-dev \
        libreadline-dev \
        libffi-dev \
        libbz2-dev \
        libncurses-dev \
        libsqlite3-dev \
        liblzma-dev

    log_cmd export PYENV_ROOT="$HOME/.pyenv"
    log_cmd export PATH="$PYENV_ROOT/bin:$PATH"
    log_cmd "curl https://pyenv.run | bash"
    end_command_group
}


run_lint() {
    install_common_system_packages
    install_nox

    begin_command_group "Run lint checks"
    log_cmd nox -s test_lint
    end_command_group
}

run_tests() {
    install_common_system_packages
    install_topwrap_system_deps
    install_interconnect_test_system_deps
    install_nox
    install_pyenv

    begin_command_group "Run Python tests"
    log_cmd nox -s tests_in_env
    end_command_group
}

generate_examples() {
    install_common_system_packages
    install_topwrap_system_deps

    begin_command_group "Installing Topwrap"
    log_cmd pip install "."
    end_command_group

    for EXAMPLE in "${EXAMPLES[@]}"; do
        begin_command_group "Generate $EXAMPLE example"
        log_cmd pushd "$ROOT_DIR"/examples/"$EXAMPLE"
        log_cmd "tuttest README.md install-deps,generate | bash -"
        log_cmd popd
        end_command_group
    done
}


generate_docs() {
    install_common_system_packages
    begin_command_group "Install system packages for doc generation"
    log_cmd apt-get install -y texlive-full make
    end_command_group
    install_nox

    begin_command_group "Generating documentation"
    log_cmd nox -s doc_gen
    end_command_group
}


package_cores() {
    install_common_system_packages
    install_topwrap_system_deps

    begin_command_group "Install Topwrap with parsing dependencies"
    log_cmd pip install ".[topwrap-parse]"
    end_command_group

    begin_command_group "Package cores for release"
    log_cmd mkdir core_repo
    log_cmd pushd core_repo
    log_cmd python ../.github/scripts/package_cores.py
    log_cmd popd
    end_command_group
}

package_dist() {
    install_common_system_packages
    install_topwrap_system_deps
    install_nox

    begin_command_group "Build and test the topwrap package"
    log_cmd nox -s build
    end_command_group
}

case "$1" in
lint)
    run_lint
    ;;
tests)
    run_tests
    ;;
examples)
    generate_examples
    ;;
package_cores)
    package_cores
    ;;
package_dist)
    package_dist
    ;;
docs)
    generate_docs
    ;;
*)
    echo "Usage: $0 {lint|tests|examples|package_cores|package_dist|docs}"
    ;;
esac
