"""
================================================================================
File:         app_shell.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Main CustomTkinter application window shell and layout coordinator
================================================================================
"""

import os
import queue
import shutil
import customtkinter as ctk
from customtkinter import filedialog

from gui.status_panel import StatusPanel
from gui.connection_panel import ConnectionPanel
from gui.generation_panel import GenerationPanel
from gui.log_console import LogConsole
from gui.results_table import ResultsTable
from gui.ai_console import AIConsole
from gui.settings_dialog import SettingsDialog
from gui.info_dialog import InfoDialog
from gui.live_graph import LiveWaveformGraph, LiveThroughputGraph
from gui.profile_rules_tab import ProfileRulesTab
from ai.gemini_provider import GeminiProvider
from ai.mock_provider import MockProvider


class App(ctk.CTk):
    """Main application window composing all tabbed panels and widgets."""

    def __init__(self, engine, ai, config, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.ai = ai
        self.config = config

        # Set theme and appearance mode
        ctk.set_appearance_mode(self.config.get("theme", "Light"))
        ctk.set_default_color_theme("dark-blue")

        self.title(f"HIL Verification Dashboard - {self.engine.profile.device_name}")
        self.geometry("1280x850")
        self.minsize(1024, 768)

        # Set grid layout weight allocations
        self.grid_rowconfigure(0, weight=0)  # StatusPanel
        self.grid_rowconfigure(1, weight=1)  # Tabview container
        self.grid_columnconfigure(0, weight=1)

        # Create thread-safe queue for logging communication
        self.log_queue = queue.Queue()
        self.engine.log_callback = self.queue_logger

        self.setup_ui()

        # Start log queue polling loop
        self.after(100, self.process_log_queue)

    def setup_ui(self):
        """Construct the top-tabbed dashboard and nest all modular panels."""
        # --- Row 0: Status bar header ---
        self.status_panel = StatusPanel(self, self.engine.profile)
        self.status_panel.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        # --- Row 1: Master Tabview ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Add tabs
        tab_dash = self.tabview.add("Dashboard")
        tab_log = self.tabview.add("Execution Log")
        tab_history = self.tabview.add("Run History")
        tab_rules = self.tabview.add("Device Specifications")
        tab_ai = self.tabview.add("AI Diagnostics")

        # ======================================================================
        # TAB 1: DASHBOARD (Controls + Live Waveforms)
        # ======================================================================
        tab_dash.grid_rowconfigure(0, weight=0)  # Controls Row
        tab_dash.grid_rowconfigure(1, weight=1)  # Live Waveform Graph
        tab_dash.grid_rowconfigure(2, weight=1)  # Live Throughput Graph
        tab_dash.grid_columnconfigure(0, weight=1)

        # --- Top controls grid ---
        controls_frame = ctk.CTkFrame(tab_dash, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        controls_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="controls")

        # Connection panel (left)
        self.conn_panel = ConnectionPanel(
            controls_frame,
            engine=self.engine,
            config=self.config,
            on_status_change=self.on_status_change
        )
        self.conn_panel.grid(row=0, column=0, sticky="nsew", padx=6, pady=0)

        # Generation panel (center)
        self.gen_panel = GenerationPanel(
            controls_frame,
            engine=self.engine,
            ai_provider=self.ai,
            profile=self.engine.profile,
            log_callback=self.queue_logger,
            on_ai_output=self.on_ai_output,
            on_status_change=self.on_status_change,
            on_table_row=self.on_table_row
        )
        self.gen_panel.grid(row=0, column=1, sticky="nsew", padx=6, pady=0)

        # System operations panel (right)
        ops_frame = ctk.CTkFrame(controls_frame)
        ops_frame.grid(row=0, column=2, sticky="nsew", padx=6, pady=0)

        ctk.CTkLabel(
            ops_frame, text="System Operations",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=16, pady=(14, 8))

        ctk.CTkButton(
            ops_frame, text="Upload CSV Batch", height=32,
            command=self.upload_and_run_csv,
            fg_color="#0284c7", hover_color="#0369a1",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(fill="x", padx=16, pady=(0, 10))

        btn_row = ctk.CTkFrame(ops_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_row, text="Settings", height=32,
            command=self.open_settings,
            fg_color=("#475569", "#334155"), hover_color=("#334155", "#1e293b"),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_row, text="App Info", height=32,
            command=self.open_app_info,
            fg_color=("#475569", "#334155"), hover_color=("#334155", "#1e293b"),
            font=ctk.CTkFont(size=11)
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # --- Bottom Logic Analyser & Throughput Graphs ---
        self.waveform_graph = LiveWaveformGraph(tab_dash, self.engine.profile)
        self.waveform_graph.grid(row=1, column=0, sticky="nsew", padx=14, pady=(6, 4))

        self.throughput_graph = LiveThroughputGraph(tab_dash, self.engine.profile)
        self.throughput_graph.grid(row=2, column=0, sticky="nsew", padx=14, pady=(4, 14))

        # ======================================================================
        # TAB 2: EXECUTION LOG
        # ======================================================================
        tab_log.grid_rowconfigure(0, weight=1)
        tab_log.grid_columnconfigure(0, weight=1)
        self.log_console = LogConsole(tab_log)
        self.log_console.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # ======================================================================
        # TAB 3: RUN HISTORY
        # ======================================================================
        tab_history.grid_rowconfigure(0, weight=1)
        tab_history.grid_columnconfigure(0, weight=1)
        self.results_table = ResultsTable(
            tab_history,
            engine=self.engine,
            log_callback=self.queue_logger
        )
        self.results_table.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # ======================================================================
        # TAB 4: DEVICE SPECIFICATIONS
        # ======================================================================
        tab_rules.grid_rowconfigure(0, weight=1)
        tab_rules.grid_columnconfigure(0, weight=1)
        self.rules_tab = ProfileRulesTab(tab_rules, self.engine.profile, config=self.config)
        self.rules_tab.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # ======================================================================
        # TAB 5: AI DIAGNOSTICS
        # ======================================================================
        tab_ai.grid_rowconfigure(0, weight=1)
        tab_ai.grid_columnconfigure(0, weight=1)
        self.ai_console = AIConsole(
            tab_ai,
            engine=self.engine,
            ai_provider=self.ai,
            profile=self.engine.profile,
            on_status_change=self.on_status_change
        )
        self.ai_console.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # --- Callbacks / Interface Methods ---
    def on_status_change(self, state: str, detail: str, colour: str):
        """Update system state descriptors on StatusPanel."""
        self.status_panel.update_status(state, detail, colour)

    def on_ai_output(self, text: str):
        """Append Gemini diagnostic outputs into the AI Console."""
        self.ai_console.append_text(text)

    def on_table_row(self, filename: str, status: str, result: str):
        """Append test summary items into ResultsTable."""
        self.results_table.add_row(filename, status, result)

    def queue_logger(self, msg: str, level: str = "INFO"):
        """Interface method matching TestEngine log_callback signature."""
        self.log_queue.put((msg, level))

    def upload_and_run_csv(self):
        """Launch file prompt to upload verification batch into queue directory."""
        filepath = filedialog.askopenfilename(
            title="Select CSV Test File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filepath:
            filename = os.path.basename(filepath)
            dest = os.path.join(self.engine.queue_dir, filename)
            try:
                shutil.copy(filepath, dest)
                self.queue_logger(f"Uploaded {filename} to queue.")
                self.on_status_change("PROCESSING", f"Queued {filename}", "#2979ff")
                self.on_table_row(filename, "Queued", "Pending")

                if not self.engine.connected:
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "Hardware Disconnected",
                        "The CSV file has been uploaded to the queue, but it will not run automatically until the hardware connection is established.\n\n"
                        "Please click 'Connect' on the connection panel to start execution."
                    )
            except Exception as e:
                self.queue_logger(f"File upload error: {e}", "ERROR")
                from tkinter import messagebox
                messagebox.showerror(
                    "Upload Error",
                    f"Failed to upload the CSV test file:\n\n{e}"
                )

    def open_settings(self):
        """Load modal configuration settings panel."""
        SettingsDialog(self, self.config, on_save_callback=self._on_settings_saved)

    def open_app_info(self):
        """Load modal information window."""
        InfoDialog(self, self.engine.profile)

    def _on_settings_saved(self):
        """Callback to reinitialise the profile, driver, and AI provider dynamically."""
        try:
            # Stop watchdog and disconnect first to free ports
            self.engine.stop_watchdog()
            self.engine.disconnect()

            # 1. Update Device Profile
            profile_name = self.config.get("device_profile", "16-bit ALU")
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
            saved_gen = self.config.get(gen_key)
            saved_anal = self.config.get(anal_key)
            if saved_gen:
                profile.ai_generation_prompt = saved_gen
            if saved_anal:
                profile.ai_analysis_prompt = saved_anal

            # 2. Update Driver
            driver_name = self.config.get("comm_driver", "UART (Serial)")
            if driver_name == "Mock (Simulation)":
                from drivers.mock_driver import MockDriver
                driver = MockDriver(profile=profile)
            else:
                from drivers.uart_driver import UARTDriver
                port = self.config.get("default_port", "COM6")
                baud = int(self.config.get("baud_rate", 921600))
                driver = UARTDriver(port=port, baud_rate=baud)

            # 3. Update AI Provider
            ai_name = self.config.get("ai_provider", "Google Gemini")
            model_name = self.config.get("gemini_model", "gemini-2.5-pro")
            api_key = self.config.get_api_key(ai_name)

            if ai_name != "Mock/Offline" and not api_key:
                self.queue_logger(f"WARNING: API key for '{ai_name}' is missing. AI actions will run in Mock/Offline mode until configured in Settings.", "WARN")

            if ai_name == "Google Gemini" and api_key:
                self.ai = GeminiProvider(api_key=api_key, model_name=model_name)
            elif ai_name == "Anthropic Claude" and api_key:
                try:
                    from ai.claude_provider import ClaudeProvider
                    self.ai = ClaudeProvider(api_key=api_key, model_name=model_name)
                except ImportError as e:
                    self.queue_logger(str(e), "ERROR")
                    self.ai = MockProvider()
            elif ai_name == "OpenAI ChatGPT" and api_key:
                try:
                    from ai.chatgpt_provider import ChatGPTProvider
                    self.ai = ChatGPTProvider(api_key=api_key, model_name=model_name)
                except ImportError as e:
                    self.queue_logger(str(e), "ERROR")
                    self.ai = MockProvider()
            else:
                self.ai = MockProvider()

            # Update engine references using dependency injection
            self.engine.driver = driver
            self.engine.profile = profile
            self.engine.port = getattr(driver, 'port', 'N/A')
            self.engine.baud = getattr(driver, 'baud_rate', 0)

            # Update title
            self.title(f"HIL Verification Dashboard - {profile.device_name}")

            # Update dependent GUI panels
            self.status_panel.profile = profile
            self.status_panel.device_label.configure(text=profile.device_name)
            
            self.gen_panel.profile = profile
            self.gen_panel.ai = self.ai
            
            self.ai_console.profile = profile
            self.ai_console.set_ai_provider(self.ai)

            # Refresh rules and logic analyser layouts
            self.rules_tab.update_profile(profile)
            self.waveform_graph.update_profile(profile)
            self.throughput_graph.update_profile(profile)

            # Sync connection panel states
            self.conn_panel.port_var.set(self.engine.port)
            self.conn_panel.baud_var.set(str(self.engine.baud))
            self.conn_panel._set_connected(False)  # Disconnect visual state

            self.on_status_change("IDLE", "Settings Applied / Hardware Swapped", "gray")
            self.queue_logger(f"Dynamic Swap: Profile='{profile.device_name}' Driver='{type(driver).__name__}' AI='{type(self.ai).__name__}'")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror(
                "Configuration Error",
                f"Failed to apply the settings modifications:\n\n{e}"
            )

    def process_log_queue(self):
        """Main thread loop polling the thread-safe queue for engine updates."""
        while not self.log_queue.empty():
            msg, level = self.log_queue.get()

            # Handle connection lost
            if "[CONNECTION_LOST]" in msg:
                self.conn_panel._set_connected(False)
                self.on_status_change("ERROR", "Connection Lost", "#ff1744")
                from tkinter import messagebox
                messagebox.showerror(
                    "Connection Lost",
                    f"Hardware communication was interrupted:\n\n{msg.replace('[CONNECTION_LOST]', '').strip()}\n\n"
                    "The framework has automatically disconnected. Please check the physical USB/Serial cabling."
                )
                continue

            # Handle progress initiation
            if "[PROGRESS_START]" in msg:
                self.status_panel.update_progress(0.0, "Initiating verification sequence...")
                self.waveform_graph.clear()
                self.throughput_graph.clear()
                continue

            # Handle periodic progress updates
            elif "[PROGRESS]" in msg:
                try:
                    parts = msg.split("|")
                    if len(parts) >= 4:
                        pct_part = parts[0].split("[PROGRESS]")[1].strip().rstrip("%")
                        pct = float(pct_part) / 100.0
                        tests = parts[1].strip()
                        elapsed = parts[2].split("Elapsed:")[1].strip()
                        eta = parts[3].split("ETA:")[1].strip()

                        self.status_panel.update_progress(
                            pct, f"Running: {tests} | Elapsed: {elapsed} | ETA: {eta}"
                        )
                    if len(parts) >= 5 and "Rate:" in parts[4]:
                        rate_part = parts[4].split("Rate:")[1].split("tests/sec")[0].strip()
                        self.throughput_graph.append_point(float(rate_part))
                except Exception:
                    pass
                continue

            # Handle job summaries
            elif "SUMMARY:" in msg:
                self.after(500, lambda: self.status_panel.update_progress(0.0, ""))
                try:
                    lines = msg.split("\n")
                    filename = ""
                    result = ""
                    score = "Completed"
                    for line in lines:
                        if "SUMMARY:" in line:
                            filename = line.split("SUMMARY:")[1].strip()
                        elif "Result:" in line:
                            result = line.split("Result:")[1].strip()
                        elif "Score:" in line:
                            score = line.split("Score:")[1].strip()
                        elif "Throughput:" in line:
                            try:
                                tps_part = line.split("Throughput:")[1].split("tests/sec")[0].strip()
                                self.throughput_graph.append_point(float(tps_part))
                            except Exception:
                                pass

                    if filename:
                        self.on_table_row(filename, result, score)
                        self.on_status_change("READY", f"Verified {filename}", "#00c853")
                except Exception:
                    pass

            # Parse structured trace data to feed the live logic analyser canvas
            elif "[LOGIC_ANALYSER_DATA]" in msg:
                try:
                    import json
                    json_str = msg.split("[LOGIC_ANALYSER_DATA]")[1].strip()
                    data = json.loads(json_str)
                    self.waveform_graph.append_point(data)
                except Exception:
                    pass
                continue

            # Output standard lines to console display
            self.log_console.append_log(msg, level)

        self.after(100, self.process_log_queue)
