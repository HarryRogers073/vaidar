"""
================================================================================
File:         claude_provider.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Anthropic Claude API provider implementation for test vector generation
================================================================================
"""

import os
from core.interfaces import AIProvider


class ClaudeProvider(AIProvider):
    """AIProvider implementation using Anthropic's Claude API."""

    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022"):
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required. Install it using: pip install anthropic"
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name
        self.last_request = None
        self.last_raw_response = None

    def generate_csv_from_prompt(self, user_prompt: str, system_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\nUser request: {user_prompt}"
        self.last_request = full_prompt
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            # Extract content text blocks safely
            text = "".join([block.text for block in response.content if hasattr(block, 'text')])
            self.last_raw_response = text

            # Clean markdown wrappers if returned
            text = text.replace("```csv", "").replace("```", "").strip()
            lines = text.splitlines()
            if lines and not lines[0].strip().lower().startswith("operation"):
                text = "Operation,Operand A,Operand B\n" + text
            return text
        except Exception as e:
            self.last_raw_response = str(e)
            return f"Error: {e}"

    def analyse_log(self, log_content: str, system_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\n{log_content}"
        self.last_request = full_prompt
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": log_content}]
            )
            text = "".join([block.text for block in response.content if hasattr(block, 'text')])
            self.last_raw_response = text
            return text
        except Exception as e:
            self.last_raw_response = str(e)
            return f"AI Analysis Error: {e}"
