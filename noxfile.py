# Copyright (c) 2023-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import nox


@nox.session()
def pre_commit(session: nox.Session) -> None:
    session.run("pre-commit", "install")
    session.run("pre-commit", "run", "--all-files")


@nox.session()
def isort(session: nox.Session) -> None:
    """Options are defined in pyproject.toml file"""
    session.install(".[lint]")
    session.run("isort", ".")


@nox.session()
def isort_check(session: nox.Session) -> None:
    """Options are defined in pyproject.toml file"""
    session.install(".[lint]")
    session.run("isort", "--check", ".")


@nox.session
def flake8(session):
    """Options are defined in .flake8 file."""
    session.install(".[lint]")
    session.run("flake8", ".")


@nox.session
def black(session):
    """Options are defined in pyproject.toml file"""
    session.install(".[lint]")
    session.run("black", ".")


@nox.session
def black_check(session):
    """Options are defined in pyproject.toml file"""
    session.install(".[lint]")
    session.run("black", "--check", ".")


@nox.session
def tests(session: nox.Session) -> None:
    session.install(".[tests,topwrap-parse]")
    session.run("pytest", "--cov=fpga_topwrap", "tests")


@nox.session
def tests_with_report(session: nox.Session) -> None:
    session.install(".[tests,topwrap-parse]")
    session.run("pytest", "--cov-report", "html:cov_html", "--cov=fpga_topwrap", "tests")
