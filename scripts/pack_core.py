#!/usr/bin/env python3

# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

import logging
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory

import click

from topwrap.repo.files import HttpGetFile
from topwrap.repo.user_repo import UserRepo, VerilogFileHandler

click_r_dir = click.Path(exists=True, file_okay=False, dir_okay=True, readable=True)
click_opt_rw_dir = click.Path(
    exists=False, file_okay=False, dir_okay=True, readable=True, writable=True
)
click_r_file = click.Path(exists=True, file_okay=True, dir_okay=False, readable=True)

AVAILABLE_LOG_LEVELS = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"


cores = {
    "verilog-axi": {
        "root": "https://raw.githubusercontent.com/alexforencich/verilog-axi/master/rtl",
        "sources": [
            "arbiter.v",
            "axi_adapter.v",
            "axi_adapter_rd.v",
            "axi_adapter_wr.v",
            "axi_axil_adapter.v",
            "axi_axil_adapter_rd.v",
            "axi_axil_adapter_wr.v",
            # "axi_cdma.v",
            "axi_cdma_desc_mux.v",
            # "axi_crossbar.v",  # unsupported parameter value
            # "axi_crossbar_addr.v",
            # "axi_crossbar_rd.v",  # unsupported parameter value
            # "axi_crossbar_wr.v",  # unsupported parameter value
            "axi_dma.v",
            "axi_dma_desc_mux.v",
            # "axi_dma_rd.v",
            # "axi_dma_wr.v",
            # "axi_dp_ram.v", # processing takes too much time
            "axi_fifo.v",
            "axi_fifo_rd.v",
            "axi_fifo_wr.v",
            # "axi_interconnect.v",
            # "axi_ram.v", # processing takes too much time
            "axi_ram_rd_if.v",
            "axi_ram_wr_if.v",
            "axi_ram_wr_rd_if.v",
            "axi_register.v",
            "axi_register_rd.v",
            "axi_register_wr.v",
            # "axi_vfifo.v",
            "axi_vfifo_dec.v",
            # "axi_vfifo_enc.v", # Unsup. expr. on dyn. range sel. on sig. `\seg_mem_rd_data'
            "axi_vfifo_raw.v",
            "axi_vfifo_raw_rd.v",
            "axi_vfifo_raw_wr.v",
            "axi_vfifo.v",
            "axil_adapter.v",
            "axil_adapter_rd.v",
            "axil_adapter_wr.v",
            "axil_cdc.v",
            "axil_cdc_rd.v",
            "axil_cdc_wr.v",
            "axil_crossbar.v",
            # "axil_crossbar_addr.v",
            "axil_crossbar_rd.v",
            "axil_crossbar_wr.v",
            # "axil_dp_ram.v", # processing takes too much time
            # "axil_interconnect.v",
            # "axil_ram.v", # processing takes too much time
            "axil_reg_if.v",
            "axil_reg_if_rd.v",
            "axil_reg_if_wr.v",
            "axil_register.v",
            "axil_register_rd.v",
            "axil_register_wr.v",
            "priority_encoder.v",
        ],
    }
}


def configure_log_level(log_level: str):
    logging.basicConfig(level=DEFAULT_LOG_LEVEL)
    if log_level not in AVAILABLE_LOG_LEVELS:
        logging.warning(f"Wrong log-level value: {log_level}. Select one of {AVAILABLE_LOG_LEVELS}")

    logger = logging.getLogger()
    logger.setLevel(log_level)


def scan_sources(source_dir: Path):
    sources = []

    for root, dirs, files in Path.walk(source_dir):
        for file in files:
            if file.lower().endswith(".v"):
                logging.info(f"Found RTL file: {file}")
                sources.append(Path(root) / file)

    return sources


@click.command()
@click.option("--log-level", default=DEFAULT_LOG_LEVEL, help="Log level")
@click.argument("name", type=click.STRING)
def pack_core(log_level: str, name: str):
    """Generates reusable cores package for usage in Topwrap project.

    Scans one or more SOURCE_DIRS for RTL sources and packages them
    into reusable "NAME.tar.gz" archive with YAML description files.
    """
    configure_log_level(log_level)
    core_repo = UserRepo()

    if name not in cores:
        exit(1)

    core = cores[name]
    root_path = core["root"]
    core_files = []

    for file in core["sources"]:
        logging.info(f"Fetching: {file}")
        core_files.append(HttpGetFile(f"{root_path}/{file}"))

    core_repo.add_files(VerilogFileHandler(core_files))

    with TemporaryDirectory() as tmpdir:
        core_repo.save(tmpdir)
        with tarfile.open(f"{name}.tar.gz", "w:gz") as tar:
            tar.add(tmpdir, arcname=".")
            logging.info(f"Cores packaged to archive: {tar.name}")


if __name__ == "__main__":
    pack_core()
