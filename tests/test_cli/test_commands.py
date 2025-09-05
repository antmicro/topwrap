# Copyright (c) 2023-2025 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import logging
import socket
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from topwrap.cli.main import (
    build_main,
    generate_kpm_design,
    generate_kpm_spec,
    main,
    parse_main,
    topwrap_gui,
)
from topwrap.util import get_config


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

    def test_parse_main(self, tmp_path):
        test_file_names = ["axi_axil_adapter.v", "axi_dispctrl_v1_0.vhd"]

        files_to_parse = [
            Path(f"{self.test_data_path}data_parse/{file_name}") for file_name in test_file_names
        ]

        with click.Context(parse_main) as ctx:
            ctx.invoke(
                parse_main,
                iface=[],
                files=files_to_parse,
                dest_dir=tmp_path,
            )

        for test_file_name in test_file_names:
            file_name = Path(test_file_name).stem
            file_name = f"{file_name}.yaml"
            assert Path(tmp_path / file_name).exists()

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
