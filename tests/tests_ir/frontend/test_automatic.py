# Copyright (c) 2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from examples.ir_examples.modules import adv_top
from topwrap.backend.sv.backend import SystemVerilogBackend
from topwrap.frontend.automatic import AutomaticFrontend
from topwrap.frontend.kpm.frontend import KpmFrontend
from topwrap.frontend.sv.frontend import SystemVerilogFrontend
from topwrap.frontend.yaml.design_schema import DesignDescription
from topwrap.frontend.yaml.frontend import YamlFrontend


@pytest.fixture
def sv_sources():
    back = SystemVerilogBackend(mod_stubs=True)
    files = back.serialize(back.represent(adv_top))
    with TemporaryDirectory() as tmpdir:
        for file in files:
            file.save(Path(tmpdir))
        yield [*Path(tmpdir).iterdir()]


@pytest.fixture
def kpm_sources():
    files = []
    with TemporaryDirectory() as tmpdir:
        for path in Path("tests/data/data_kpm/conversions/complex").glob("*.json"):
            target = (Path(tmpdir) / path).with_name(path.name + ".kpm.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target)
            files.append(target)
        yield files


@pytest.fixture
def yaml_sources() -> list[Path]:
    des_path = Path("tests/data/data_build/design.yaml")
    desc = DesignDescription.load(des_path)
    return [des_path] + [p.path for p in desc.all_ips]


class TestAutomaticFrontend:
    def test_automatic_frontend(
        self,
        kpm_sources: list[Path],
        sv_sources: list[Path],
        yaml_sources: list[Path],
    ):
        kpm_cnt = len(KpmFrontend().parse_files(kpm_sources).modules)
        yaml_cnt = len(YamlFrontend().parse_files(yaml_sources).modules)
        sv_cnt = len(SystemVerilogFrontend().parse_files(sv_sources).modules)

        assert kpm_cnt > 0 and yaml_cnt > 0 and sv_cnt > 0

        all_sources = sv_sources + kpm_sources + yaml_sources
        front = AutomaticFrontend()
        modules = front.parse_files(all_sources).modules
        assert len(modules) == kpm_cnt + yaml_cnt + sv_cnt

    def test_unknown(self, sv_sources: list[Path]):
        unknown_source = Path("/tmp/foo.bar")
        all_sources = [*sv_sources, unknown_source]

        front = AutomaticFrontend()
        info = front.parse_files_with_unknown_info(all_sources)
        assert info.unknown_sources == [unknown_source]
