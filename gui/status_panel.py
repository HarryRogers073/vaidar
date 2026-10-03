"""
********************************************************************************
* MODULE:       status_panel.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* A compact header widget that displays the system state, progress bar,
* and current clock. Updated by calling the `update()` method from the
* main shell or from other panels via callbacks.
********************************************************************************
"""
import customtkinter as ctk
from datetime import datetime


class StatusPanel(ctk.CTkFrame):
    """Top header bar showing system status, progress, and clock."""

    def __init__(self, master, profile, **kwargs):
        super().__init__(master, corner_radius=8, **kwargs)
        self.profile = profile

        # --- Left: status dot + label ---
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=16, pady=8)

        self.status_dot = ctk.CTkLabel(
            left, text="●", font=ctk.CTkFont(size=18),
            text_color="gray", width=22)
        self.status_dot.pack(side="left")

        self.status_text = ctk.CTkLabel(
            left, text="IDLE",
            font=ctk.CTkFont(size=13, weight="bold"))
        self.status_text.pack(side="left", padx=(6, 0))

        self.status_detail = ctk.CTkLabel(
            left, text="Awaiting Connection",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60"))
        self.status_detail.pack(side="left", padx=(10, 0))

        # --- Centre: progress bar ---
        centre = ctk.CTkFrame(self, fg_color="transparent")
        centre.pack(side="left", fill="x", expand=True, padx=16)

        self.progress_bar = ctk.CTkProgressBar(centre, height=6)
        self.progress_bar.pack(fill="x", pady=(0, 2))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            centre, text="",
            font=ctk.CTkFont(size=10), text_color=("gray40", "gray60"))
        self.progress_label.pack(anchor="w")

        # --- Right: clock + device name ---
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=16, pady=8)

        self.clock_label = ctk.CTkLabel(
            right, text="",
            font=ctk.CTkFont(size=11, family="Consolas"),
            text_color=("gray40", "gray60"))
        self.clock_label.pack(anchor="e")

        self.device_label = ctk.CTkLabel(
            right, text=self.profile.device_name,
            font=ctk.CTkFont(size=10), text_color=("gray50", "gray55"))
        self.device_label.pack(anchor="e")

        self._tick_clock()

    def update_status(self, state: str, detail: str, colour: str):
        self.status_text.configure(text=state)
        self.status_detail.configure(text=detail)
        self.status_dot.configure(text_color=colour)

    def update_progress(self, fraction: float, text: str = ""):
        self.progress_bar.set(fraction)
        self.progress_label.configure(text=text)

    def _tick_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_label.configure(text=now)
        self.after(1000, self._tick_clock)
