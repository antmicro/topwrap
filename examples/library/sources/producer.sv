// Copyright (c) 2026 Antmicro <www.antmicro.com>
// SPDX-License-Identifier: Apache-2.0

module producer (
    input  logic [3:0] in_1,
    output logic [3:0] p_data,
    output logic       p_valid
);

  assign p_data = in_1;
  assign p_valid = 1'b1;

endmodule
