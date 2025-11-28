module A #(
    parameter PARAM1 = 1,
    parameter CONSTS = {1'b0, 1'b1}
) (
    input logic clk,
    input logic a_b_in,
    input logic a_c_in,
    input logic [7:0] a_data_in,
    input logic logicdriver,
    output logic [1:0] a_out,
    output logic a_b_out,
    output logic [2:0] a_b_ext_out,
    output logic [2:0] a_b_ext_bitsel_out,
    output logic a_bit_sel_out,
    output logic [2:0] a_range_sel_out,
    output logic selfdriven_out,
    output logic [1:0] fordriven_out,
    output logic clocked_out
);

  B #(
    .Bparam(1'b1)
  ) binst (
    .b_in((control).\binst.b_in ),
    .b_out(a_b_out)
  );

  C cinst (
    .c_in(a_c_in),
    .c_out()
  );

  C cinst2 (
    .c_in(),
    .c_out()
  );

  C #(
    .Cparam_bit(CONSTS[0]),
    .Cparam_str("tab[i]")
  ) \genfor_cinst#0  (
    .c_in(a_c_in),
    .c_out()
  );

  C #(
    .Cparam_bit(CONSTS[1]),
    .Cparam_str("tab[i]")
  ) \genfor_cinst#1  (
    .c_in(a_c_in),
    .c_out()
  );

  \A.(control)  (control) (
    .\top.a_b_in (a_b_in),
    .\top.clk (clk),
    .\top.logicdriver (logicdriver),
    .\top.clocked_out (clocked_out),
    .\binst.b_in ()
  );

  concat_2 concat_0 (
    .in0(binst.b_out),
    .in1(cinst.c_out),
    .out(a_out)
  );

  concat_3 concat_1 (
    .in0(1'b0),
    .in1(1'b1),
    .in2(binst.b_out),
    .out(a_b_ext_out)
  );

  concat_2 concat_2 (
    .in0(1'b0),
    .in1(binst.b_out),
    .out()
  );

  concat_2 concat_3 (
    .in0(concat_2.out),
    .in1(binst.b_out),
    .out(a_b_ext_bitsel_out)
  );

  \a_data_in[3]  \a_data_in[3]  (
    .a_data_in(a_data_in),
    .\a_data_in[3] (a_bit_sel_out)
  );

  \a_data_in[5:3]  \a_data_in[5:3]  (
    .a_data_in(a_data_in),
    .\a_data_in[5:3] (a_range_sel_out)
  );

  \a_data_in[0]  \a_data_in[0]  (
    .a_data_in(a_data_in),
    .\a_data_in[0] (selfdriven_out)
  );

  concat_2 concat_4 (
    .in0(\genfor_cinst#1 .c_out),
    .in1(\genfor_cinst#0 .c_out),
    .out(fordriven_out)
  );

endmodule


module B #(
    parameter Bparam = 1'b0
) (
    input logic b_in,
    output logic b_out
);

  assign b_out = b_in;

endmodule


module C #(
    parameter Cparam_bit = 1'b0,
    parameter Cparam_str = ""
) (
    input logic c_in,
    output logic c_out
);

  D dinst (
    .d_in(c_in),
    .d_out(c_out)
  );

endmodule


module \A.(control)  (
    output logic \binst.b_in ,
    input logic \top.a_b_in ,
    output logic \top.clocked_out ,
    input logic \top.clk ,
    input logic \top.logicdriver
);

endmodule


module concat_2 (
    input logic in0,
    input logic in1,
    output logic out
);

endmodule


module concat_3 (
    input logic in0,
    input logic in1,
    input logic in2,
    output logic out
);

endmodule


module \a_data_in[3]  (
    input logic a_data_in,
    output logic \a_data_in[3]
);

endmodule


module \a_data_in[5:3]  (
    input logic a_data_in,
    output logic \a_data_in[5:3]
);

endmodule


module \a_data_in[0]  (
    input logic a_data_in,
    output logic \a_data_in[0]
);

endmodule


module D (
    input logic d_in,
    output logic d_out
);

  assign d_out = d_in;

endmodule
