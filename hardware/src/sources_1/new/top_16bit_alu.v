/*
********************************************************************************
* MODULE:       top_16bit_alu
* AUTHOR:       Harry Rogers
* DATE:         2026
********************************************************************************
*/

module top_16bit_alu #(
    parameter CLK_FREQ  = 100_000_000, 
    parameter BAUD_RATE = 921600       
) (
    input        clk,
    input        rst,
    input        rx_serial_in,
    output       tx_serial_out,
    output [7:0] seven_seg_cathodes,
    output [7:0] seven_seg_anodes,
    output [3:0] status_leds        
);

    // =========================================================================
    // SIGNALS & REGISTERS
    // =========================================================================
    
    wire [7:0] rx_byte_data;
    wire       rx_done_flag;
    reg        tx_data_valid = 0;
    reg [7:0]  tx_byte_data  = 0;
    wire       tx_done_flag;

    reg [3:0] current_state = 0;
    localparam STATE_IDLE        = 0,
               STATE_WAIT_A_HI   = 1,
               STATE_WAIT_A_LO   = 2,
               STATE_WAIT_B_HI   = 3,
               STATE_WAIT_B_LO   = 4,
               STATE_CALCULATE   = 5,
               STATE_TX_FLAGS    = 6,
               STATE_TX_HI       = 7,
               STATE_TX_LO       = 8;

    reg [7:0]  opcode_reg;
    reg [15:0] operand_a, operand_b, alu_result;
    reg [15:0] register_file [0:3]; 
    reg [3:0]  alu_flags;          
    reg [31:0] temp_accumulator;   
    reg [15:0] wait_timer = 0;
    reg        pow_carry_latch;     
    
    // Dynamically calculate N and Z, and combine with stored C and V
    assign status_leds = {alu_result[15], (alu_result == 16'b0), alu_flags[1], alu_flags[0]};

    // --- TIMING & FLAG WIRES ---
    wire [16:0] add_val = {1'b0, operand_a} + {1'b0, operand_b};
    wire [16:0] sub_val = {1'b0, operand_a} - {1'b0, operand_b};
    wire [31:0] shl_val = {16'b0, operand_a} << operand_b[3:0];
    wire [16:0] inc_val = {1'b0, operand_a} + 1;
    wire [16:0] dec_val = {1'b0, operand_a} - 1;
    wire [16:0] neg_val = 17'b0 - {1'b0, operand_a};

    // =========================================================================
    // COMBINATIONAL FUNCTIONS
    // =========================================================================
    
    function [15:0] hardware_sqrt;
        input [15:0] val;
        reg [15:0] a, q;
        reg [17:0] left, right;
        integer i;
        begin
            a = val; q = 0; left = 0; right = 0;
            for (i = 0; i < 8; i = i + 1) begin
                right = {q, right[1], 1'b1};
                left  = {left[13:0], a[15:14]};
                a     = {a[13:0], 2'b00};
                if (left >= right) begin
                    left = left - right;
                    q    = {q[6:0], 1'b1};
                end else begin
                    q    = {q[6:0], 1'b0};
                end
            end
            hardware_sqrt = q;
        end
    endfunction

    // =========================================================================
    // MODULE INSTANTIATIONS
    // =========================================================================
    
    uart_receiver #(.CLKS_PER_BIT(CLK_FREQ / BAUD_RATE)) uart_rx_inst (
        .clk(clk), .rx_serial_in(rx_serial_in), 
        .rx_data_valid(rx_done_flag), .rx_byte_out(rx_byte_data)
    );

    uart_transmitter #(.CLKS_PER_BIT(CLK_FREQ / BAUD_RATE)) uart_tx_inst (
        .clk(clk), .tx_data_valid(tx_data_valid), .tx_byte_in(tx_byte_data), 
        .tx_active(), .tx_serial_out(tx_serial_out), .tx_done_flag(tx_done_flag)
    );

    // =========================================================================
    // MAIN CONTROL LOGIC (FSM)
    // =========================================================================
    
    integer j;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            current_state <= STATE_IDLE;
            tx_data_valid <= 0; 
            alu_result    <= 0; 
            alu_flags     <= 0;
            wait_timer    <= 0;
            pow_carry_latch <= 0;
            for (j = 0; j < 4; j = j + 1) register_file[j] <= 16'h0000;
        end else begin
            tx_data_valid <= 0; 

            case (current_state)
                STATE_IDLE:      if (rx_done_flag) begin opcode_reg <= rx_byte_data; current_state <= STATE_WAIT_A_HI; end
                STATE_WAIT_A_HI: if (rx_done_flag) begin operand_a[15:8] <= rx_byte_data; current_state <= STATE_WAIT_A_LO; end
                STATE_WAIT_A_LO: if (rx_done_flag) begin operand_a[7:0] <= rx_byte_data; current_state <= STATE_WAIT_B_HI; end
                STATE_WAIT_B_HI: if (rx_done_flag) begin operand_b[15:8] <= rx_byte_data; current_state <= STATE_WAIT_B_LO; end
                STATE_WAIT_B_LO: if (rx_done_flag) begin operand_b[7:0] <= rx_byte_data; current_state <= STATE_CALCULATE; end

                STATE_CALCULATE: begin
                    alu_flags <= 4'b0000; 
                    case (opcode_reg)
                        8'h01: begin // ADD
                            alu_result   <= add_val[15:0];
                            alu_flags[1] <= add_val[16]; 
                            alu_flags[0] <= ~(operand_a[15] ^ operand_b[15]) & (operand_a[15] ^ add_val[15]); 
                            current_state <= STATE_TX_FLAGS;
                        end
                        8'h02: begin // SUB
                            alu_result   <= sub_val[15:0];
                            // Corrected carry bit assignment
                            alu_flags[1] <= sub_val[16];
                            alu_flags[0] <= (operand_a[15] ^ operand_b[15]) & (operand_a[15] ^ sub_val[15]);
                            current_state <= STATE_TX_FLAGS;
                        end
                        8'h03: begin // MUL
                            temp_accumulator = operand_a * operand_b;
                            alu_result <= temp_accumulator[15:0];
                            if (temp_accumulator > 32'hFFFF) alu_flags[1] <= 1'b1; 
                            current_state <= STATE_TX_FLAGS;
                        end

                        8'h04, 8'h05, 8'h06: begin // DIV, MOD, SQRT
                            if ((opcode_reg == 8'h04 || opcode_reg == 8'h05) && operand_b == 0) begin
                                alu_result <= 16'hEEEE; alu_flags[0] <= 1; current_state <= STATE_TX_FLAGS;
                            end else if (wait_timer < 32) begin
                                wait_timer <= wait_timer + 1;
                                current_state <= STATE_CALCULATE; 
                            end else begin
                                if (opcode_reg == 8'h04) alu_result <= operand_a / operand_b;
                                else if (opcode_reg == 8'h05) alu_result <= operand_a % operand_b;
                                else alu_result <= hardware_sqrt(operand_a);
                                wait_timer <= 0;
                                current_state <= STATE_TX_FLAGS;
                            end
                        end

                        8'h07: begin // POW
                            if (operand_b == 0) begin
                                alu_result <= 16'h0001; 
                                alu_flags[1] <= 0;
                                current_state <= STATE_TX_FLAGS;
                            end else if (wait_timer == 0) begin
                                temp_accumulator <= operand_a;
                                pow_carry_latch <= 0;
                                wait_timer <= 1;
                            end else if (wait_timer < operand_b) begin
                                if ((temp_accumulator * operand_a) > 32'hFFFF) begin
                                    pow_carry_latch <= 1;
                                end
                                temp_accumulator <= temp_accumulator * operand_a;
                                wait_timer <= wait_timer + 1;
                            end else begin
                                alu_result <= temp_accumulator[15:0];
                                alu_flags[1] <= pow_carry_latch; 
                                wait_timer <= 0;
                                current_state <= STATE_TX_FLAGS;
                            end
                        end

                        8'h08: begin alu_result <= operand_a & operand_b; current_state <= STATE_TX_FLAGS; end
                        8'h09: begin alu_result <= operand_a | operand_b; current_state <= STATE_TX_FLAGS; end
                        8'h0A: begin alu_result <= operand_a ^ operand_b; current_state <= STATE_TX_FLAGS; end
                        8'h0B: begin alu_result <= ~operand_a; current_state <= STATE_TX_FLAGS; end
                        
                        8'h0C: begin // SHL
                            alu_result <= shl_val[15:0]; 
                            current_state <= STATE_TX_FLAGS; 
                        end
                        8'h0D: begin alu_result <= operand_a >> operand_b[3:0]; current_state <= STATE_TX_FLAGS; end
                        8'h0E: begin register_file[operand_b[1:0]] <= operand_a; alu_result <= 16'h0000; current_state <= STATE_TX_FLAGS; end
                        8'h0F: begin alu_result <= register_file[operand_b[1:0]]; current_state <= STATE_TX_FLAGS; end
                        
                        8'h10: begin // INC
                            alu_result   <= inc_val[15:0];
                            alu_flags[1] <= inc_val[16]; 
                            alu_flags[0] <= 1'b0; 
                            current_state <= STATE_TX_FLAGS; 
                        end
                        8'h11: begin // DEC
                            alu_result   <= dec_val[15:0];
                            alu_flags[1] <= dec_val[16]; 
                            alu_flags[0] <= (operand_a[15] & ~dec_val[15]); 
                            current_state <= STATE_TX_FLAGS; 
                        end
                        8'h12: begin // NEG
                            alu_result   <= neg_val[15:0];
                            alu_flags[1] <= ~neg_val[16]; 
                            alu_flags[0] <= (operand_a == 16'h8000); 
                            current_state <= STATE_TX_FLAGS; 
                        end

                        default: begin alu_result <= 16'hDEAD; current_state <= STATE_TX_FLAGS; end
                    endcase
                end

                STATE_TX_FLAGS: begin
                    tx_byte_data <= {4'b0000, alu_result[15], (alu_result == 16'b0), alu_flags[1], alu_flags[0]};
                    tx_data_valid <= 1;
                    current_state <= STATE_TX_HI;
                end
                STATE_TX_HI: if (tx_done_flag) begin tx_byte_data <= alu_result[15:8]; tx_data_valid <= 1; current_state <= STATE_TX_LO; end
                STATE_TX_LO: if (tx_done_flag) begin tx_byte_data <= alu_result[7:0]; tx_data_valid <= 1; current_state <= STATE_IDLE; end
            endcase
        end
    end

    seven_segment_controller u_display (
        .clk(clk), .rst(rst), .display_value(alu_result),
        .cathodes(seven_seg_cathodes), .anodes(seven_seg_anodes)
    );

endmodule