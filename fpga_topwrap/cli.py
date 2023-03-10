# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
import click
from logging import warning
from .design import build_design
from .verilog_parser import parse_verilog_sources
from .vhdl_parser import parse_vhdl_sources
from .config import config


click_dir = click.Path(exists=True, file_okay=False, dir_okay=True,
                       readable=True)
click_file = click.Path(exists=True, file_okay=True, dir_okay=False,
                        readable=True)

main = click.Group(help="FPGA Topwrap")


@main.command("build", help="Generate top module")
@click.option('--sources', '-s', type=click_dir,
              help='Specify directory to scan for additional sources')
@click.option('--design', '-d', type=click_file, required=True,
              help='Specify top design file')
@click.option('--part', '-p', help='FPGA part name')
@click.option('--iface-compliance/--no-iface-compliance', default=False,
              help='Force compliance checks for predefined interfaces')
def build_main(sources, design, part, iface_compliance):
    config.force_interface_compliance = iface_compliance

    if part is None:
        warning("You didn't specify part number. "
                "'None' will be used and thus your implamentation may fail.")

    build_design(design, sources, part)


@main.command("parse", help="Parse HDL sources to ip core yamls")
@click.option('--iface-deduce', default=False, is_flag=True,
              help='Try to group port into interfaces automatically')
@click.option('--iface', '-i', multiple=True,
              help='Interface name, that ports will be grouped into')
@click.argument('files', type=click_file, nargs=-1)
def parse_main(iface_deduce, iface, files):
    parse_verilog_sources(
        list(filter(lambda name: name[-2:] == ".v", files)),
        iface, iface_deduce)
    parse_vhdl_sources(list(filter(
        lambda name: name[-4:] == ".vhd" or name[-5:] == ".vhdl", files)),
        iface, iface_deduce)
