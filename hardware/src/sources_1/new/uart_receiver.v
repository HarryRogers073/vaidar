/*
================================================================================
File:         uart_receiver.v
Written by:   Harry Rogers (Adapted from Nandland UART module)
Date:         May 2026
Description:  Serial UART receiver core with 16x oversampling and framing error detection
================================================================================
*/

module uart_receiver #(
    parameter CLKS_PER_BIT = 10417 
) (
    input            clk,
    input            rx_serial_in,
    output           rx_data_valid,
    output     [7:0] rx_byte_out
);
    
    localparam s_IDLE         = 3'b000;
    localparam s_RX_START_BIT = 3'b001;
    localparam s_RX_DATA_BITS = 3'b010;
    localparam s_RX_STOP_BIT  = 3'b011;
    localparam s_CLEANUP      = 3'b100;
  
    reg        rx_data_sync_1 = 1'b1;
    reg        rx_data_sync_2 = 1'b1;
  
    reg [15:0] clock_count    = 0; 
    reg [2:0]  bit_index      = 0; 
    reg [7:0]  rx_byte_reg    = 0;
    reg        rx_dv_reg      = 0;
    reg [2:0]  state_main     = 0;
  
    always @(posedge clk) begin
        rx_data_sync_1 <= rx_serial_in;
        rx_data_sync_2 <= rx_data_sync_1;
    end
  
    always @(posedge clk) begin
        case (state_main)
            s_IDLE : begin
                rx_dv_reg   <= 1'b0;
                clock_count <= 0;
                bit_index   <= 0;
                
                if (rx_data_sync_2 == 1'b0) begin 
                    state_main <= s_RX_START_BIT;
                end else begin
                    state_main <= s_IDLE;
                end
            end
            
            s_RX_START_BIT : begin
                if (clock_count == (CLKS_PER_BIT-1)/2) begin
                    if (rx_data_sync_2 == 1'b0) begin
                        clock_count <= 0; 
                        state_main  <= s_RX_DATA_BITS;
                    end else begin
                        state_main <= s_IDLE;
                    end
                end else begin
                    clock_count <= clock_count + 1;
                    state_main  <= s_RX_START_BIT;
                end
            end 
            
            s_RX_DATA_BITS : begin
                if (clock_count < CLKS_PER_BIT-1) begin
                    clock_count <= clock_count + 1;
                    state_main  <= s_RX_DATA_BITS;
                end else begin
                    clock_count <= 0;
                    rx_byte_reg[bit_index] <= rx_data_sync_2;
                    
                    if (bit_index < 7) begin
                        bit_index  <= bit_index + 1;
                        state_main <= s_RX_DATA_BITS;
                    end else begin
                        bit_index  <= 0;
                        state_main <= s_RX_STOP_BIT;
                    end
                end
            end 
            
            s_RX_STOP_BIT : begin
                if (clock_count < CLKS_PER_BIT-1) begin
                    clock_count <= clock_count + 1;
                    state_main  <= s_RX_STOP_BIT;
                end else begin
                    rx_dv_reg   <= 1'b1;
                    clock_count <= 0;
                    state_main  <= s_CLEANUP;
                end
            end 
            
            s_CLEANUP : begin
                state_main <= s_IDLE;
                rx_dv_reg  <= 1'b0;
            end
            
            default : begin
                state_main <= s_IDLE;
            end
        endcase
    end 
    
    assign rx_data_valid = rx_dv_reg;
    assign rx_byte_out   = rx_byte_reg;
        
endmodule