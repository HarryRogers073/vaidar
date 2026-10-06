"""
================================================================================
File:         app.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Application entry point and composition root for VAIDAR HIL framework
================================================================================
"""

import os
import sys

# Ensure project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config_manager import ConfigManager
from core.engine import TestEngine
from drivers.uart_driver import UARTDriver
from profiles.alu_16bit import ALU16BitProfile
from ai.gemini_provider import GeminiProvider
from ai.mock_provider import MockProvider
from gui.app_shell import App


def main():
    # Load settings
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    config = ConfigManager(path=config_path)

    # 1. Instantiate profile dynamically
    profile_name = config.get("device_profile", "16-bit ALU")
    if profile_name == "8-bit ALU":
        from profiles.alu_8bit import ALU8BitProfile
        profile = ALU8BitProfile()
    elif profile_name == "3-to-5 Encoder":
        from profiles.encoder_3to5 import Encoder3to5Profile
        profile = Encoder3to5Profile()
    else:
        from profiles.alu_16bit import ALU16BitProfile
        profile = ALU16BitProfile()

    # Load custom prompts if saved in config
    gen_key = f"prompt_gen_{profile.device_name.lower().replace(' ', '_')}"
    anal_key = f"prompt_anal_{profile.device_name.lower().replace(' ', '_')}"
    saved_gen = config.get(gen_key)
    saved_anal = config.get(anal_key)
    if saved_gen:
        profile.ai_generation_prompt = saved_gen
    if saved_anal:
        profile.ai_analysis_prompt = saved_anal

    # 2. Instantiate driver dynamically
    driver_name = config.get("comm_driver", "UART (Serial)")
    if driver_name == "Mock (Simulation)":
        from drivers.mock_driver import MockDriver
        driver = MockDriver(profile=profile)
    else:
        from drivers.uart_driver import UARTDriver
        port = config.get("default_port", "COM6")
        baud = int(config.get("baud_rate", 921600))
        driver = UARTDriver(port=port, baud_rate=baud)

    # 3. Wire up the engine orchestration layer using dependency injection
    engine = TestEngine(driver=driver, profile=profile)

    # 4. Determine AI Provider backend dynamically
    ai_name = config.get("ai_provider", "Google Gemini")
    model_name = config.get("gemini_model", "gemini-2.5-pro")
    api_key = config.get_api_key(ai_name)

    if ai_name != "Mock/Offline" and not api_key:
        print(f"WARNING: API key for '{ai_name}' is missing. AI will operate in Mock/Offline mode.")

    if ai_name == "Google Gemini" and api_key:
        try:
            ai = GeminiProvider(api_key=api_key, model_name=model_name)
        except Exception as e:
            print(f"Error initialising Gemini: {e}")
            ai = MockProvider()
    elif ai_name == "Anthropic Claude" and api_key:
        try:
            from ai.claude_provider import ClaudeProvider
            ai = ClaudeProvider(api_key=api_key, model_name=model_name)
        except Exception as e:
            print(f"Error initialising Claude: {e}")
            ai = MockProvider()
    elif ai_name == "OpenAI ChatGPT" and api_key:
        try:
            from ai.chatgpt_provider import ChatGPTProvider
            ai = ChatGPTProvider(api_key=api_key, model_name=model_name)
        except Exception as e:
            print(f"Error initialising ChatGPT: {e}")
            ai = MockProvider()
    else:
        ai = MockProvider()

    # Start the graphical user interface application
    print(f"Starting HIL Verification Suite for: {profile.device_name}")
    app = App(engine=engine, ai=ai, config=config)
    app.mainloop()


if __name__ == "__main__":
    main()
