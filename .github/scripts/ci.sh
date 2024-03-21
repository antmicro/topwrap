#!/bin/bash
# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

set -e

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")"/../.. &>/dev/null && pwd)
EXAMPLES=(hdmi inout pwm)

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
        python3-pip \
        python3-venv
    end_command_group
}

install_pyenv() {
    begin_command_group "Install pyenv"
    log_cmd export PYENV_ROOT="$HOME/.pyenv"
    log_cmd export PATH="$PYENV_ROOT/bin:$PATH"
    log_cmd "curl https://pyenv.run | bash"
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

install_topwrap() {
    begin_command_group "Install Topwrap"
    log_cmd "tuttest README.md | bash -"
    end_command_group
}

run_lint() {
    install_common_system_packages
    enter_venv

    begin_command_group "Install python packages for lint"
    log_cmd pip install ".[lint]"
    end_command_group

    begin_command_group "Run lint checks"
    log_cmd nox -s test_lint
    end_command_group
}

run_tests() {
    install_common_system_packages

    begin_command_group "Install system packages for tests"
    log_cmd apt-get install -y --no-install-recommends \
        curl \
        wget \
        python3-dev \
        make \
        meson \
        ninja-build \
        gcc-riscv64-unknown-elf \
        bsdextrautils \
        verilator \
        libssl-dev \
        libreadline-dev \
        libffi-dev \
        libbz2-dev \
        libncurses-dev \
        libsqlite3-dev \
        liblzma-dev
    end_command_group

    install_pyenv
    enter_venv

    begin_command_group "Install python packages for tests"
    log_cmd pip install ".[tests]"
    log_cmd pip install git+https://github.com/antmicro/tuttest
    end_command_group

    install_topwrap

    begin_command_group "Run Python tests"
    log_cmd nox -s tests_in_env
    end_command_group
}

generate_examples() {
    install_common_system_packages
    begin_command_group "Install system packages for examples"
    log_cmd apt-get install -y --no-install-recommends python3-dev
    end_command_group
    enter_venv

    begin_command_group "Install python packages for examples"
    log_cmd pip install git+https://github.com/antmicro/tuttest
    end_command_group

    install_topwrap

    for EXAMPLE in "${EXAMPLES[@]}"; do
        begin_command_group "Generate $EXAMPLE example"
        log_cmd pushd "$ROOT_DIR"/examples/"$EXAMPLE"
        log_cmd "tuttest README.md install-deps,generate | bash -"
        log_cmd popd
        end_command_group
    done
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
*)
    echo "Usage: $0 {lint|tests|examples}"
    ;;
esac
