module top_design (
    input  wire clk,
    input  wire rst,
    output wire Output_y,
    output wire Output_c
);
   wire z_to_a;

   simple_core_1 simple_core_1_inst (
       .clk(clk),
       .rst(rst),
       .z(z_to_a)
   );

   simple_core_2 simple_core_2_inst (
       .a(z_to_a),
       .y(Output_y),
       .c(Output_c)
   );

endmodule
