// Copyright (c) 2024 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

#include <memory>

#include <stdlib.h>
#include <fcntl.h>
#include <termios.h>
#include <unistd.h>

#include <verilated.h>

#include "Vsimple_soc.h"
#include "verilated_vcd_c.h"

int main(int argc, char** argv) {
    const std::unique_ptr<VerilatedContext> contextp{new VerilatedContext};
    contextp->debug(0);
    contextp->randReset(2);
    contextp->traceEverOn(true);
    contextp->commandArgs(argc, argv);

    const std::unique_ptr<Vsimple_soc> soc{new Vsimple_soc{contextp.get(), "simple_soc"}};
    const std::unique_ptr<VerilatedVcdC> tfp{new VerilatedVcdC};
    soc->trace(tfp.get(), 99);
    tfp->open("build/dump.vcd");

    soc->clk100 = 0;
    while (contextp->time() < 225000) {
        contextp->timeInc(1);
        soc->clk100 = !soc->clk100;
        soc->eval();
        tfp->dump(contextp->time());
    }

    soc->final();
    tfp->close();
    return 0;
}
