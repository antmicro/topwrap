# Copyright (c) 2024 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: Apache-2.0

loop:
    li a0, 0x68
    jal x1, write_char
    li a0, 0x65
    jal x1, write_char
    li a0, 0x6C
    jal x1, write_char
    li a0, 0x6C
    jal x1, write_char
    li a0, 0x6F
    jal x1, write_char
    li a0, 0x20
    jal x1, write_char
    li a0, 0x77
    jal x1, write_char
    li a0, 0x6F
    jal x1, write_char
    li a0, 0x72
    jal x1, write_char
    li a0, 0x6C
    jal x1, write_char
    li a0, 0x64
    jal x1, write_char
    li a0, 0x0D
    jal x1, write_char
    li a0, 0x0A
    jal x1, write_char
    j loop

write_char:
    li t0, 0xF0000000 # base UART CSR address
wait:
    lw t1, 0x4(t0)    # load TX_FULL register
    bne t1, x0, wait  # check if TX fifo not full
    sw a0, 0x0(t0)    # store character
    ret
