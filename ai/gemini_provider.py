"""
********************************************************************************
* MODULE:       gemini_provider.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Concrete implementation of the AIProvider interface using Google's Gemini
* API. This is a generic LLM wrapper with zero hardcoded domain knowledge.
* All context about the device under test comes from the system_prompt
* argument, which is supplied by the DeviceProfile.
********************************************************************************
"""
import io
import csv
from core.interfaces import AIProvider
from core.generate_tests import calculate_flags


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro"):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.last_request = None
        self.last_raw_response = None

    def generate_csv_from_prompt(self, user_prompt: str, system_prompt: str) -> str:
        full_prompt = f"{system_prompt}\n\nUser request: {user_prompt}"
        self.last_request = full_prompt
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            self.last_raw_response = response.text or ""
            text = self.last_raw_response
            
            # Strip markdown formatting if present
            text = text.replace("```csv", "").replace("```", "").strip()
            
            # Ensure header row is present
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
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
            )
            self.last_raw_response = response.text or ""
            return self.last_raw_response
        except Exception as e:
            self.last_raw_response = str(e)
            return f"AI Analysis Error: {e}"
