# Copyright (c) 2021-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0
import logging
import os
import subprocess
import sys
from pathlib import Path

import click
from pipeline_manager.scripts.build import script_build
from pipeline_manager.scripts.run import script_run

from .config import config
from .design import build_design_from_yaml
from .interface_grouper import InterfaceGrouper
from .kpm_topwrap_client import kpm_run_client
from .verilog_parser import VerilogModuleGenerator, ipcore_desc_from_verilog_module
from .vhdl_parser import VHDLModule, ipcore_desc_from_vhdl_module

click_dir = click.Path(exists=True, file_okay=False, dir_okay=True, readable=True)
click_opt_dir = click.Path(exists=False, file_okay=False, dir_okay=True, readable=True)
click_file = click.Path(exists=True, file_okay=True, dir_okay=False, readable=True)

main = click.Group(help="FPGA Topwrap")


@main.command("build", help="Generate top module")
@click.option(
    "--sources", "-s", type=click_dir, help="Specify directory to scan for additional sources"
)
@click.option("--design", "-d", type=click_file, required=True, help="Specify top design file")
@click.option(
    "--build-dir",
    "-b",
    type=click_opt_dir,
    default="build",
    help="Specify directory name for output files",
)
@click.option("--part", "-p", help="FPGA part name")
@click.option(
    "--iface-compliance/--no-iface-compliance",
    default=False,
    help="Force compliance checks for predefined interfaces",
)
def build_main(sources, design, build_dir, part, iface_compliance):
    config.force_interface_compliance = iface_compliance

    if part is None:
        logging.warning(
            "You didn't specify part number. 'None' will be used"
            "and thus your implamentation may fail."
        )

    build_design_from_yaml(design, build_dir, sources, part)


@main.command("parse", help="Parse HDL sources to ip core yamls")
@click.option(
    "--use-yosys",
    default=False,
    is_flag=True,
    help="Use yosys's read_verilog_feature to parse Verilog files",
)
@click.option(
    "--iface-deduce",
    default=False,
    is_flag=True,
    help="Try to group port into interfaces automatically",
)
@click.option(
    "--iface", "-i", multiple=True, help="Interface name, that ports will be grouped into"
)
@click.option(
    "--dest-dir",
    "-d",
    type=click_dir,
    default="./",
    help="Destination directory for generated yamls",
)
@click.argument("files", type=click_file, nargs=-1)
def parse_main(use_yosys, iface_deduce, iface, files, dest_dir):
    logging.basicConfig(level=logging.INFO)
    dest_dir = os.path.dirname(dest_dir)

    for filename in list(filter(lambda name: os.path.splitext(name)[-1] == ".v", files)):  # noqa
        modules = VerilogModuleGenerator().get_modules(filename)
        iface_grouper = InterfaceGrouper(use_yosys, iface_deduce, iface)
        for verilog_mod in modules:
            ipcore_desc = ipcore_desc_from_verilog_module(verilog_mod, iface_grouper)
            yaml_path = os.path.join(dest_dir, f"gen_{ipcore_desc.name}.yaml")
            ipcore_desc.save(yaml_path)
            logging.info(
                f"Verilog module '{verilog_mod.get_module_name()}'" f"saved in file '{yaml_path}'"
            )

    for filename in list(
        filter(lambda name: os.path.splitext(name)[-1] in [".vhd", ".vhdl"], files)
    ):  # noqa
        # TODO - handle case with multiple VHDL modules in one file
        vhdl_mod = VHDLModule(filename)
        iface_grouper = InterfaceGrouper(False, iface_deduce, iface)
        ipcore_desc = ipcore_desc_from_vhdl_module(vhdl_mod, iface_grouper)
        yaml_path = os.path.join(dest_dir, f"gen_{ipcore_desc.name}.yaml")
        ipcore_desc.save(yaml_path)
        logging.info(f"VHDL Module '{vhdl_mod.get_module_name()}'" f"saved in file '{yaml_path}'")


DEFAULT_WORKSPACE_DIR = Path("build", "workspace")
DEFAULT_BACKEND_DIR = Path("build", "backend")
DEFAULT_FRONTEND_DIR = Path("build", "frontend")
DEFAULT_SERVER_ADDR = "127.0.0.1"
DEFAULT_SERVER_PORT = 9000
DEFAULT_BACKEND_ADDR = "127.0.0.1"
DEFAULT_BACKEND_PORT = 5000


@main.command("kpm_client", help="Run a client app, that connects to" "a running KPM server")
@click.option("--host", "-h", default=DEFAULT_SERVER_ADDR, help="KPM server address")
@click.option("--port", "-p", default=DEFAULT_SERVER_PORT, help="KPM server listening port")
@click.argument("yamlfiles", type=click_file, nargs=-1)
def kpm_client_main(host, port, yamlfiles):
    kpm_run_client(host, port, yamlfiles)


@main.command("kpm_build_server", help="Build KPM server")
@click.option(
    "--workspace-directory",
    type=click.Path(),
    default=DEFAULT_WORKSPACE_DIR,
    help="Directory where the frontend sources should be stored",
)
@click.option(
    "--output-directory",
    type=click.Path(),
    default=DEFAULT_FRONTEND_DIR,
    help="Directory where the built frontend should be stored",
)
@click.pass_context
def kpm_build_server(ctx, workspace_directory, output_directory):
    args = ["pipeline_manager", "build", "server-app"]
    for k, v in ctx.params.items():
        args += [f"--{k}".replace("_", "-"), f"{v}"]
    subprocess.check_call(args)


@main.command("kpm_run_server", help="Run a KPM server")
@click.option(
    "--frontend-directory",
    type=click.Path(),
    default=DEFAULT_FRONTEND_DIR,
    help="Location of the built frontend",
)
@click.option(
    "--server-host",
    default=DEFAULT_SERVER_ADDR,
    help="The address of the Pipeline Manager TCP Server",
)
@click.option(
    "--server-port", default=DEFAULT_SERVER_PORT, help="The port of the Pipeline Manager TCP Server"
)
@click.option(
    "--backend-host",
    default=DEFAULT_BACKEND_ADDR,
    help="The adress of the backend of Pipeline Manager",
)
@click.option(
    "--backend-port",
    default=DEFAULT_BACKEND_PORT,
    help="The port of the backend of Pipeline Manager",
)
@click.pass_context
def kpm_run_server(
    ctx,
    frontend_directory,
    server_host,
    server_port,
    backend_host,
    backend_port,
):
    args = ["pipeline_manager", "run"]
    for k, v in ctx.params.items():
        args += [f"--{k}".replace("_", "-"), f"{v}"]
    subprocess.check_call(args)
