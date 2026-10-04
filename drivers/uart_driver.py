"""
================================================================================
File:         uart_driver.py
Written by:   Harry Rogers
Date:         May 2026
Description:  High-speed buffered serial UART communication driver (up to 921,600 baud)
================================================================================
"""

import serial
import time
from core.interfaces import CommDriver

class UARTDriver(CommDriver):
    def __init__(self, port, baud_rate, timeout=2):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.connection = None

    def connect(self):
        try:
            print(f"[Driver] Connecting to {self.port} at {self.baud_rate}...")
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )
            time.sleep(0.5) 
            print("[Driver] Connected successfully.")
            return True
        except serial.SerialException as e:
            print(f"[Driver] Error connecting: {e}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("[Driver] Disconnected.")

    def send_packet(self, data: bytes):
        if not self.connection or not self.connection.is_open:
            raise ConnectionError("Serial port not open.")
        self.connection.write(data)

    def receive_packet(self, num_bytes: int) -> bytes:
        if not self.connection or not self.connection.is_open:
            raise ConnectionError("Serial port not open.")
        return self.connection.read(num_bytes)

    def clear_buffer(self):
        """
        Discard all data currently in the serial input buffer.
        Useful to resynchronise before starting a new test batch.
        """
        if self.connection and self.connection.is_open:
            self.connection.reset_input_buffer()
