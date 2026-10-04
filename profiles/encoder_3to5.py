"""
================================================================================
File:         encoder_3to5.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Device profile for 3-to-5 priority encoder verification
================================================================================
"""

"""
Profile for a custom combinatorial 3-input, 5-output encoder.
Demonstrates framework modularity (arbitrary inputs and outputs).
"""
from core.interfaces import DeviceProfile


class Encoder3to5Profile(DeviceProfile):
    # --- Identity ---
    device_name = "3-to-5 Encoder"
    description = (
        "A custom combinatorial logic encoder featuring 3 inputs (X, Y, Z) "
        "and 5 outputs (Out1, Out2, Out3, Out4, Out5)."
    )
    author = "Harry Rogers"
    version = "1.0.0"

    # --- Signal Schema ---
    inputs = [("X", 8), ("Y", 8), ("Z", 8)]
    outputs = [
        ("Out1", 8),
        ("Out2", 8),
        ("Out3", 8),
        ("Out4", 8),
        ("Out5", 8)
    ]
    command_size = 3
    response_size = 5

    # --- Engine display ---
    op_symbols = {}

    # --- AI prompts ---
    ai_generation_prompt = (
        "Generate a CSV test vector list for a 3-to-5 encoder device.\n"
        "Columns: X,Y,Z\n"
        "Operands: 0 to 255 (8-bit unsigned).\n"
        "Output raw CSV text only."
    )
    ai_analysis_prompt = "Analyse this encoder test log and give a 1 sentence summary."

    def pack_command(self, row: dict) -> bytes:
        try:
            x = int(row.get('X', 0))
            y = int(row.get('Y', 0))
            z = int(row.get('Z', 0))
        except ValueError:
            x = y = z = 0
        return bytes([x & 0xFF, y & 0xFF, z & 0xFF])

    def unpack_response(self, raw_bytes: bytes) -> dict:
        if len(raw_bytes) < 5:
            return None
        return {
            "Out1": raw_bytes[0],
            "Out2": raw_bytes[1],
            "Out3": raw_bytes[2],
            "Out4": raw_bytes[3],
            "Out5": raw_bytes[4]
        }
