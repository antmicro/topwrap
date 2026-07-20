# Copyright (c) 2023-2026 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import logging
import socket
import threading
from itertools import chain
from pathlib import Path
from typing import List

import pytest

import topwrap.cli.main  # noqa: F401
from topwrap.backend.yaml.interface import InterfaceDefinitionDescriptionBackend
from topwrap.cli import cli
from topwrap.frontend.ipxact.frontend import IpXactFrontend
from topwrap.util import get_config

pytest_plugins = "tests.tests_ir.frontend.test_automatic"


def run_cli(*tokens: str, exit_on_error: bool = True):
    return cli.meta(list(tokens), result_action="return_value", exit_on_error=exit_on_error)


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

    def test_top_level_command(self, tmpdir: Path):
        # Using `topwrap specification` because it's a dummy command option-wise
        repo = Path(tmpdir) / "this_could_be_a_repo" / "cores"
        repo.mkdir(parents=True)
        run_cli(
            "--log-level",
            "DEBUG",
            "--repo",
            str(repo.parent),
            "specification",
            "-o",
            str(tmpdir / "out"),
        )
        assert logging.getLevelName(logging.getLogger().level) == "DEBUG"
        assert "this_could_be_a_repo" in get_config().repositories
        # Removing invalid repo so other tests won't be affected by it
        del get_config().repositories["this_could_be_a_repo"]

    def test_build_main(self, build_design_yaml: Path, tmp_path: Path):
        run_cli("build", "-d", str(build_design_yaml), "-b", str(tmp_path))
        assert Path(tmp_path / "top.sv").exists()

    def test_main_handle_validation_exception(self):
        with pytest.raises(SystemExit) as exc_info:
            run_cli("build", "-d", "./tests/test_cli/sample_design.yaml")
        assert exc_info.value.code == 1

    def create_socket_client(self, sock: socket.socket, exit: threading.Event):
        sock.listen(1)
        sock.settimeout(0.5)
        while True:
            if exit.is_set():
                return True
            try:
                connection, client_address = sock.accept()
                break
            except socket.timeout:
                pass
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
            socket_exit = threading.Event()
            future = executor.submit(self.create_socket_client, sock, socket_exit)

            try:
                run_cli(
                    "gui",
                    "--server-host",
                    server_addr,
                    "--server-port",
                    str(server_port),
                    "--no-use-server",
                    "--raise-exception",
                    exit_on_error=False,
                )
            except Exception as e:
                socket_exit.set()
                raise e
            assert future.result()

    def test_generate_kpm_spec(self, build_yaml_files: List[Path], tmp_path: Path):
        converted = tuple(map(lambda p: str(p), build_yaml_files))
        spec_path = Path(tmp_path / "gen_kpm_spec.json")
        assert not spec_path.exists(), "Specification to generate already exists"
        run_cli("specification", *converted, "-o", str(spec_path))
        assert spec_path.exists()

    def test_generate_kpm_design(self, build_yaml_files: List[Path], tmp_path: Path):
        converted = tuple(map(lambda p: str(p), build_yaml_files))
        design_path = Path(tmp_path / "gen_kpm_design.json")
        design_build = Path(f"{self.test_data_path}data_build/design.yaml")

        assert not design_path.exists(), "Design to generate already exists"

        run_cli("dataflow", *converted, "-d", str(design_build), "-o", str(design_path))
        assert design_path.exists()


class TestCleanCacheCli:
    @pytest.fixture()
    def git_cache_dir(self, tmpdir: Path, monkeypatch: pytest.MonkeyPatch):
        cache_dir = Path(tmpdir) / "git_cache"
        monkeypatch.setattr(topwrap.cli.main, "DEFAULT_GIT_CACHE_DIR", cache_dir)
        return cache_dir

    @pytest.fixture()
    def kpm_build_cache_dir(self, tmpdir: Path, monkeypatch: pytest.MonkeyPatch):
        from topwrap.config import config

        cache_dir = Path(tmpdir) / "kpm_build_cache"
        monkeypatch.setattr(config, "kpm_build_location", str(cache_dir))
        return cache_dir

    def test_clean_cache_empty(
        self,
        git_cache_dir: Path,
        kpm_build_cache_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ):
        with caplog.at_level(logging.INFO):
            run_cli("--log-level", "info", "clean-cache")

        assert "No 'git' cache found" in caplog.text
        assert "No 'kpm-build' cache found" in caplog.text
        assert not git_cache_dir.exists()
        assert not kpm_build_cache_dir.exists()

    def test_clean_cache_removes_all_by_default(
        self,
        git_cache_dir: Path,
        kpm_build_cache_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ):
        (git_cache_dir / "repo1").mkdir(parents=True)
        kpm_build_cache_dir.mkdir(parents=True)

        with caplog.at_level(logging.INFO):
            run_cli("--log-level", "info", "clean-cache")

        assert "Removed 'git' cache" in caplog.text
        assert "Removed 'kpm-build' cache" in caplog.text
        assert not git_cache_dir.exists()
        assert not kpm_build_cache_dir.exists()

    def test_clean_cache_removes_only_selected_target(
        self,
        git_cache_dir: Path,
        kpm_build_cache_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ):
        (git_cache_dir / "repo1").mkdir(parents=True)
        kpm_build_cache_dir.mkdir(parents=True)

        with caplog.at_level(logging.INFO):
            run_cli("--log-level", "info", "clean-cache", "--target", "git")

        assert "Removed 'git' cache" in caplog.text
        assert not git_cache_dir.exists()
        assert kpm_build_cache_dir.exists()

    def test_clean_cache_removes_all_explicitly(
        self,
        git_cache_dir: Path,
        kpm_build_cache_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ):
        (git_cache_dir / "repo1").mkdir(parents=True)
        kpm_build_cache_dir.mkdir(parents=True)

        with caplog.at_level(logging.INFO):
            run_cli("--log-level", "info", "clean-cache", "--target", "all")

        assert "Removed 'git' cache" in caplog.text
        assert "Removed 'kpm-build' cache" in caplog.text
        assert not git_cache_dir.exists()
        assert not kpm_build_cache_dir.exists()


