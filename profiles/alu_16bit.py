"""
ALU profile for the 16-bit custom ALU device.

This module provides a concrete DeviceProfile implementation that converts
high-level command dictionaries (for example parsed from CSV rows) into the
binary command packet expected by the FPGA/ALU hardware, and conversely parses
the binary response packet into a Python dictionary.

Packet formats used by this profile (little-endian bytes within fields):
- Command packet (5 bytes): [ opcode, A_hi, A_lo, B_hi, B_lo ]
  - opcode: 1 byte operation code
  - A_hi/A_lo: 16-bit operand A split into high and low bytes
  - B_hi/B_lo: 16-bit operand B split into high and low bytes

- Response packet (>=3 bytes): [ flags, RESULT_hi, RESULT_lo, ... ]
  - flags: 1 byte containing status flags (N, Z, C, V) packed into low bits
  - RESULT_hi/RESULT_lo: 16-bit result split into two bytes

Note: The exact bit positions for flags are taken from the hardware spec used
by this project: N is bit 3, Z is bit 2, C is bit 1 and V is bit 0.
"""

from core.interfaces import DeviceProfile


class ALU16BitProfile(DeviceProfile):
    """Profile to translate between CSV-style dicts and ALU binary packets."""

    # --- Identity ---
    device_name = "16-bit ALU"
    description = (
        "This framework bridges the gap between high-level Python abstraction "
        "and physical FPGA execution. It enables scalable, AI-assisted "
        "Hardware-in-the-Loop (HIL) verification for digital logic circuits."
    )
    author = "Harry Rogers"
    version = "1.0.0"

    # --- Signal Schema ---
    inputs = [("Operand A", 16), ("Operand B", 16)]
    outputs = [("result", 16), ("N", 1), ("Z", 1), ("C", 1), ("V", 1)]
    command_size = 5
    response_size = 3

    # --- Engine display ---
    op_symbols = {
        'ADD': '+', 'SUB': '-', 'MUL': '*', 'DIV': '/',
        'MOD': '%', 'AND': '&', 'OR': '|', 'XOR': '^',
        'SHL': '<<', 'SHR': '>>'
    }

    # --- AI behaviour ---
    ai_generation_prompt = (
        "You are a Verification Engineer. Generate a CSV file containing "
        "edge-case test vectors for an FPGA ALU.\n\n"
        "**Schema:**\n"
        "Columns: Operation,Operand A,Operand B\n\n"
        "**Rules:**\n"
        "1. Operation must be one of: ADD, SUB, MUL, DIV, MOD, SQRT, POW, "
        "AND, OR, XOR, NOT, SHL, SHR, STO, RCL, INC, DEC, NEG.\n"
        "2. Operands: 0 to 65535 (16-bit unsigned).\n"
        "3. Generate tricky edge cases (e.g., max values, zeros, alternating "
        "bits, off-by-one boundaries) based on the user's request.\n"
        "4. For STO and RCL operations, Operand B is the register address "
        "and MUST be strictly between 0 and 3.\n\n"
        "**IMPORTANT:** The first line of your output MUST be exactly: "
        "Operation,Operand A,Operand B\n"
        "Do not use markdown code blocks or formatting. Output raw CSV text "
        "only. Do NOT calculate the expected results or flags."
    )

    ai_analysis_prompt = (
        "Analyse this FPGA ALU test log.\n"
        "Give a 1 sentence pass/fail summary.\n"
        "Only if it failed, give 1 sentence on the likely cause of any failures."
        "\nIf it passed, summarise what it successfully tested, in one sentence."
    )

    # --- Opcode mapping ---
    OPCODES = {
        'add': 0x01, 'sub': 0x02, 'mul': 0x03, 'div': 0x04,
        'mod': 0x05, 'sqrt': 0x06, 'pow': 0x07, 'and': 0x08,
        'or': 0x09, 'xor': 0x0A, 'not': 0x0B, 'shl': 0x0C,
        'shr': 0x0D, 'sto': 0x0E, 'rcl': 0x0F, 'inc': 0x10,
        'dec': 0x11, 'neg': 0x12
    }

    def pack_command(self, row: dict) -> bytes:
        cmd_str = row.get('Operation', '').lower().strip()
        opcode = self.OPCODES.get(cmd_str, 0xFF)

        try:
            op_a = int(row.get('Operand A', 0))
            op_b = int(row.get('Operand B', 0))
        except ValueError:
            print(f"[Profile] Error parsing operands: {row}")
            op_a = 0
            op_b = 0

        a_hi = (op_a >> 8) & 0xFF
        a_lo = op_a & 0xFF
        b_hi = (op_b >> 8) & 0xFF
        b_lo = op_b & 0xFF

        return bytes([opcode, a_hi, a_lo, b_hi, b_lo])

    def unpack_response(self, raw_bytes: bytes):
        if len(raw_bytes) < 3:
            return None

        flags_byte = raw_bytes[0]
        res_hi = raw_bytes[1]
        res_lo = raw_bytes[2]

        result = (res_hi << 8) | res_lo

        n = (flags_byte >> 3) & 1
        z = (flags_byte >> 2) & 1
        c = (flags_byte >> 1) & 1
        v = flags_byte & 1

        return {
            'result': result,
            'N': n, 'Z': z, 'C': c, 'V': v
        }
