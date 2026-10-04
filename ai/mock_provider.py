"""
================================================================================
File:         mock_provider.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Deterministic offline mock LLM provider for CI and testing
================================================================================
"""

from core.interfaces import AIProvider


class MockProvider(AIProvider):
    def __init__(self):
        self.last_request = None
        self.last_raw_response = None

    def generate_csv_from_prompt(self, user_prompt: str, system_prompt: str) -> str:
        self.last_request = f"{system_prompt}\n\nUser request: {user_prompt}"
        self.last_raw_response = "Mock response: no AI backend configured."
        return "Operation,Operand A,Operand B\nADD,100,200\nSUB,500,300\nMUL,255,255\nDIV,1000,0"

    def analyse_log(self, log_content: str, system_prompt: str) -> str:
        self.last_request = f"{system_prompt}\n\n{log_content}"
        self.last_raw_response = "Mock analysis: no AI backend configured."
        return "[Mock AI] No AI backend is configured. Set your API key in Settings to enable AI analysis."
