"""
********************************************************************************
* MODULE:       log_console.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Real-time console widget for displaying system logs. Features auto-scrolling
* and colour-coded message lines based on logging severity (INFO, WARN, ERROR).
********************************************************************************
"""
import tkinter as tk
import customtkinter as ctk


class LogConsole(ctk.CTkFrame):
    """Real-time scrollable log console widget."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 6))
        
        ctk.CTkLabel(
            header_frame, text="REALTIME LOG CONSOLE",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_frame, text="[Active]",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00e676"
        ).pack(side="right")

        # --- Console Textbox ---
        self.console = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.console.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # --- Configure text tags ---
        self.console.tag_config("INFO")
        self.console.tag_config("WARN", foreground="#ffab00")
        self.console.tag_config("ERROR", foreground="#ff1744")

    def append_log(self, message: str, level: str = "INFO"):
        """Append a message to the console with the corresponding colour/tag."""
        self.console.configure(state="normal")
        self.console.insert(tk.END, message + "\n", level)
        self.console.see(tk.END)
        self.console.configure(state="disabled")

    def clear(self):
        """Clear all content from the console."""
        self.console.configure(state="normal")
        self.console.delete("1.0", tk.END)
        self.console.configure(state="disabled")
