"""
********************************************************************************
* MODULE:       config_manager.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Centralised configuration management. Provides a single source of truth
* for settings. Handles loading/saving non-sensitive settings in config.json,
* and loading/saving sensitive API credentials securely in a local .env file.
********************************************************************************
"""
import os
import json


class ConfigManager:
    """Loads, stores, and persists settings. Excludes secrets from config.json."""

    DEFAULTS = {
        "default_port": "COM6",
        "baud_rate": 921600,
        "visual_delay": 0.0,
        "theme": "Dark",
        "device_profile": "16-bit ALU",
        "comm_driver": "UART (Serial)",
        "ai_provider": "Google Gemini",
        "gemini_model": "gemini-2.5-pro"
    }

    def __init__(self, path="config.json"):
        self._path = path
        self._data = dict(self.DEFAULTS)
        self._keys = {}
        self._load()
        self.load_api_keys()

    def _load(self):
        if not os.path.exists(self._path):
            self.save()
            return
        try:
            with open(self._path, 'r') as f:
                user_data = json.load(f)
                self._data.update(user_data)
        except Exception:
            pass

    def load_api_keys(self):
        """Loads API credentials from environment variables or a local .env file."""
        self._keys = {
            "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
            "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", "")
        }

        # Check local .env file
        env_path = os.path.join(os.path.dirname(self._path), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip().upper()
                        v = v.strip().strip('"').strip("'")
                        if k == "GEMINI_API_KEY":
                            self._keys["gemini_api_key"] = v
                        elif k == "ANTHROPIC_API_KEY":
                            self._keys["anthropic_api_key"] = v
                        elif k == "OPENAI_API_KEY":
                            self._keys["openai_api_key"] = v
            except Exception:
                pass

        # Migration logic: if an old key exists in config.json, move it to .env
        old_key = self._data.pop("api_key", None)
        if old_key and old_key != "YOUR_GOOGLE_API_KEY_HERE" and not self._keys["gemini_api_key"]:
            self._keys["gemini_api_key"] = old_key
            self.save_api_keys(
                old_key,
                self._keys["anthropic_api_key"],
                self._keys["openai_api_key"]
            )
            self.save()  # Persist config.json without "api_key"

    def get_api_key(self, provider_name: str) -> str:
        """Retrieve the API key for the specified provider."""
        provider = provider_name.lower()
        if "gemini" in provider:
            return self._keys.get("gemini_api_key", "")
        elif "claude" in provider or "anthropic" in provider:
            return self._keys.get("anthropic_api_key", "")
        elif "chatgpt" in provider or "openai" in provider:
            return self._keys.get("openai_api_key", "")
        return ""

    def save_api_keys(self, gemini_key: str, anthropic_key: str, openai_key: str):
        """Persist API keys to a secure local .env file."""
        self._keys["gemini_api_key"] = gemini_key.strip()
        self._keys["anthropic_api_key"] = anthropic_key.strip()
        self._keys["openai_api_key"] = openai_key.strip()

        env_path = os.path.join(os.path.dirname(self._path), ".env")
        try:
            with open(env_path, "w") as f:
                f.write(f"GEMINI_API_KEY={self._keys['gemini_api_key']}\n")
                f.write(f"ANTHROPIC_API_KEY={self._keys['anthropic_api_key']}\n")
                f.write(f"OPENAI_API_KEY={self._keys['openai_api_key']}\n")
        except Exception as e:
            print(f"[ConfigManager] Error writing .env: {e}")

    def get(self, key, fallback=None):
        return self._data.get(key, fallback)

    def set(self, key, value):
        self._data[key] = value

    def save(self):
        with open(self._path, 'w') as f:
            json.dump(self._data, f, indent=4)

    @property
    def data(self):
        return dict(self._data)
