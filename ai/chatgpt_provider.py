"""
================================================================================
File:         chatgpt_provider.py
Written by:   Harry Rogers
Date:         May 2026
Description:  OpenAI ChatGPT API provider implementation for test vector generation
================================================================================
"""

import os
from core.interfaces import AIProvider


class ChatGPTProvider(AIProvider):
    """AIProvider implementation using OpenAI's ChatGPT API."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        try:
            import openai
        except ImportError:
            raise ImportError(
                "The 'openai' package is required. Install it using: pip install openai"
            )
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        self.last_request = None
        self.last_raw_response = None

    def generate_csv_from_prompt(self, user_prompt: str, system_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\nUser request: {user_prompt}"
        self.last_request = full_prompt
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            text = response.choices[0].message.content or ""
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
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": log_content}
                ]
            )
            text = response.choices[0].message.content or ""
            self.last_raw_response = text
            return text
        except Exception as e:
            self.last_raw_response = str(e)
            return f"AI Analysis Error: {e}"
