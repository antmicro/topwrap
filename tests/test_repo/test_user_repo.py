# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import tempfile
from pathlib import Path
from typing import IO, cast

import pytest

from topwrap.config import config
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.repo.exceptions import TopLevelNotFoundException
from topwrap.repo.file_handlers import CoreFileHandler, InterfaceFileHandler
from topwrap.repo.files import File, LocalFile
from topwrap.repo.user_repo import (
    Core,
    CoreHandler,
    InterfaceDescription,
    InterfaceDescriptionHandler,
    ResourcePathWithType,
    UserRepo,
)
from topwrap.resource_field import FileReferenceHandler


@pytest.fixture()
def verilog_modules() -> tuple[list[str], list[str]]:
    MODULE_NAMES = ["myor", "myand", "mydep1", "mydep2", "mytop"]
    CONTENTS = [
        """
module myand(input wire a, input wire b, output wire c);
    assign c = a & b;
endmodule

module myor(input wire a, input wire b, output wire c);
    assign c = a | b;
endmodule
""",
        """
module mydep1(input wire a);
    myand subdep(.a(a), .b(), .c());
    myor subdep2(.a(), .b(), .c());
    missing_dep subdep3();
endmodule

module mydep2(input wire a);
    mydep1 dep(.a(a));
endmodule
""",
        """
module mytop(input wire a);
    mydep1 dep(.a(a));
    mydep2 dep2(.a(a));
endmodule
""",
    ]
    return (MODULE_NAMES, CONTENTS)


@pytest.fixture
def saved_modules(verilog_modules: tuple[list[str], list[str]]):
    _, content = verilog_modules
    files = list[IO[str]]()
    for cnt_file in content:
        f = tempfile.NamedTemporaryFile("w", suffix="_verilog.v")
        f.write(cnt_file)
        f.flush()
        files.append(f)

    yield [LocalFile(Path(f.name)) for f in files]


@pytest.fixture
def saved_cores(saved_modules: list[File]):
    return CoreFileHandler(saved_modules, all_sources=True).parse()


@pytest.fixture()
def iface_desc():
    return """
name: MyInterface
port_prefix: my
signals:
    required:
        - sig1
        - sig2
    optional:
        - opt1
"""


@pytest.fixture
def cores(fs, request, num_cores=2) -> dict[str, Core]:
    cores = {}
    for i in range(num_cores):
        additional_path = ""
        if hasattr(request, "param"):
            additional_path = request.param[i]
        mod_name = f"{additional_path}mymod_{i}"
        verilog_file = Path(f"{mod_name}.v")

        fs.create_file(verilog_file)
        core = Core(
            verilog_file.stem,
            mod_name,
            [
                ResourcePathWithType(
                    FileReferenceHandler(verilog_file), SystemVerilogFrontend().metadata.name
                )
            ],
        )
        cores[core.name] = core
    return cores


@pytest.fixture
def ifaces(fs, num_ifaces=2, iface_path="example/path/"):
    ifaces = []
    for i in range(num_ifaces):
        iface_name = f"{iface_path}iface_{i}"
        iface_file = Path(f"{iface_name}.yaml")

        fs.create_file(iface_file)
        iface = InterfaceDescription(iface_name, LocalFile(iface_file))
        ifaces.append(iface)
    return ifaces


class TestCoreResouce:
    def test_load_ir_module(
        self, verilog_modules: tuple[list[str], list[str]], saved_cores: list[Core]
    ):
        names, _ = verilog_modules

        for core in saved_cores:
            loaded = core.ir_module
            assert loaded.top_level.id.name == core.name
            assert [*loaded.unknown_sources] == []
            assert len([*loaded.other_sources]) == len(names) - 1

    def test_load_no_top(self, saved_cores: list[Core]):
        for core in saved_cores:
            with pytest.MonkeyPatch().context() as ctx:
                ctx.setattr(core, "top_level_name", "I DON'T EXIST")
                with pytest.raises(TopLevelNotFoundException):
                    _ = core.ir_module


class TestCoreHandler:
    def test_save(self, fs, cores: dict[str, Core]):
        repo_dir = Path("myrepo")
        fs.create_dir(repo_dir)

        core_handler = CoreHandler()
        for core in cores.values():
            core_handler.save(core, repo_dir)

        paths = repo_dir.glob("**/*")
        EXPECTED_PATHS = [
            "myrepo/cores",
            "myrepo/cores/mymod_0",
            "myrepo/cores/mymod_0/srcs",
            "myrepo/cores/mymod_0/mymod_0.yaml",
            "myrepo/cores/mymod_0/srcs/mymod_0.v",
            "myrepo/cores/mymod_1",
            "myrepo/cores/mymod_1/srcs",
            "myrepo/cores/mymod_1/mymod_1.yaml",
            "myrepo/cores/mymod_1/srcs/mymod_1.v",
        ]

        assert len(list(paths)) == len(EXPECTED_PATHS), (
            "The repository has an unexpected number of files"
        )
        for path in paths:
            assert path in EXPECTED_PATHS, "The repository contains unexpected paths"

    @pytest.fixture
    def saved_repo(self, tmpdir: Path, saved_modules: list[File]):
        repo = UserRepo("repo")
        repo.add_files(CoreFileHandler(saved_modules, all_sources=True))
        repo.save(Path(tmpdir))
        yield Path(tmpdir)

    def test_save_by_ref(
        self, saved_cores: list[Core], verilog_modules: tuple[list[str], list[str]]
    ):
        _, v_files = verilog_modules

        with tempfile.TemporaryDirectory() as tmpdir:
            hand = CoreHandler()
            for core in saved_cores:
                hand.save(core, Path(tmpdir))
            assert len(list(Path(tmpdir).glob("cores/*/srcs/*"))) == len(v_files) * len(saved_cores)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.MonkeyPatch().context() as ctx:
                hand = CoreHandler()
                for core in saved_cores:
                    ctx.setattr(core, "by_ref", True)
                    hand.save(core, Path(tmpdir))
                assert len(list(Path(tmpdir).glob("cores/*/srcs/*"))) == 0

    def test_load(self, saved_repo: Path, saved_cores: list[Core]):
        [*load_cores] = CoreHandler().load(saved_repo)

        for org_core in saved_cores:
            for core in load_cores:
                if org_core.name == core.name:
                    for core_file in org_core.sources:
                        assert isinstance(core_file, FileReferenceHandler)
                        for repo_file in core.sources:
                            assert isinstance(repo_file, FileReferenceHandler)
                            if core_file.to_path().read_text() == repo_file.to_path().read_text():
                                break
                        else:
                            raise AssertionError("Files differ")
                    break
            else:
                raise AssertionError(f"Core {org_core.name} not found")

    def test_builtins(self):
        repo = config.builtin_repo
        assert len(repo.get_resources(Core)) == 5


