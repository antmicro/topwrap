# Copyright (c) 2023-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import logging
import socket
from itertools import chain
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from topwrap.cli.main import (
    build_main,
    generate_kpm_design,
    generate_kpm_spec,
    main,
    topwrap_gui,
)
from topwrap.repo.user_repo import Core
from topwrap.util import get_config

pytest_plugins = "tests.tests_ir.frontend.test_automatic"


@pytest.fixture
def runner():
    return CliRunner()


class TestCli:
    test_data_path = "tests/data/"

    @pytest.fixture
    def build_yaml_files(self):
        return [
            Path(f"{self.test_data_path}data_build/DMATop.yaml"),
            Path(f"{self.test_data_path}data_build/axi_dispctrl_v1_0.yaml"),
        ]

    @pytest.fixture
    def build_design_yaml(self):
        return Path(self.test_data_path + "data_build/design.yaml")

    def test_top_level_command(self, runner: CliRunner, tmpdir: Path):
        # Using `topwrap specification` because it's a dummy command option-wise
        repo = Path(tmpdir) / "this_could_be_a_repo" / "cores"
        repo.mkdir(parents=True)
        runner.invoke(
            main,
            [
                "--log-level",
                "DEBUG",
                "--repo",
                str(repo.parent),
                "specification",
                "-o",
                str(tmpdir / "out"),
            ],
        )
        assert logging.getLevelName(logging.getLogger().level) == "DEBUG"
        assert "this_could_be_a_repo" in get_config().repositories

    def test_build_main(self, build_design_yaml: Path, tmp_path: Path):
        with click.Context(build_main) as ctx:
            ctx.invoke(
                build_main,
                design=build_design_yaml,
                build_dir=tmp_path,
            )
        assert Path(tmp_path / "top.sv").exists()

    def create_socket_client(self, sock: socket.socket):
        sock.listen(1)

        connection, client_address = sock.accept()
        logging.info(f"Client connected: {client_address}")
        connection.close()
        sock.shutdown(socket.SHUT_WR)  # Send FIN(finish) packet
        sock.close()
        return True

    def test_kpm_gui_cli(self):
        server_addr = "127.0.0.1"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((server_addr, 0))  # Bind to port picked by OS
        server_port = sock.getsockname()[1]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.create_socket_client, sock)
            with click.Context(topwrap_gui) as ctx:
                ctx.invoke(
                    topwrap_gui, server_host=server_addr, server_port=server_port, use_server=False
                )
            assert future.result()

    def test_generate_kpm_spec(self, build_yaml_files, tmp_path):
        spec_path = Path(tmp_path / "gen_kpm_spec.json")
        assert not spec_path.exists(), "Specification to generate already exists"
        with click.Context(generate_kpm_spec) as ctx:
            ctx.invoke(generate_kpm_spec, output=spec_path, files=build_yaml_files)
        assert spec_path.exists()

    def test_generate_kpm_design(self, build_yaml_files, tmp_path):
        design_path = Path(tmp_path / "gen_kpm_design.json")
        design_build = Path(f"{self.test_data_path}data_build/design.yaml")

        assert not design_path.exists(), "Design to generate already exists"

        with click.Context(generate_kpm_design) as ctx:
            ctx.invoke(
                generate_kpm_design,
                output=design_path,
                files=build_yaml_files,
                design=design_build,
            )
        assert design_path.exists()


