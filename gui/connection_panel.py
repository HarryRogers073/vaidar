"""
================================================================================
File:         connection_panel.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Hardware connection, serial port selector, and baud rate control panel
================================================================================
"""

import customtkinter as ctk


class ConnectionPanel(ctk.CTkFrame):
    """Sidebar panel for managing the serial connection."""

    def __init__(self, master, engine, config, on_status_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self.engine = engine
        self.config = config
        self.on_status_change = on_status_change

        # --- Header ---
        ctk.CTkLabel(
            self, text="Connection",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=16, pady=(14, 8))

        # --- Port ---
        ctk.CTkLabel(self, text="Port", font=ctk.CTkFont(size=11),
                      text_color=("gray40", "gray60")).pack(anchor="w", padx=16)
        self.port_var = ctk.StringVar(value=self.config.get("default_port", "COM6"))
        ctk.CTkEntry(self, textvariable=self.port_var, height=30).pack(
            fill="x", padx=16, pady=(2, 8))

        # --- Baud Rate ---
        ctk.CTkLabel(self, text="Baud Rate", font=ctk.CTkFont(size=11),
                      text_color=("gray40", "gray60")).pack(anchor="w", padx=16)
        self.baud_var = ctk.StringVar(
            value=str(self.config.get("baud_rate", "921600")))
        ctk.CTkOptionMenu(
            self, variable=self.baud_var,
            values=["9600", "115200", "230400", "460800", "921600"],
            height=30, dynamic_resizing=False
        ).pack(fill="x", padx=16, pady=(2, 10))

        # --- Status indicator ---
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(0, 8))

        self.status_dot = ctk.CTkLabel(
            status_row, text="●", font=ctk.CTkFont(size=16),
            text_color="#e74c3c", width=20)
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(
            status_row, text="Disconnected",
            font=ctk.CTkFont(size=11), text_color=("gray40", "gray60"))
        self.status_label.pack(side="left", padx=(4, 0))

        # --- Connect button ---
        self.btn_connect = ctk.CTkButton(
            self, text="Connect", height=34,
            command=self.toggle_connection,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.btn_connect.pack(fill="x", padx=16, pady=(0, 14))

    def toggle_connection(self):
        """Connect or disconnect from the FPGA."""
        if not self.engine.connected:
            port = self.port_var.get().strip()
            if not port:
                from tkinter import messagebox
                messagebox.showwarning(
                    "Invalid Port",
                    "Please enter a valid serial port name (e.g. COM6 or /dev/ttyUSB0)."
                )
                return

            # Update driver with current UI values
            self.engine.driver.port = port
            self.engine.driver.baud_rate = int(self.baud_var.get())
            self.engine.port = port
            self.engine.baud = int(self.baud_var.get())

            # Save to config
            self.config.set("default_port", port)
            self.config.set("baud_rate", int(self.baud_var.get()))
            self.config.save()

            if self.engine.connect():
                self._set_connected(True)
                self.engine.start_watchdog(
                    delay=float(self.config.get("visual_delay", 0.0)))
                if self.on_status_change:
                    self.on_status_change("READY", "Hardware Synchronised", "#00c853")
            else:
                if self.on_status_change:
                    self.on_status_change("ERROR", "Connection Failed", "#ff1744")
                from tkinter import messagebox
                messagebox.showerror(
                    "Connection Failed",
                    f"Failed to connect to the hardware on port {self.port_var.get()}.\n\n"
                    "Please verify that:\n"
                    "1. The correct port name and baud rate are selected.\n"
                    "2. The FPGA board is powered on and connected.\n"
                    "3. No other application (like TeraTerm or Arduino Serial Monitor) is using this port."
                )
        else:
            self.engine.stop_watchdog()
            self.engine.disconnect()
            self._set_connected(False)
            if self.on_status_change:
                self.on_status_change("IDLE", "Awaiting Connection", "gray")

    def _set_connected(self, connected: bool):
        if connected:
            self.status_dot.configure(text_color="#00c853")
            self.status_label.configure(text="Connected")
            self.btn_connect.configure(
                text="Disconnect", fg_color="#ff1744", hover_color="#d50000")
        else:
            self.status_dot.configure(text_color="#e74c3c")
            self.status_label.configure(text="Disconnected")
            self.btn_connect.configure(
                text="Connect",
                fg_color=("#3B8ED0", "#1F6AA5"),
                hover_color=("#36719F", "#144870"))
