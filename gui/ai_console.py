"""
================================================================================
File:         ai_console.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Interactive LLM prompt and test generation console UI panel
================================================================================
"""

import os
import glob
import threading
import tkinter as tk
import customtkinter as ctk


class AIConsole(ctk.CTkFrame):
    """Console widget for display of AI actions and logging diagnostics."""

    def __init__(self, master, engine, ai_provider, profile,
                 on_status_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self.engine = engine
        self.ai = ai_provider
        self.profile = profile
        self.on_status_change = on_status_change

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            header_frame, text="AI Console",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        self.btn_analyse = ctk.CTkButton(
            header_frame, text="Analyse Logs", width=90, height=26,
            fg_color="#7c3aed", hover_color="#6d28d9",
            command=self.trigger_analysis,
            font=ctk.CTkFont(size=11)
        )
        self.btn_analyse.pack(side="right")

        # --- AI Textbox ---
        self.console = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.console.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.console.insert(
            tk.END, "Model Configured: Gemini Pro\nStatus: Ready for diagnostic analysis.\n"
        )
        self.console.configure(state="disabled")

    def append_text(self, text: str):
        """Thread-safe append text to the console."""
        self.console.configure(state="normal")
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)
        self.console.configure(state="disabled")

    def set_ai_provider(self, ai_provider):
        """Update the active AI provider instance."""
        self.ai = ai_provider

    def trigger_analysis(self):
        """Initiate asynchronous log analysis on the latest verification file."""
        if not self.ai or type(self.ai).__name__ == "MockProvider":
            from tkinter import messagebox
            messagebox.showwarning(
                "AI Not Configured",
                "The selected AI Provider is not configured or is operating offline.\n\n"
                "Please add a valid API key in Settings to use the log analysis feature."
            )
            self.append_text("\n[ERROR] AI Provider is not configured. Add an API Key in settings.")
            return

        r_dir = getattr(self.engine, 'results_dir', '.')
        if not os.path.exists(r_dir):
            from tkinter import messagebox
            messagebox.showwarning(
                "No Logs Found",
                "Results directory does not exist.\n\n"
                "Please run a verification batch first to generate log files."
            )
            self.append_text("\n[ERROR] Results directory does not exist.")
            return

        files = glob.glob(os.path.join(r_dir, "*.log"))
        if not files:
            from tkinter import messagebox
            messagebox.showwarning(
                "No Logs Found",
                "No test log files were found to analyse.\n\n"
                "Please run a verification batch first to generate log files."
            )
            self.append_text("\n[INFO] No test log files found to analyse.")
            return

        latest_log = max(files, key=os.path.getctime)
        self.append_text(f"\nAnalysing {os.path.basename(latest_log)}...")
        
        if self.on_status_change:
            self.on_status_change("BUSY", "AI Analysing...", "#ffab00")

        threading.Thread(
            target=self._async_analyse, args=(latest_log,), daemon=True
        ).start()

    def _async_analyse(self, filepath):
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Request analysis using the profile-specific prompt
            analysis = self.ai.analyse_log(content, self.profile.ai_analysis_prompt)

            raw_debug = (
                f"\n[Gemini Request]\n{self.ai.last_request}\n"
                f"\n[Gemini Raw Response]\n{self.ai.last_raw_response}\n"
                f"\n[AI Analysis]\n{analysis}\n"
            )
            
            self.after(0, self._finish_analysis, raw_debug)
        except Exception as e:
            self.after(0, self._analysis_failed, str(e))

    def _finish_analysis(self, raw_debug: str):
        self.append_text(raw_debug)
        if self.on_status_change:
            self.on_status_change("IDLE", "Analysis Complete", "#00c853")

    def _analysis_failed(self, error_msg: str):
        self.append_text(f"\n[AI Analyse Error]\n{error_msg}")
        if self.on_status_change:
            self.on_status_change("ERROR", "API Failure", "#ff1744")
        from tkinter import messagebox
        messagebox.showerror(
            "AI Analysis Failed",
            f"An error occurred during log analysis:\n\n{error_msg}"
        )
