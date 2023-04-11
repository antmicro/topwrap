# Copyright (C) 2021 Antmicro
# SPDX-License-Identifier: Apache-2.0
import click
from logging import warning
from .design import build_design
from .verilog_parser import VerilogModule, ipcore_desc_from_verilog_module
from .vhdl_parser import VHDLModule, ipcore_desc_from_vhdl_module
from .interface_grouper import InterfaceGrouper
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
@click.option('--use-yosys', default=False, is_flag=True,
              help='Use yosys\'s read_verilog_feature to parse Verilog files')
@click.option('--iface-deduce', default=False, is_flag=True,
              help='Try to group port into interfaces automatically')
@click.option('--iface', '-i', multiple=True,
              help='Interface name, that ports will be grouped into')
@click.argument('files', type=click_file, nargs=-1)
def parse_main(use_yosys, iface_deduce, iface, files):
    for filename in list(filter(lambda name: name[-2:] == ".v", files)):
        verilog_mod = VerilogModule(filename)
        iface_grouper = InterfaceGrouper(use_yosys, iface_deduce, iface)
        ipcore_desc = ipcore_desc_from_verilog_module(verilog_mod, iface_grouper) # noqa
        ipcore_desc.save('gen_' + ipcore_desc.name + '.yaml')

    for filename in list(filter(lambda name: name[-4:] == ".vhd" or name[-5:] == ".vhdl", files)): # noqa
        vhdl_mod = VHDLModule(filename)
        iface_grouper = InterfaceGrouper(False, iface_deduce, iface)
        ipcore_desc = ipcore_desc_from_vhdl_module(vhdl_mod, iface_grouper)
        ipcore_desc.save('gen_' + ipcore_desc.name + '.yaml')
