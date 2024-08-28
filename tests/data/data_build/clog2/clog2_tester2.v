module clog2_tester
    #(parameter w=1,
    parameter p4=4,
    parameter depth=32*(32+p4)/w)
    (input wire i_clk,
    input wire [$clog2(depth*2)-2:0] i_waddr,
    output wire [$clog2(depth*2)-2:0] o_waddr
    );

    always @(posedge i_clk) begin
        o_waddr <= i_waddr;
    end

endmodule
