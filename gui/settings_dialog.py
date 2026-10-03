"""
********************************************************************************
* MODULE:       settings_dialog.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Modal dialog popup for configuring application settings. Features a General
* settings tab (with secure API key inputs) and an Advanced tab (to swap
* hardware drivers, device profiles, AI backends, and model parameters).
********************************************************************************
"""
import customtkinter as ctk


class SettingsDialog(ctk.CTkToplevel):
    """Configuration settings popup window with General and Advanced tabs."""

    def __init__(self, parent, config_manager, on_save_callback=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config_manager = config_manager
        self.on_save_callback = on_save_callback

        self.title("System Settings")
        self.geometry("460x580")
        self.resizable(False, False)
        
        # Bring to front and grab focus
        self.attributes("-topmost", True)
        self.grab_set()

        # --- Header ---
        ctk.CTkLabel(
            self, text="Configuration Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(16, 4))

        # --- Tabview ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        
        # Add tabs
        self.tab_general = self.tabview.add("General")
        self.tab_advanced = self.tabview.add("Advanced")

        # ======================================================================
        # TAB 1: GENERAL SETTINGS (UI & Secure Keys)
        # ======================================================================
        # Visual Delay
        ctk.CTkLabel(
            self.tab_general, text="Visual Delay (seconds per test):",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(6, 2))
        
        self.delay_var = ctk.StringVar(
            value=str(self.config_manager.get("visual_delay", 0.0))
        )
        ctk.CTkEntry(self.tab_general, textvariable=self.delay_var, height=28).pack(
            fill="x", padx=16, pady=(0, 8)
        )

        # Gemini API Key
        ctk.CTkLabel(
            self.tab_general, text="Google Gemini API Key:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.gemini_key_var = ctk.StringVar(
            value=self.config_manager.get_api_key("Gemini")
        )
        ctk.CTkEntry(self.tab_general, textvariable=self.gemini_key_var, show="*", height=28).pack(
            fill="x", padx=16, pady=(0, 8)
        )

        # Claude API Key
        ctk.CTkLabel(
            self.tab_general, text="Anthropic Claude API Key:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.claude_key_var = ctk.StringVar(
            value=self.config_manager.get_api_key("Claude")
        )
        ctk.CTkEntry(self.tab_general, textvariable=self.claude_key_var, show="*", height=28).pack(
            fill="x", padx=16, pady=(0, 8)
        )

        # ChatGPT API Key
        ctk.CTkLabel(
            self.tab_general, text="OpenAI ChatGPT API Key:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.chatgpt_key_var = ctk.StringVar(
            value=self.config_manager.get_api_key("ChatGPT")
        )
        ctk.CTkEntry(self.tab_general, textvariable=self.chatgpt_key_var, show="*", height=28).pack(
            fill="x", padx=16, pady=(0, 8)
        )

        # Theme Selector
        ctk.CTkLabel(
            self.tab_general, text="Interface Theme Mode:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.theme_var = ctk.StringVar(
            value=self.config_manager.get("theme", "Dark")
        )
        ctk.CTkOptionMenu(
            self.tab_general, variable=self.theme_var, values=["Dark", "Light"], height=28
        ).pack(fill="x", padx=16, pady=(0, 10))

        # ======================================================================
        # TAB 2: ADVANCED CONFIGURATIONS (Modularity Options)
        # ======================================================================
        # Device Profile
        ctk.CTkLabel(
            self.tab_advanced, text="Device Profile:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(10, 2))
        
        self.profile_var = ctk.StringVar(
            value=self.config_manager.get("device_profile", "16-bit ALU")
        )
        ctk.CTkOptionMenu(
            self.tab_advanced, variable=self.profile_var,
            values=["16-bit ALU", "8-bit ALU", "3-to-5 Encoder"], height=30
        ).pack(fill="x", padx=16, pady=(0, 8))

        # Communication Driver
        ctk.CTkLabel(
            self.tab_advanced, text="Communication Driver:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.driver_var = ctk.StringVar(
            value=self.config_manager.get("comm_driver", "UART (Serial)")
        )
        ctk.CTkOptionMenu(
            self.tab_advanced, variable=self.driver_var,
            values=["UART (Serial)", "Mock (Simulation)"], height=30
        ).pack(fill="x", padx=16, pady=(0, 8))

        # AI Provider
        ctk.CTkLabel(
            self.tab_advanced, text="AI Provider Backend:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.ai_var = ctk.StringVar(
            value=self.config_manager.get("ai_provider", "Google Gemini")
        )
        self.ai_menu = ctk.CTkOptionMenu(
            self.tab_advanced, variable=self.ai_var,
            values=["Google Gemini", "Anthropic Claude", "OpenAI ChatGPT", "Mock/Offline"],
            command=self._on_provider_changed, height=30
        )
        self.ai_menu.pack(fill="x", padx=16, pady=(0, 8))

        # AI Model (updated dynamically based on provider)
        ctk.CTkLabel(
            self.tab_advanced, text="AI Model Parameters:",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60")
        ).pack(anchor="w", padx=16, pady=(4, 2))
        
        self.model_var = ctk.StringVar(
            value=self.config_manager.get("gemini_model", "gemini-2.5-pro")
        )
        self.model_menu = ctk.CTkOptionMenu(
            self.tab_advanced, variable=self.model_var,
            values=["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
            height=30
        )
        self.model_menu.pack(fill="x", padx=16, pady=(0, 16))

        # Set initial dynamic models dropdown state
        self._on_provider_changed(self.ai_var.get())

        # ======================================================================
        # BUTTON ROW
        # ======================================================================
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 16))

        ctk.CTkButton(
            btn_row, text="Cancel", width=90,
            command=self.destroy,
            fg_color=("#e2e8f0", "#4a5568"),
            text_color=("#1a202c", "#f7fafc"),
            hover_color=("#cbd5e0", "#3f4856")
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Save & Apply", width=120,
            command=self._save_settings,
            fg_color="#00c853", hover_color="#00e676"
        ).pack(side="right")

    def _on_provider_changed(self, choice: str):
        """Update available models list dynamically based on provider selection."""
        if choice == "Google Gemini":
            models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
            default_model = "gemini-2.5-pro"
        elif choice == "Anthropic Claude":
            models = ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
            default_model = "claude-3-5-sonnet-latest"
        elif choice == "OpenAI ChatGPT":
            models = ["gpt-4o", "gpt-4o-mini"]
            default_model = "gpt-4o"
        else:
            models = ["Mock"]
            default_model = "Mock"

        self.model_menu.configure(values=models)
        # Only set if the current selection is not in the new valid models list
        if self.model_var.get() not in models:
            self.model_var.set(default_model)

    def _save_settings(self):
        # Validate visual delay
        try:
            val = float(self.delay_var.get())
            if val < 0:
                raise ValueError("Delay must be non-negative")
        except ValueError:
            from tkinter import messagebox
            messagebox.showwarning(
                "Invalid Input",
                "Please enter a valid non-negative number for the visual delay."
            )
            return

        # Validate API key presence for the selected AI Provider
        ai_provider = self.ai_var.get()
        api_key = ""
        if ai_provider == "Google Gemini":
            api_key = self.gemini_key_var.get().strip()
        elif ai_provider == "Anthropic Claude":
            api_key = self.claude_key_var.get().strip()
        elif ai_provider == "OpenAI ChatGPT":
            api_key = self.chatgpt_key_var.get().strip()

        if ai_provider != "Mock/Offline" and not api_key:
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Missing API Key",
                f"You have selected '{ai_provider}' but the API key field is empty.\n\n"
                "Do you want to save anyway? (AI diagnostics will run in offline simulation mode.)"
            ):
                return

        # Update theme configuration
        new_theme = self.theme_var.get()
        self.config_manager.set("theme", new_theme)
        ctk.set_appearance_mode(new_theme)

        try:
            # Set visual delay
            self.config_manager.set("visual_delay", val)

            # Save API keys to environment secrets (.env)
            self.config_manager.save_api_keys(
                self.gemini_key_var.get(),
                self.claude_key_var.get(),
                self.chatgpt_key_var.get()
            )

            # Save modular selections to settings file
            self.config_manager.set("device_profile", self.profile_var.get())
            self.config_manager.set("comm_driver", self.driver_var.get())
            self.config_manager.set("ai_provider", self.ai_var.get())
            self.config_manager.set("gemini_model", self.model_var.get())  # Reuses gemini_model key for active model name

            # Persist settings configuration
            self.config_manager.save()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Save Error", f"Failed to save settings configuration:\n\n{e}")
            return

        # Fire callbacks
        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
