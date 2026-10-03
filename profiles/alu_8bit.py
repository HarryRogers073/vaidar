from core.interfaces import DeviceProfile

class ALU8BitProfile(DeviceProfile):
    """
    Profile for the 8-bit FPGA ALU.
    Handles the conversion between Dictionary data and Byte packets.
    """

    # --- Identity ---
    device_name = "8-bit ALU"
    description = "Hardware-in-the-Loop verification for the 8-bit FPGA ALU."
    author = "Harry Rogers"
    version = "1.0.0"

    # --- Signal Schema ---
    inputs = [("operand_a", 8), ("operand_b", 8)]
    outputs = [("result", 8)]
    command_size = 3
    response_size = 3

    # --- Engine display ---
    op_symbols = {
        'ADD': '+', 'SUB': '-', 'MUL': '*', 'DIV': '/'
    }

    # --- AI behaviour ---
    ai_generation_prompt = (
        "You are a Verification Engineer. Generate a CSV file containing "
        "edge-case test vectors for an 8-bit FPGA ALU.\n\n"
        "Columns: command,operand_a,operand_b\n"
        "Operations: add, sub, mul, div\n"
        "Operands: 0 to 255 (8-bit unsigned).\n"
        "Output raw CSV text only."
    )

    ai_analysis_prompt = (
        "Analyse this 8-bit ALU test log.\n"
        "Give a 1 sentence pass/fail summary."
    )

    OPCODES = {
        'add': 1,
        'sub': 2,
        'mul': 3,
        'div': 4
    }

    def pack_command(self, test_data: dict) -> bytes:
        # Check command or Operation
        command_str = test_data.get('command', test_data.get('Operation', ''))
        if not command_str:
            command_str = 'add'
        command_str = str(command_str).lower().strip()
        
        if command_str in self.OPCODES:
            opcode = self.OPCODES[command_str]
        else:
            print(f"[Profile] Sending unknown opcode 0xFF for '{command_str}'")
            opcode = 0xFF 
            
        op_a = int(test_data.get('operand_a', test_data.get('Operand A', 0)))
        op_b = int(test_data.get('operand_b', test_data.get('Operand B', 0)))

        return bytes([opcode, op_a, op_b])
    
    def unpack_response(self, raw_bytes: bytes) -> dict:
        if not raw_bytes:
            return None 
            
        val = int.from_bytes(raw_bytes, 'big')
        return {"result": val & 0xFF}
