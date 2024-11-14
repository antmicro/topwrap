#!/bin/bash

# Copyright (c) 2024-2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

DEPS_DEBIAN="git g++ make python3 python3-pip yosys npm  antlr4 libantlr4-runtime-dev"
DEPS_FEDORA="git g++ make python3 python3-pip python3-devel yosys npm  antlr4 antlr4-cpp-runtime-devel"
DEPS_ARCH="git gcc make python3 python-pip yosys npm  antlr4 antlr4-runtime"

set -e

if [[ -f /etc/os-release ]]
then
    source /etc/os-release
    for id in $ID $ID_LIKE; do
        case $id in
            "debian")
                apt update
                apt install --assume-yes $DEPS_DEBIAN
                exit 0
                ;;
            "fedora")
                dnf install --assumeyes $DEPS_FEDORA
                # In order to compile hdlConvertor as a Topwrap dependency,
                # parts of the antlr4 installation need to be symlinked on Fedora
                cd /usr/share/java
                ln -s stringtemplate4/ST4.jar stringtemplate4.jar
                ln -s antlr4/antlr4.jar antlr4.jar
                ln -s antlr4/antlr4-runtime.jar antlr4-runtime.jar
                ln -s treelayout/org.abego.treelayout.core.jar treelayout.jar
                exit 0
                ;;
            "arch")
                pacman -Syu --asdeps --noconfirm --needed $DEPS_ARCH
                # On Arch, the antlr4 installation just needs to be
                # symlinked with a specific filename
                ln -s /usr/share/java/antlr-complete.jar /usr/share/java/antlr4-complete.jar
                exit 0
                ;;
        esac
    done
fi

echo "Unsupported operating system/distribution. Make sure to install the dependencies appropriately for your OS."