class TestRepoCli:
    def test_repo_init(self, tmpdir: Path):
        tmpdir = Path(tmpdir)
        path = tmpdir / "repos" / "repo_directory"

        run_cli("repo", "init", "--no-config-update", "name_repo", str(path))

        assert path.exists()
        assert list(path.iterdir()) == []

    def test_repo_init_add_to_config(self, tmpdir: Path):
        tmpdir = Path(tmpdir)

        with pytest.MonkeyPatch().context() as ctx:
            ctx.chdir(tmpdir)
            path = tmpdir / "repos" / "repo_directory"
            assert not Path("topwrap.yaml").exists()
            run_cli("repo", "init", "name_repo", str(path))
            content: str = f"repositories:\n  name_repo: file:{str(path.relative_to(tmpdir))}\n"
            assert Path("topwrap.yaml").read_text() == content

            path = tmpdir / "repos" / "another_repo"
            run_cli("repo", "init", "repo2", str(path))
            assert (
                Path("topwrap.yaml").read_text()
                == content + f"  repo2: file:{str(path.relative_to(tmpdir))}\n"
            )

    def test_repo_init_existing_dir(self, tmpdir: Path, caplog: pytest.LogCaptureFixture):
        tmpdir = Path(tmpdir)
        (tmpdir / "hello.file").write_text("I am a file")

        run_cli("repo", "init", "name", str(tmpdir))

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

    def invoke_parse(self, repo_path: Path, *args: str) -> list[str]:
        repo_path.mkdir(parents=True)
        arg_list = ["--repo", str(repo_path), "repo", "parse", repo_path.name]
        arg_list.extend(list(args))
        run_cli(*arg_list)
        return [str(f).split("/")[7] for f in repo_path.glob("cores/**/module.yaml")]

    def test_repo_parse_minimal(self, all_sources: tuple[set[str], list[Path]], tmpdir: Path):
        mods_in_srcs, sources = all_sources

        # TODO: Remove when IPCoreYamlBackend starts supporting multiple dim bit vectors
        sources_str = set()
        for s in sources:
            if "string_sequencer" in str(s):
                continue
            sources_str.add(str(s))
        mods_in_srcs.remove("string_sequencer")

        repo_path = Path(tmpdir) / "repo_parse_norm"
        cores = self.invoke_parse(
            repo_path,
            "--exists-strategy",
            "overwrite",
            *(sources_str),
        )
        assert set(cores) == mods_in_srcs

    def test_repo_parse_with_duplicate(
        self,
        all_sources: tuple[set[str], list[Path]],
        tmpdir: Path,
        caplog: pytest.LogCaptureFixture,
    ):
        _, sources = all_sources

        repo_path = Path(tmpdir) / "repo_parse_norm"
        self.invoke_parse(repo_path, *(str(p) for p in sources))

        for _, level, message in caplog.record_tuples:
            if level == logging.ERROR and '"top" already exists' in message:
                break
        else:
            raise AssertionError("Expected resource already exists error")

        assert list(repo_path.glob("**/*")) == []

    def test_repo_parse_module_filtering(
        self,
        all_sources: tuple[set[str], list[Path]],
        tmpdir: Path,
    ):
        _, sources = all_sources
        only_mods = {"advanced_top", "SUB"}

        repo_path = Path(tmpdir) / "repo_parse_norm"
        cores = self.invoke_parse(
            repo_path,
            *chain(*(("-m", m) for m in only_mods)),
            *(str(p) for p in sources),
        )

        assert set(cores) == only_mods

    def test_repo_parse_custom_correct_frontend(
        self,
        sv_sources: list[Path],
        tmpdir: Path,
    ):
        repo_path = Path(tmpdir) / "repo_parse_norm"

        # TODO: Remove when IPCoreYamlBackend starts supporting multiple dim bit vectors
        sources = []
        for s in sv_sources:
            if "string_sequencer" in str(s):
                continue
            sources.append(s)

        cores = self.invoke_parse(
            repo_path,
            "--frontend",
            "systemverilog",
            *(str(p) for p in sources),
        )

        assert cores != []

    def test_repo_parse_ipxact_iface_from_repo(self, tmpdir: Path):
        repo_path = Path(tmpdir) / "ipxact_repo"

        iface_yaml = (
            IpXactFrontend()
            .parse_files(
                [Path("examples/ir_examples/interface/ipxact/amba.com/AMBA4/axi4stream.xml")]
            )
            .interfaces[0]
        )
        ifaces_dir = repo_path / "interfaces"
        ifaces_dir.mkdir(parents=True)
        InterfaceDefinitionDescriptionBackend().represent(iface_yaml).save(
            ifaces_dir / f"{iface_yaml.id.combined()}.yaml"
        )

        get_config().__dict__.pop("loaded_repos", None)
        try:
            run_cli(
                "--repo",
                str(repo_path),
                "repo",
                "parse",
                "--exists-strategy",
                "overwrite",
                repo_path.name,
                str(
                    Path(
                        "examples/ir_examples/interface/ipxact/antmicro.com/interface"
                        "/receiver/1.0/receiver.1.0.xml"
                    )
                ),
            )
            assert (repo_path / "cores" / "receiver" / "module.yaml").exists()
        finally:
            del get_config().repositories[repo_path.name]
            get_config().__dict__.pop("loaded_repos", None)
