/*
================================================================================
File:         seven_segment_controller.v
Written by:   Harry Rogers
Date:         May 2026
Description:  Multiplexed 7-segment display driver for live FPGA bus inspection
================================================================================
*/

module seven_segment_controller (
    input             clk,
    input             rst,
    input      [15:0] display_value, 
    output     [7:0]  cathodes,      
    output reg [7:0]  anodes       
);

    wire [3:0] digit_0; 
    wire [3:0] digit_1;
    wire [3:0] digit_2;
    wire [3:0] digit_3; 

    wire       refresh_clk;  
    reg [1:0]  scan_count = 0; 
    reg [3:0]  current_nibble; 

    assign digit_0 = display_value[3:0];   
    assign digit_1 = display_value[7:4];   
    assign digit_2 = display_value[11:8];  
    assign digit_3 = display_value[15:12]; 

    clock_divider u_clk_div (
        .clk_in(clk),
        .rst(rst),
        .clk_out(refresh_clk)
    );

    always @(posedge refresh_clk or posedge rst) begin
        if (rst) begin
            scan_count <= 2'b00;
        end else begin
            scan_count <= scan_count + 1;
        end
    end

    always @(*) begin
        case (scan_count)
            2'b00: current_nibble = digit_0; 
            2'b01: current_nibble = digit_1; 
            2'b10: current_nibble = digit_2; 
            2'b11: current_nibble = digit_3; 
            default: current_nibble = 4'h0;
        endcase
    end

    hex_to_seven_segment u_decoder (
        .hex_in(current_nibble), 
        .seg_out(cathodes)
    );
    
    always @(*) begin
        case (scan_count)
            2'b00: anodes = 8'b1111_1110;
            2'b01: anodes = 8'b1111_1101; 
            2'b10: anodes = 8'b1111_1011; 
            2'b11: anodes = 8'b1111_0111; 
            default: anodes = 8'b1111_1111;
        endcase
    end 

endmodule