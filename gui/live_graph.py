"""
================================================================================
File:         live_graph.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Real-time throughput and signal waveform plotting widgets using Tkinter Canvas
================================================================================
"""

import tkinter as tk
import customtkinter as ctk


class LiveWaveformGraph(ctk.CTkFrame):
    """Real-time logic analyser signal viewer supporting arbitrary dynamic channels."""

    def __init__(self, master, profile, **kwargs):
        super().__init__(master, **kwargs)
        self.profile = profile
        self.history = []  # List of dicts: {"inputs": {...}, "outputs": {...}, "is_pass": bool}
        self.max_points = 45

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 4))
        
        ctk.CTkLabel(
            header_frame, text="LOGIC ANALYSER / SIGNAL WAVEFORMS",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        # --- Canvas widget ---
        self.canvas = tk.Canvas(
            self, highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Re-draw on resize
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def update_profile(self, profile):
        """Set active profile and clear history to reset scale bounds."""
        self.profile = profile
        self.history.clear()
        self.redraw()

    def append_point(self, data: dict):
        """Append a new test execution trace packet and redraw."""
        self.history.append(data)
        if len(self.history) > self.max_points:
            self.history.pop(0)
        self.redraw()

    def clear(self):
        """Reset the plot buffer."""
        self.history.clear()
        self.redraw()

    def redraw(self):
        """Clear and redraw the logic analyser grid and signal traces."""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Guard against zero sizing during Tkinter init
        if width < 50 or height < 50:
            return

        # Fetch theme-dependent colours dynamically
        theme = ctk.get_appearance_mode().lower()
        if theme == "dark":
            bg_colour = "#0f172a"          # slate-900
            grid_colour = "#1e293b"        # slate-800
            grid_sub_colour = "#334155"    # slate-700
            text_colour = "#94a3b8"        # slate-400
            ch1_colour = "#00e676"         # bright green
            ch2_colour = "#00b0ff"         # bright blue
            ch3_colour = "#ff6d00"         # orange
            pass_colour = "#00c853"
            fail_colour = "#ff1744"
        else:
            bg_colour = "#f8fafc"          # slate-50
            grid_colour = "#e2e8f0"        # slate-200
            grid_sub_colour = "#cbd5e1"    # slate-300
            text_colour = "#64748b"        # slate-500
            ch1_colour = "#16a34a"         # green-600
            ch2_colour = "#0284c7"         # sky-600
            ch3_colour = "#ea580c"         # orange-600
            pass_colour = "#16a34a"
            fail_colour = "#dc2626"

        # Apply canvas background colour
        self.canvas.configure(bg=bg_colour)

        # Gather inputs and outputs from active profile schema
        profile_inputs = getattr(self.profile, 'inputs', [])
        profile_outputs = getattr(self.profile, 'outputs', [])
        
        channels = []
        for name, bit_width in profile_inputs:
            channels.append((name, bit_width, True))
        for name, bit_width in profile_outputs:
            channels.append((name, bit_width, False))

        total_channels = len(channels)
        if total_channels == 0:
            total_channels = 1

        # Split height into signal channels + bottom marker row
        channel_height = (height - 24) / total_channels

        # Draw vertical grid lines (oscilloscope pattern)
        for i in range(1, 10):
            grid_x = (width / 10) * i
            self.canvas.create_line(grid_x, 0, grid_x, height - 24, fill=grid_colour, dash=(2, 2))
        
        # Draw horizontal channel division grid lines
        for i in range(1, total_channels):
            grid_y = channel_height * i
            self.canvas.create_line(0, grid_y, width, grid_y, fill=grid_sub_colour)

        # Label channels dynamically
        def get_channel_color(idx, is_input):
            if is_input:
                return ch1_colour if idx % 2 == 0 else ch2_colour
            return ch3_colour

        for idx, (name, bit_width, is_input) in enumerate(channels):
            y_offset = (channel_height * idx) + 15
            color = get_channel_color(idx, is_input)
            label = f"IN: {name}" if is_input else f"OUT: {name}"
            self.canvas.create_text(
                15, y_offset, text=label, fill=color, anchor="w",
                font=("Consolas", 10, "bold")
            )

        if not self.history:
            # Draw idle line message
            self.canvas.create_text(
                width / 2, height / 2, text="[No Signal: Stream HIL Tests to Start]",
                fill=text_colour, font=("Consolas", 11)
            )
            return

        # Plot spacing
        x_step = width / (self.max_points - 1)

        # Map channel trace coordinates
        trace_points = {i: [] for i in range(total_channels)}

        for idx, data in enumerate(self.history):
            x = x_step * idx
            is_pass = data.get("is_pass", True)

            for ch_idx, (name, bit_width, is_input) in enumerate(channels):
                val_dict = data.get("inputs" if is_input else "outputs", {})
                val = val_dict.get(name, 0)
                
                max_val = (1 << bit_width) - 1
                if max_val <= 0:
                    max_val = 1

                # Map Y coordinate for this specific trace channel segment
                y = (channel_height * (ch_idx + 1)) - 15 - ((val / max_val) * (channel_height - 30))
                trace_points[ch_idx].append((x, y))

            # Draw PASS/FAIL indicators at the bottom marker row
            marker_y = height - 12
            if is_pass:
                self.canvas.create_oval(
                    x - 3, marker_y - 3, x + 3, marker_y + 3,
                    fill=pass_colour, outline=""
                )
            else:
                self.canvas.create_line(
                    x - 3, marker_y - 3, x + 3, marker_y + 3,
                    fill=fail_colour, width=2
                )
                self.canvas.create_line(
                    x - 3, marker_y + 3, x + 3, marker_y - 3,
                    fill=fail_colour, width=2
                )

        # Render Trace lines
        for ch_idx in range(total_channels):
            is_input = channels[ch_idx][2]
            color = get_channel_color(ch_idx, is_input)
            self._draw_trace(trace_points[ch_idx], colour=color)

    def _draw_trace(self, pts, colour):
        if len(pts) < 2:
            return
        # Flat list conversion for Tkinter create_line
        flat_coords = []
        for x, y in pts:
            flat_coords.extend([x, y])
        self.canvas.create_line(flat_coords, fill=colour, width=2, joinstyle="round")


class LiveThroughputGraph(ctk.CTkFrame):
    """Real-time throughput (tests per second) waveform graph."""

    def __init__(self, master, profile, **kwargs):
        super().__init__(master, **kwargs)
        self.profile = profile
        self.history = []  # List of throughput rates (tests/sec)
        self.max_points = 50

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=12, pady=(10, 4))
        
        ctk.CTkLabel(
            header_frame, text="LIVE VERIFICATION SPEED",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        # --- Canvas widget ---
        self.canvas = tk.Canvas(
            self, highlightthickness=0, bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Re-draw on resize
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def update_profile(self, profile):
        """Reset when active profile changes."""
        self.profile = profile
        self.history.clear()
        self.redraw()

    def append_point(self, throughput: float):
        """Append a new throughput rate point to the graph buffer."""
        self.history.append(throughput)
        if len(self.history) > self.max_points:
            self.history.pop(0)
        self.redraw()

    def clear(self):
        """Reset the plot buffer."""
        self.history.clear()
        self.redraw()

    def redraw(self):
        """Draw the grid, axes labels, filled area throughput chart, and digital readout."""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Guard against zero sizing during Tkinter init
        if width < 50 or height < 50:
            return

        # Fetch theme-dependent colours dynamically
        theme = ctk.get_appearance_mode().lower()
        if theme == "dark":
            bg_colour = "#0f172a"        # slate-900
            grid_colour = "#1e293b"      # slate-800
            line_colour = "#38bdf8"      # sky-400
            fill_colour = "#0c4a6e"      # sky-900 (darker)
            text_colour = "#94a3b8"      # slate-400
            accent_colour = "#38bdf8"    # sky-400
        else:
            bg_colour = "#f8fafc"        # slate-50
            grid_colour = "#e2e8f0"      # slate-200
            line_colour = "#0284c7"      # sky-600
            fill_colour = "#bae6fd"      # sky-200
            text_colour = "#64748b"      # slate-500
            accent_colour = "#0369a1"    # sky-700

        # Apply canvas background colour
        self.canvas.configure(bg=bg_colour)

        # Draw vertical grid divisions
        for i in range(1, 10):
            grid_x = (width / 10) * i
            self.canvas.create_line(grid_x, 0, grid_x, height - 20, fill=grid_colour, dash=(2, 2))

        # Check throughput history range for auto-scaling
        valid_points = [x for x in self.history if x > 0]
        max_rate = max(valid_points) if valid_points else 100.0
        # Ensure a minimum scale to make grid look nice
        if max_rate < 10.0:
            max_rate = 10.0
        
        # Round upper scale bound for readable labels
        upper_bound = round(max_rate * 1.1)

        # Draw horizontal grid divisions (4 sections)
        channel_height = (height - 30) / 4
        for i in range(1, 4):
            grid_y = channel_height * i
            self.canvas.create_line(0, grid_y, width, grid_y, fill=grid_colour)
            
            # Label grid levels
            level_val = int(upper_bound - (i * (upper_bound / 4)))
            self.canvas.create_text(
                8, grid_y - 8, text=f"{level_val:,}", fill=text_colour, anchor="w",
                font=("Consolas", 9)
            )

        # Label bottom axis (0 tests/sec)
        self.canvas.create_text(
            8, height - 20, text="0", fill=text_colour, anchor="w",
            font=("Consolas", 9)
        )

        if not self.history:
            self.canvas.create_text(
                width / 2, height / 2, text="[No Run Data: Stream HIL Tests to Plot Throughput]",
                fill=text_colour, font=("Consolas", 11)
            )
            return

        # Map throughput coordinates
        x_step = width / (self.max_points - 1)
        plot_pts = []
        
        y_min = 10
        y_max = height - 30

        for idx, rate in enumerate(self.history):
            x = x_step * idx
            # Prevent divide by zero / out of bounds
            fraction = rate / upper_bound if upper_bound > 0 else 0
            if fraction > 1.0:
                fraction = 1.0
            
            y = y_max - (fraction * (y_max - y_min))
            plot_pts.append((x, y))

        # Draw Filled Area Polygon under the line
        poly_coords = [0, y_max]  # Start at bottom-left corner
        for x, y in plot_pts:
            poly_coords.extend([x, y])
        poly_coords.extend([plot_pts[-1][0], y_max])  # End at bottom-right corner
        
        self.canvas.create_polygon(
            poly_coords, fill=fill_colour, outline=""
        )

        # Draw Chart Line
        flat_coords = []
        for x, y in plot_pts:
            flat_coords.extend([x, y])
        self.canvas.create_line(
            flat_coords, fill=line_colour, width=2.5, joinstyle="round"
        )

        # Draw digital rate text display (top right)
        current_rate = self.history[-1]
        self.canvas.create_text(
            width - 16, 24, text=f"{current_rate:,.1f} tests/sec",
            fill=accent_colour, anchor="e",
            font=("Consolas", 14, "bold")
        )
