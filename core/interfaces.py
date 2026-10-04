"""
================================================================================
File:         interfaces.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Abstract base classes for CommDriver, DeviceProfile, and AIProvider
================================================================================
"""

from abc import ABC, abstractmethod


class CommDriver(ABC):
    """
    Abstract Base Class for Communication Drivers (UART, TCP, SPI, etc).
    """
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def send_packet(self, data: bytes):
        pass

    @abstractmethod
    def receive_packet(self, num_bytes: int) -> bytes:
        pass


class DeviceProfile(ABC):
    """
    Abstract Base Class for Device Logic (ALU, Sensor, Motor, etc).
    Subclasses must override the metadata class attributes to describe
    their specific device, and implement pack/unpack for binary conversion.
    """

    # --- Identity (override in subclasses) ---
    device_name: str = "Unknown Device"
    description: str = "No description provided."
    author: str = ""
    version: str = "1.0.0"

    # --- Signal Schema (override in subclasses for arbitrary modularity) ---
    inputs: list = [("Operand A", 16), ("Operand B", 16)]
    outputs: list = [("result", 16), ("N", 1), ("Z", 1), ("C", 1), ("V", 1)]
    command_size: int = 5
    response_size: int = 3

    # --- Engine display ---
    op_symbols: dict = {}

    # --- AI behaviour (the developer writes these per-profile) ---
    ai_generation_prompt: str = ""
    ai_analysis_prompt: str = ""

    @abstractmethod
    def pack_command(self, test_data: dict) -> bytes:
        pass

    @abstractmethod
    def unpack_response(self, raw_bytes: bytes):
        pass


class AIProvider(ABC):
    """
    Abstract Base Class for AI Backends (Gemini, OpenAI, Local, Mock, etc).
    Methods accept a system_prompt argument so all domain knowledge comes
    from the DeviceProfile, not from the provider itself.
    """
    @abstractmethod
    def generate_csv_from_prompt(self, user_prompt: str, system_prompt: str) -> str:
        pass

    @abstractmethod
    def analyse_log(self, log_content: str, system_prompt: str) -> str:
        pass