class TestRepoCli:
    def test_repo_init(self, runner: CliRunner, tmpdir):
        tmpdir = Path(tmpdir)
        path = tmpdir / "repos" / "repo_directory"

        runner.invoke(main, ["repo", "init", "--no-config-update", "name_repo", str(path)])

        assert path.exists()
        assert list(path.iterdir()) == []

    def test_repo_init_add_to_config(self, runner: CliRunner, tmpdir):
        tmpdir = Path(tmpdir)

        with pytest.MonkeyPatch().context() as ctx:
            ctx.chdir(tmpdir)
            path = tmpdir / "repos" / "repo_directory"
            assert not Path("topwrap.yaml").exists()
            runner.invoke(main, ["repo", "init", "name_repo", str(path)])
            content: str = f"repositories:\n  name_repo: file:{str(path.relative_to(tmpdir))}\n"
            assert Path("topwrap.yaml").read_text() == content

            path = tmpdir / "repos" / "another_repo"
            runner.invoke(main, ["repo", "init", "repo2", str(path)])
            assert (
                Path("topwrap.yaml").read_text()
                == content + f"  repo2: file:{str(path.relative_to(tmpdir))}\n"
            )

    def test_repo_init_existing_dir(
        self, runner: CliRunner, tmpdir, caplog: pytest.LogCaptureFixture
    ):
        tmpdir = Path(tmpdir)
        (tmpdir / "hello.file").write_text("I am a file")

        runner.invoke(main, ["repo", "init", "name", str(tmpdir)])

        for _, level, message in caplog.record_tuples:
            if level == logging.ERROR and "not empty" in message:
                break
        else:
            raise AssertionError("Repo created in a nonempty directory")

    @pytest.fixture
    def all_sources(
        self,
        sv_sources: list[Path],
        kpm_sources: list[Path],
        yaml_sources: list[Path],
    ):
        mods_in_srcs = {
            "advanced_top", "axi_dispctrl_v1_0", "BETWEEN", "char_processor", "c_mod_2",
            "DMATop", "s1_mod_2", "s1_mod_3", "s2_mod_1", "s2_mod_2", "seq_to_sci4_bridge",
            "string_sequencer", "SUB", "SUBEMPTY", "top"
        }  # fmt: skip

        return (mods_in_srcs, sv_sources + kpm_sources + yaml_sources)

    def invoke_parse(self, repo_path: Path, runner: CliRunner, *args: str) -> list[Core]:
        repo_path.mkdir(parents=True)
        runner.invoke(main, ("--repo", str(repo_path), "repo", "parse", repo_path.name) + args)
        cores = list(repo_path.glob("cores/*/.core.yaml"))
        return [Core.load(p) for p in cores]

    def test_repo_parse_minimal(
        self, all_sources: tuple[set[str], list[Path]], tmpdir: Path, runner: CliRunner
    ):
        mods_in_srcs, sources = all_sources

        repo_path = Path(tmpdir) / "repo_parse_norm"
        cores = self.invoke_parse(
            repo_path,
            runner,
            "--exists-strategy",
            "overwrite",
            *(str(p) for p in sources),
        )
        assert {c.top_level_name for c in cores} == mods_in_srcs

    def test_repo_parse_with_duplicate(
        self,
        all_sources: tuple[set[str], list[Path]],
        tmpdir: Path,
        runner: CliRunner,
        caplog: pytest.LogCaptureFixture,
    ):
        _, sources = all_sources

        repo_path = Path(tmpdir) / "repo_parse_norm"
        self.invoke_parse(repo_path, runner, *(str(p) for p in sources))

        for _, level, message in caplog.record_tuples:
            if level == logging.ERROR and '"top" already exists' in message:
                break
        else:
            raise AssertionError("Expected resource already exists error")

        assert list(repo_path.glob("**/*")) == []

    def test_repo_parse_all_sources(
        self, all_sources: tuple[set[str], list[Path]], tmpdir: Path, runner: CliRunner
    ):
        mod_names, sources = all_sources

        repo_path = Path(tmpdir) / "repo_parse_norm"
        cores = self.invoke_parse(
            repo_path,
            runner,
            "--all-sources",
            "--exists-strategy",
            "overwrite",
            *(str(p) for p in sources),
        )

        assert len(list(repo_path.glob("cores/*/srcs/**/*"))) == len(sources) * len(mod_names)

        for core in cores:
            assert len(core.sources) == len(sources)

    def test_repo_parse_module_filtering(
        self, all_sources: tuple[set[str], list[Path]], tmpdir: Path, runner: CliRunner
    ):
        _, sources = all_sources
        only_mods = {"advanced_top", "SUB"}

        repo_path = Path(tmpdir) / "repo_parse_norm"
        cores = self.invoke_parse(
            repo_path,
            runner,
            *chain(*(("-m", m) for m in only_mods)),
            *(str(p) for p in sources),
        )

        assert {c.top_level_name for c in cores} == only_mods

    def test_repo_parse_by_ref(
        self, all_sources: tuple[set[str], list[Path]], tmpdir: Path, runner: CliRunner
    ):
        mod_names, sources = all_sources

        repo_path = Path(tmpdir) / "repo_parse_norm"
        cores = self.invoke_parse(
            repo_path,
            runner,
            "--reference",
            "--all-sources",
            "--exists-strategy",
            "overwrite",
            *(str(p) for p in sources),
        )

        assert list(repo_path.glob("cores/*/srcs/**/*")) == []

        for core in cores:
            assert len(core.sources) == len(sources)

    def test_repo_parse_custom_correct_frontend(
        self,
        sv_sources: list[Path],
        tmpdir: Path,
        runner: CliRunner,
    ):
        repo_path = Path(tmpdir) / "repo_parse_norm"

        cores = self.invoke_parse(
            repo_path,
            runner,
            "--frontend",
            "systemverilog",
            *(str(p) for p in sv_sources),
        )
        assert cores != []
