"""
********************************************************************************
* MODULE:       results_table.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Table widget that lists verification run summaries. Shows the job ID,
* filename, run status, and actual pass/fail or local/AI outcome.
* Includes a quick action to open the latest log file.
********************************************************************************
"""
import os
import glob
import customtkinter as ctk


class ResultsTable(ctk.CTkFrame):
    """Widget showing historical run results in a grid list."""

    def __init__(self, master, engine, log_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.engine = engine
        self.log_callback = log_callback
        self.job_counter = 1

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            header_frame, text="Latest Results Summary",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header_frame, text="Open Last Log", width=90, height=26,
            fg_color=("#4a5568", "#2d3748"),
            hover_color=("#3f4856", "#1a202c"),
            command=self.open_last_result,
            font=ctk.CTkFont(size=11)
        ).pack(side="right")

        # --- Table container ---
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # --- Table headers ---
        headers = ["Job ID", "File Name", "Status", "Result"]
        for col_idx, h_text in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.scroll_frame, text=h_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray40", "gray70")
            )
            lbl.grid(row=0, column=col_idx, padx=6, pady=4, sticky="w")

    def _log(self, msg, level="INFO"):
        if self.log_callback:
            self.log_callback(msg, level)

    def add_row(self, filename: str, status: str, result: str):
        """Append a new result record row to the table."""
        row_idx = self.job_counter
        self.job_counter += 1

        # Job ID
        ctk.CTkLabel(
            self.scroll_frame, text=f"#{row_idx}",
            font=ctk.CTkFont(size=11, family="Consolas")
        ).grid(row=row_idx, column=0, padx=6, pady=2, sticky="w")

        # Filename (truncate if long)
        display_name = filename if len(filename) < 18 else filename[:15] + "..."
        ctk.CTkLabel(
            self.scroll_frame, text=display_name,
            font=ctk.CTkFont(size=11)
        ).grid(row=row_idx, column=1, padx=6, pady=2, sticky="w")

        # Status
        status_colour = "#00c853" if status.lower() in ["done", "pass", "generated"] else "#ff1744"
        if status.lower() == "queued":
            status_colour = "#2979ff"

        ctk.CTkLabel(
            self.scroll_frame, text=status,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_colour
        ).grid(row=row_idx, column=2, padx=6, pady=2, sticky="w")

        # Result
        ctk.CTkLabel(
            self.scroll_frame, text=result,
            font=ctk.CTkFont(size=11)
        ).grid(row=row_idx, column=3, padx=6, pady=2, sticky="w")

    def open_last_result(self):
        """Find the latest log file in results and launch it with OS defaults."""
        r_dir = getattr(self.engine, 'results_dir', '.')
        from tkinter import messagebox
        if not os.path.exists(r_dir):
            self._log(f"Results directory does not exist: {r_dir}", "ERROR")
            messagebox.showwarning(
                "No Logs Found",
                "There are no execution log files available in the results directory yet.\n\n"
                "Please run a verification batch first."
            )
            return

        files = glob.glob(os.path.join(r_dir, "*.log"))
        if not files:
            self._log("No log files found in the results directory.", "WARN")
            messagebox.showwarning(
                "No Logs Found",
                "There are no execution log files available in the results directory yet.\n\n"
                "Please run a verification batch first."
            )
            return

        latest_log = max(files, key=os.path.getctime)
        self._log(f"Opening latest log: {os.path.basename(latest_log)}")
        try:
            os.startfile(latest_log)
        except Exception as e:
            self._log(f"Failed to open log file: {e}", "ERROR")
            messagebox.showerror(
                "Error Opening Log",
                f"Failed to open the log file:\n\n{e}"
            )
