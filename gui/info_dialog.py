"""
================================================================================
File:         info_dialog.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Application architecture and provenance information modal dialog
================================================================================
"""

import customtkinter as ctk


class InfoDialog(ctk.CTkToplevel):
    """Application metadata information popup window."""

    def __init__(self, parent, profile, **kwargs):
        super().__init__(parent, **kwargs)
        self.profile = profile

        self.title("App Information")
        self.geometry("380x320")
        self.resizable(False, False)
        
        # Bring to front and grab focus
        self.attributes("-topmost", True)
        self.grab_set()

        # --- Logo / Main Header ---
        ctk.CTkLabel(
            self, text="Software-to-Silicon",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(24, 4))
        
        ctk.CTkLabel(
            self, text="HIL & AI Verification Suite",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color=("gray40", "gray50")
        ).pack(pady=(0, 16))

        # --- Dynamic Profile Metadata ---
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=30, pady=5)

        # Developer / Author
        author_text = f"Author: {getattr(self.profile, 'author', 'Harry Rogers')}"
        ctk.CTkLabel(
            info_frame, text=author_text,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w")

        # Version
        version_text = f"Version: {getattr(self.profile, 'version', '1.0.0')}"
        ctk.CTkLabel(
            info_frame, text=version_text,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")

        # Device Under Test Name
        device_text = f"Device Profile: {getattr(self.profile, 'device_name', 'Unknown')}"
        ctk.CTkLabel(
            info_frame, text=device_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00c853"
        ).pack(anchor="w", pady=(4, 6))

        # Dynamic Description from Profile
        desc_text = getattr(self.profile, 'description', 'No description provided.')
        ctk.CTkLabel(
            self, text=desc_text, justify="center",
            font=ctk.CTkFont(size=11), wraplength=310,
            text_color=("gray20", "gray80")
        ).pack(padx=30, pady=(4, 16))

        # --- Close Button ---
        ctk.CTkButton(
            self, text="Close", width=120,
            command=self.destroy,
            fg_color=("#4a5568", "#2d3748"),
            hover_color=("#3f4856", "#1a202c")
        ).pack(pady=(0, 20))
