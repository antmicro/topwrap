// Copyright (c) 2026 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

module consumer (
    input  logic [3:0] c_data,
    input  logic       c_valid,
    output logic [3:0] out_1
);

  assign out_1 = c_valid ? c_data : 4'b0;

endmodule
