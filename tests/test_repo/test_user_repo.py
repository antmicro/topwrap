# Copyright (c) 2024-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from examples.ir_examples.modules import (
    adv_top,
    hier_top,
    intf_top,
    intr_top,
    inv_top,
    simp_top,
)
from topwrap.config import ConfigManager
from topwrap.model.connections import PortDirection
from topwrap.model.interface import InterfaceDefinition
from topwrap.model.misc import Identifier
from topwrap.model.module import Module
from topwrap.repo.user_repo import (
    Core,
    CoreHandler,
    InterfaceDefinitionResource,
    InterfaceDescriptionHandler,
    UserRepo,
)
from topwrap.util import get_config


@pytest.fixture()
def yaml_cores(fs) -> tuple[list[str], list[str], list[str]]:
    p = Path("tests/data/data_yaml/ipcore")
    fs.add_real_directory(p)
    CONTENTS = []
    NAMES = []
    FILES = []
    for file in p.glob("*.yaml"):
        CONTENTS.append(file.read_text())
        NAMES.append(file.stem)
        FILES.append(file)
    return (CONTENTS, NAMES, FILES)


@pytest.fixture()
def yaml_ifaces(fs) -> tuple[list[str], list[str], list[str]]:
    p = Path("tests/data/data_yaml/ifaces")
    fs.add_real_directory(p)
    CONTENTS = []
    NAMES = []
    FILES = []
    for file in p.glob("*.yaml"):
        CONTENTS.append(file.read_text())
        NAMES.append(file.stem)
        FILES.append(file)
    return (CONTENTS, NAMES, FILES)


@pytest.fixture
def cores(num_cores=2) -> list[Core]:
    cores = []
    for i in range(num_cores):
        id = Identifier(name=f"core_{i}")
        top = Module(
            id=id,
        )
        cores.append(Core(id.combined(), top))
    return cores


@pytest.fixture
def ifaces(num_ifaces=2):
    ifaces = []
    for i in range(num_ifaces):
        id = Identifier(f"iface_{i}")
        definition = InterfaceDefinition(
            id=id,
        )
        iface = InterfaceDefinitionResource(definition=definition)
        ifaces.append(iface)
    return ifaces


@pytest.fixture(autouse=True)
def add_buildin_repo_to_fs(fs):
    fs.add_real_directory(get_config().repositories[ConfigManager.BUILTIN_REPO_NAME].to_path())
    yield


class TestCoreResouce:
    def test_load_core_from_file(self, fs, yaml_cores):
        simp_top_yaml_content = None
        for i, name in enumerate(yaml_cores[1]):
            if name == "simp_top":
                simp_top_yaml_content = yaml_cores[0][i]
        assert simp_top_yaml_content, (
            "can't find 'simp_top', probably files in data/data_yaml/ipcore are wrong"
        )
        file = Path("core.yaml")
        file.write_text(simp_top_yaml_content)
        core = Core(name="", top_or_source_yaml=file)
        ports = core.top.ports
        assert ports.find_by_name("sel_gen") is not None
        assert ports.find_by_name("sel_gen").direction == PortDirection.IN
        assert ports.find_by_name("rnd_bit") is not None
        assert ports.find_by_name("rnd_bit").direction == PortDirection.OUT


class TestCoreHandler:
    def test_save(self, fs):
        repo_path = Path("repo")
        irs = [
            adv_top,
            hier_top,
            intf_top,
            intr_top,
            inv_top,
            simp_top,
        ]
        for ir in irs:
            core = Core(ir.id.name, ir)
            CoreHandler().save(core, repo_path)
        files = [
            "cores/hier_top/module.yaml",
            "cores/intf_top/module.yaml",
            "cores/intr_top/module.yaml",
            "cores/inv_top/module.yaml",
            "cores/simp_top/module.yaml",
            "cores/advanced_top/module.yaml",
        ]
        repo_files = [str(f.absolute())[6:] for f in repo_path.glob("**/*.yaml")]
        repo_files.sort()
        files.sort()
        assert repo_files == files

    def test_load(self, fs):
        repo_path = Path("examples/user_repository/repo")
        fs.add_real_directory(repo_path)
        cores = list(CoreHandler().load(repo_path))
        core_names = [c.name for c in cores]
        expetced_names = ["core1", "core2"]
        core_names.sort()
        expetced_names.sort()
        assert core_names == expetced_names


class TestInterfaceDescriptionHandler:
    def test_save(self, fs):
        repo_path = Path("repo")
        irs = [
            adv_top,
            hier_top,
            intf_top,
            intr_top,
            inv_top,
            simp_top,
        ]
        ifaces = []
        for ir in irs:
            for interface in ir.interfaces:
                ifaces.append(interface.definition)
        for iface in ifaces:
            InterfaceDescriptionHandler().save(InterfaceDefinitionResource(iface), repo_path)

        files = [
            "interfaces/top.wrap_scilib_Simply Complex Interface 4.yaml",
            "interfaces/vendor_libdefault_wishbone.yaml",
        ]
        repo_files = [str(f.absolute())[6:] for f in repo_path.glob("**/*.yaml")]
        repo_files.sort()
        files.sort()
        assert repo_files == files

    def test_load(self, fs):
        repo_path = Path("examples/user_repository/repo")
        fs.add_real_directory(repo_path)
        iface = list(InterfaceDescriptionHandler().load(repo_path))
        iface_names = [i.name for i in iface]
        expetced_names = ["vendor_libdefault_coreStream"]
        iface_names.sort()
        expetced_names.sort()
        assert iface_names == expetced_names


class TestUserRepo:
    def test_user_repo(self, fs):
        repo_path = Path("examples/user_repository/repo")
        fs.add_real_directory(repo_path)
        repo = UserRepo("my_repo")
        repo.load(repo_path)
        assert repo.get_resource(Core, "core1") is not None
        assert repo.get_resource(Core, "core2") is not None
        assert (
            repo.get_resource(InterfaceDefinitionResource, "vendor_libdefault_coreStream")
            is not None
        )
