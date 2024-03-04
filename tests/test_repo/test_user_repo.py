# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import tempfile
from pathlib import Path

import pytest

from topwrap.repo.files import LocalFile
from topwrap.repo.user_repo import (
    Core,
    CoreHandler,
    InterfaceDescription,
    InterfaceDescriptionHandler,
    InterfaceFileHandler,
    VerilogFileHandler,
)


@pytest.fixture()
def verilog_modules():
    MODULE_NAMES = ["myor", "myand"]
    CONTENTS = """
module myand(input wire a, input wire b, output wire c);
    assign c = a & b;
endmodule

module myor(input wire a, input wire b, output wire c);
    assign c = a | b;
endmodule
"""
    return (MODULE_NAMES, CONTENTS)


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


class TestCoreHandler:
    @pytest.fixture
    def cores(self, fs, num_cores=2):
        cores = []
        for i in range(num_cores):
            mod_name = f"mymod_{i}"
            verilog_file = f"{mod_name}.v"
            design_file = f"{mod_name}.yaml"

            fs.create_file(verilog_file)
            fs.create_file(design_file)
            core = Core(mod_name, LocalFile(design_file), [LocalFile(verilog_file)])
            cores.append(core)
        return cores

    def test_save(self, fs, cores):
        repo_dir = Path("myrepo")
        fs.create_dir(repo_dir)

        core_handler = CoreHandler()
        for core in cores:
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

        assert len(list(paths)) == len(
            EXPECTED_PATHS
        ), "The repository has incorrect number of files"
        for path in paths:
            assert path in EXPECTED_PATHS, "The repository contains unexpected paths"

    @pytest.fixture
    def repo_with_cores(self, fs, num_cores=2, repo_name="myrepo"):
        cores = {}
        for i in range(num_cores):
            mod_name = f"mymod_{i}"
            core_dir = Path(repo_name, "cores", mod_name)
            design_file = core_dir / f"{mod_name}.yaml"
            verilog_file = core_dir / "srcs" / f"{mod_name}.yaml"

            fs.create_file(design_file)
            fs.create_file(verilog_file)
            core = Core(mod_name, LocalFile(design_file), [LocalFile(verilog_file)])
            cores[mod_name] = core
        return (Path(repo_name), cores)

    @pytest.mark.usefixtures("fs")
    def test_load(self, repo_with_cores):
        (repo, repo_cores) = repo_with_cores
        load_cores = CoreHandler().load(repo)
        for core in load_cores:
            assert core.name in repo_cores, "A Core not found in the repository"
            repo_core = repo_cores[core.name]

            assert core.design.path == repo_core.design.path, "Paths to design description differ"
            assert len(core.files) == len(repo_core.files), "Number of files differ"

            core.files.sort()
            repo_core.files.sort()
            for core_file, repo_file in zip(core.files, repo_core.files):
                assert core_file.path == repo_file.path, "Paths to sources differ"


class TestInterfaceDescriptionHandler:
    @pytest.fixture
    def ifaces(self, fs, num_ifaces=2):
        ifaces = []
        for i in range(num_ifaces):
            iface_name = f"iface_{i}"
            iface_file = f"{iface_name}.yaml"

            fs.create_file(iface_file)
            iface = InterfaceDescription(iface_name, LocalFile(iface_file))
            ifaces.append(iface)
        return ifaces

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

        assert len(list(paths)) == len(
            EXPECTED_PATHS
        ), "The repository has incorrect number of files"
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


class TestVerilogFileHandler:
    def test_parse(self, verilog_modules):
        module_names, content = verilog_modules
        with tempfile.NamedTemporaryFile("w", suffix="_verilog.v") as f:
            f.write(content)
            f.flush()

            handler = VerilogFileHandler([LocalFile(f.name)])
            resources = handler.parse()

        assert len(resources) == 2, "Should have 2 resources (Core)"
        for resource in resources:
            assert resource.name in module_names, "Resource names differ"


class TestInterfaceFileHandler:
    def test_parse(self, fs, iface_desc):
        my_interface = Path("my_interface.yaml")
        fs.create_file(my_interface.name, contents=iface_desc)

        handler = InterfaceFileHandler([LocalFile(my_interface.name)])
        resources = handler.parse()
        assert len(resources) == 1, "Should have 1 resources (InterfaceDescription)"