class TestInterfaceDescriptionHandler:
    def test_save(self, fs, ifaces):
        repo_dir = Path("myrepo")
        fs.create_dir(repo_dir)

        iface_handler = InterfaceDescriptionHandler()
        for iface in ifaces:
            iface_handler.save(iface, repo_dir)

        paths = repo_dir.glob("**/*")
        EXPECTED_PATHS = [
            "myrepo/interfaces",
            "myrepo/interfaces/iface_0.yaml",
            "myrepo/interfaces/iface_1.yaml",
        ]

        assert len(list(paths)) == len(EXPECTED_PATHS), (
            "The repository has incorrect number of files"
        )
        for path in paths:
            assert path in EXPECTED_PATHS, "The repository contains unexpected paths"

    @pytest.fixture
    def repo_with_ifaces(self, fs, num_cores=2, repo_name="myrepo"):
        ifaces = {}
        for i in range(num_cores):
            interfaces_dir = Path(repo_name, "interfaces")
            iface_name = f"mymod_{i}"
            iface_file = interfaces_dir / f"{iface_name}.yaml"

            fs.create_file(iface_file)
            iface = InterfaceDescription(iface_name, LocalFile(iface_file))
            ifaces[iface_name] = iface
        return (Path(repo_name), ifaces)

    @pytest.mark.usefixtures("fs")
    def test_load(self, repo_with_ifaces):
        (repo, repo_ifaces) = repo_with_ifaces
        load_ifaces = InterfaceDescriptionHandler().load(repo)
        for iface in load_ifaces:
            assert iface.name in repo_ifaces, "A InterfaceDescription not found in the repository"
            repo_iface = repo_ifaces[iface.name]
            assert iface.file.path == repo_iface.file.path, "Paths to interface differ"


class TestCoreFileHandler:
    @staticmethod
    def contains_warnings_in_log(caplog, contains: str):
        for name, level, msg in caplog.record_tuples:
            if (
                name == "topwrap.repo.file_handlers"
                and level == logging.WARNING
                and msg.find(contains) > -1
            ):
                return True
        return False

    def test_parse_with_auto_deps(
        self, verilog_modules: tuple[list[str], list[str]], saved_modules: list[File]
    ):
        cores = CoreFileHandler(saved_modules, all_sources=False).parse()
        names, _ = verilog_modules

        assert len(cores) == len(names)

        for core in cast(list[Core], cores):
            # We won't have proper dependency gathering without
            # design parsing support in SV frontend
            assert len(core.sources) == 1

    def test_parse_with_tops_filtering(
        self, verilog_modules: tuple[list[str], list[str]], saved_modules: list[File]
    ):
        _, v_files = verilog_modules

        cores = CoreFileHandler(saved_modules, tops=["mytop"]).parse()
        cores_all = CoreFileHandler(saved_modules, tops=["mytop"], all_sources=True).parse()

        assert len(cores) == len(cores_all) == 1

        [mytop] = cast(list[Core], cores)
        [mytop_all] = cast(list[Core], cores_all)

        assert mytop.top_level_name == mytop_all.top_level_name == "mytop"
        assert len(mytop.sources) == 1
        assert len(mytop_all.sources) == len(v_files)


class TestInterfaceFileHandler:
    def test_parse(self, fs, iface_desc):
        my_interface = Path("my_interface.yaml")
        fs.create_file(my_interface.name, contents=iface_desc)

        handler = InterfaceFileHandler([LocalFile(my_interface)])
        resources = handler.parse()
        assert len(resources) == 1, "Should have 1 resources (InterfaceDescription)"


class TestUserRepo:
    @pytest.fixture
    def demo_user_repo(self, cores, ifaces):
        demo_user_repo = UserRepo("demo")
        demo_user_repo.resources = {
            Core: cores,
            InterfaceDescription: {intf.name: intf for intf in ifaces},
        }
        return demo_user_repo

    def test_core_by_name(self, demo_user_repo: UserRepo):
        cor = demo_user_repo.get_core_by_name("mymod_1")
        assert cor is not None and cor.top_level_name == "mymod_1"
