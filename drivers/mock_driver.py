"""
********************************************************************************
* MODULE:       mock_driver.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Closed-loop hardware simulation driver implementing the CommDriver interface.
* Decodes command packets, simulates execution in software (using the golden model),
* packs the result with proper NZCV flags, and streams it back to the test engine.
********************************************************************************
"""
import time
from core.interfaces import CommDriver
from core.generate_tests import calculate_flags


class MockDriver(CommDriver):
    """Simulated communication driver executing ALU math in software."""

    def __init__(self, profile=None):
        self.profile = profile
        self.connected = False
        self.port = "MOCK"
        self.baud_rate = 0
        self._rx_buffer = bytearray()

    def connect(self):
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False
        self._rx_buffer.clear()

    def send_packet(self, data: bytes):
        if not self.connected:
            raise ConnectionError("Mock serial connection not active.")

        profile_type = type(self.profile).__name__ if self.profile else "ALU16BitProfile"

        if profile_type == "Encoder3to5Profile":
            # 3-to-5 Encoder packet format: [X, Y, Z] (3 bytes)
            if len(data) >= 3:
                x = data[0]
                y = data[1]
                z = data[2]

                out1 = (x + y) & 0xFF
                out2 = (y + z) & 0xFF
                out3 = (x ^ z) & 0xFF
                out4 = (x & y) & 0xFF
                out5 = (y | z) & 0xFF

                self._rx_buffer = bytearray([out1, out2, out3, out4, out5])

        elif profile_type == "ALU8BitProfile":
            # 8-bit ALU packet format: [opcode, operand_a, operand_b] (3 bytes)
            if len(data) >= 3:
                opcode = data[0]
                op_a = data[1]
                op_b = data[2]

                # Map opcode to operation
                opcodes = getattr(self.profile, 'OPCODES', {})
                op_name = ""
                for k, v in opcodes.items():
                    if v == opcode:
                        op_name = k.upper()
                        break

                # Execute 8-bit math
                result = 0
                if op_name == 'ADD':
                    result = (op_a + op_b) & 0xFF
                elif op_name == 'SUB':
                    result = (op_a - op_b) & 0xFF
                elif op_name == 'MUL':
                    result = (op_a * op_b) & 0xFF
                elif op_name == 'DIV':
                    result = (op_a // op_b) & 0xFF if op_b != 0 else 0

                # Return 3 bytes (big-endian) to match the engine's 3-byte receive call
                self._rx_buffer = bytearray(result.to_bytes(3, 'big'))

        else:
            # 16-bit ALU packet format: [opcode, a_hi, a_lo, b_hi, b_lo] (5 bytes)
            if len(data) >= 5:
                opcode = data[0]
                a = (data[1] << 8) | data[2]
                b = (data[3] << 8) | data[4]

                # Map opcode to operation
                opcodes = getattr(self.profile, 'OPCODES', {})
                op_name = ""
                for k, v in opcodes.items():
                    if v == opcode:
                        op_name = k.upper()
                        break

                # Simulate golden model response
                res, n, z, c, v = calculate_flags(op_name, a, b)

                # Return 3 bytes: [flags, res_hi, res_lo]
                flags_byte = (n << 3) | (z << 2) | (c << 1) | v
                res_hi = (res >> 8) & 0xFF
                res_lo = res & 0xFF

                self._rx_buffer = bytearray([flags_byte, res_hi, res_lo])

    def receive_packet(self, num_bytes: int) -> bytes:
        if not self.connected:
            raise ConnectionError("Mock serial connection not active.")

        out = self._rx_buffer[:num_bytes]
        self._rx_buffer = self._rx_buffer[num_bytes:]

        # Pad response if too short
        if len(out) < num_bytes:
            out += bytes([0] * (num_bytes - len(out)))

        return bytes(out)

    def clear_buffer(self):
        self._rx_buffer.clear()
