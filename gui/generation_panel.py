"""
================================================================================
File:         generation_panel.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Test vector batch configuration and queue management panel
================================================================================
"""

import os
import io
import csv
import threading
from datetime import datetime

import customtkinter as ctk

from core.generate_tests import generate_test_file, calculate_flags


class GenerationPanel(ctk.CTkFrame):
    """Sidebar panel for generating test CSV files."""

    def __init__(self, master, engine, ai_provider, profile,
                 log_callback=None, on_ai_output=None,
                 on_status_change=None, on_table_row=None, **kwargs):
        super().__init__(master, **kwargs)
        self.engine = engine
        self.ai = ai_provider
        self.profile = profile
        self.log_callback = log_callback
        self.on_ai_output = on_ai_output
        self.on_status_change = on_status_change
        self.on_table_row = on_table_row

        # --- Header ---
        ctk.CTkLabel(
            self, text="Test Generation",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=16, pady=(14, 4))

        # --- Random section ---
        ctk.CTkLabel(self, text="Python Scripting", font=ctk.CTkFont(size=10),
                      text_color=("gray50", "gray55")).pack(anchor="w", padx=16, pady=(4, 2))

        self.test_count_var = ctk.StringVar(value="100")
        ctk.CTkEntry(
            self, textvariable=self.test_count_var, height=30,
            placeholder_text="Number of tests"
        ).pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkButton(
            self, text="Generate Random Tests", height=32,
            command=self._gen_random, font=ctk.CTkFont(size=11)
        ).pack(fill="x", padx=16, pady=(0, 10))

        # --- AI section ---
        ctk.CTkLabel(self, text="AI Models", font=ctk.CTkFont(size=10),
                      text_color=("gray50", "gray55")).pack(anchor="w", padx=16, pady=(4, 2))

        self.ai_prompt_var = ctk.StringVar(value="DIV edge cases")
        ctk.CTkEntry(
            self, textvariable=self.ai_prompt_var, height=30,
            placeholder_text="Describe tests..."
        ).pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkButton(
            self, text="Generate via AI", height=32,
            command=self._gen_ai, fg_color="#7c3aed", hover_color="#6d28d9",
            font=ctk.CTkFont(size=11)
        ).pack(fill="x", padx=16, pady=(0, 14))

    # ------------------------------------------------------------------
    def _log(self, msg, level="INFO"):
        if self.log_callback:
            self.log_callback(msg, level)

    def _gen_random(self):
        try:
            count = int(self.test_count_var.get())
            if count <= 0:
                raise ValueError("Count must be positive")
        except ValueError:
            from tkinter import messagebox
            messagebox.showwarning("Invalid Input", "Please enter a valid positive integer for the test count.")
            return

        try:
            filename = f"random_{datetime.now().strftime('%H%M%S')}.csv"
            filepath = os.path.join(self.engine.queue_dir, filename)
            generate_test_file(filepath, count)
            self._log(f"Generated {filename} ({count} tests)")
            if self.on_table_row:
                self.on_table_row(filename, "Generated", "Local")

            if not self.engine.connected:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Hardware Disconnected",
                    "The random test file has been generated and queued, but it will not run automatically until the hardware connection is established.\n\n"
                    "Please click 'Connect' on the connection panel to start execution."
                )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Generation Error", f"Failed to generate random tests:\n\n{e}")

    def _gen_ai(self):
        if not self.ai or type(self.ai).__name__ == "MockProvider":
            from tkinter import messagebox
            messagebox.showwarning(
                "AI Not Configured",
                "The selected AI Provider is not configured or is operating offline.\n\n"
                "Please add a valid API key in Settings to use AI test generation."
            )
            self._log("AI not configured. Check API key in Settings.", "ERROR")
            return
        prompt = self.ai_prompt_var.get().strip()
        if not prompt:
            from tkinter import messagebox
            messagebox.showwarning("Validation Error", "Please describe the test vectors you want to generate.")
            return
        threading.Thread(target=self._async_ai_gen, args=(prompt,), daemon=True).start()

    def _show_error_main_thread(self, title, msg):
        from tkinter import messagebox
        messagebox.showerror(title, msg)

    def _show_warning_main_thread(self, title, msg):
        from tkinter import messagebox
        messagebox.showwarning(title, msg)

    def _async_ai_gen(self, prompt):
        self._log("Asking AI to generate tests...", "WARN")
        if self.on_status_change:
            self.on_status_change("BUSY", "AI Generating...", "#ffab00")
        try:
            csv_text = self.ai.generate_csv_from_prompt(
                prompt, self.profile.ai_generation_prompt)

            # Push raw AI debug to AI console
            if self.on_ai_output:
                raw_debug = (
                    f"\n[Gemini Request]\n{self.ai.last_request}\n"
                    f"\n[Gemini Raw Response]\n{self.ai.last_raw_response}\n"
                )
                self.on_ai_output(raw_debug)

            if "Error" in csv_text or not csv_text.strip():
                raise Exception(csv_text if csv_text else "Empty response from AI")

            filename = f"ai_tests_{datetime.now().strftime('%H%M%S')}.csv"
            filepath = os.path.join(self.engine.queue_dir, filename)

            reader = csv.reader(io.StringIO(csv_text))
            headers = next(reader, None)

            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Operation', 'Operand A', 'Operand B',
                                 'Expected Result', 'Flag N', 'Flag Z',
                                 'Flag C', 'Flag V'])
                for row in reader:
                    if len(row) < 3:
                        continue
                    op = row[0].strip()
                    try:
                        a = int(row[1].strip())
                        b = int(row[2].strip())
                    except ValueError:
                        continue
                    res, n, z, c, v = calculate_flags(op, a, b)
                    writer.writerow([op, a, b, res, n, z, c, v])

            self._log(f"AI generated and solved {filename}")
            if self.on_table_row:
                self.on_table_row(filename, "Generated", "AI + Golden")
            if self.on_status_change:
                self.on_status_change("IDLE", "Generation Complete", "#00c853")

            if not self.engine.connected:
                self.after(0, lambda: self._show_warning_main_thread(
                    "Hardware Disconnected",
                    "The AI test file has been generated and queued, but it will not run automatically until the hardware connection is established.\n\n"
                    "Please click 'Connect' on the connection panel to start execution."
                ))

        except Exception as e:
            self._log(f"AI Error: {e}", "ERROR")
            if self.on_ai_output:
                self.on_ai_output(f"\n[AI Generation Error]\n{e}")
            if self.on_status_change:
                self.on_status_change("ERROR", "API Failure", "#ff1744")
            self.after(0, lambda: self._show_error_main_thread("AI Generation Error", f"AI test generation failed:\n\n{e}"))
