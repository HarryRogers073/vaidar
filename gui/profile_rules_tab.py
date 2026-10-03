"""
********************************************************************************
* MODULE:       profile_rules_tab.py
* AUTHOR:       Harry Rogers
* DATE:         2026
*
* DESCRIPTION:
* Display panel that parses and renders the metadata, supported commands,
* binary opcode maps, and AI prompts of the active DeviceProfile.
* Refreshes dynamically when the profile changes at runtime. Allows the user
* to edit and save custom AI generation and analysis prompts.
********************************************************************************
"""
import tkinter as tk
import customtkinter as ctk


class ProfileRulesTab(ctk.CTkFrame):
    """Explorer widget for displaying and editing active device profile configurations."""

    def __init__(self, master, profile, config, **kwargs):
        super().__init__(master, **kwargs)
        self.profile = profile
        self.config = config
        self.setup_ui()

    def update_profile(self, profile):
        """Dynamic refresh when active profile is changed in settings."""
        self.profile = profile
        # Clear frame and recreate UI
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()

    def setup_ui(self):
        """Construct the split profile rules viewer."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ======================================================================
        # LEFT PANE: Identity, Metadata & Symbols
        # ======================================================================
        left_pane = ctk.CTkFrame(self, fg_color="transparent")
        left_pane.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

        # Header Title
        ctk.CTkLabel(
            left_pane, text=self.profile.device_name,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        # Metadata row
        meta_text = f"Version: {getattr(self.profile, 'version', '1.0.0')} | Author: {getattr(self.profile, 'author', 'Harry Rogers')}"
        ctk.CTkLabel(
            left_pane, text=meta_text,
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=("gray50", "gray40")
        ).pack(anchor="w", pady=(0, 12))

        # Description
        desc_box = ctk.CTkTextbox(
            left_pane, height=90, font=ctk.CTkFont(size=12),
            border_width=1, corner_radius=6
        )
        desc_box.pack(fill="x", pady=(0, 16))
        desc_box.insert("1.0", self.profile.description)
        desc_box.configure(state="disabled")

        # Signal Schema Header
        ctk.CTkLabel(
            left_pane, text="Signal IO Schema Configuration",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        schema_frame = ctk.CTkFrame(left_pane, border_width=1, corner_radius=6)
        schema_frame.pack(fill="x", pady=(0, 16))
        
        # Display inputs and outputs
        profile_inputs = getattr(self.profile, 'inputs', [])
        profile_outputs = getattr(self.profile, 'outputs', [])
        
        inps_str = ", ".join([f"{name} ({width}-bit)" for name, width in profile_inputs])
        outs_str = ", ".join([f"{name} ({width}-bit)" for name, width in profile_outputs])
        
        ctk.CTkLabel(schema_frame, text=f"Inputs:  {inps_str if inps_str else 'None'}", font=ctk.CTkFont(size=11), text_color=("#16a34a", "#00e676")).pack(anchor="w", padx=12, pady=(6, 2))
        ctk.CTkLabel(schema_frame, text=f"Outputs: {outs_str if outs_str else 'None'}", font=ctk.CTkFont(size=11), text_color=("#ea580c", "#ff6d00")).pack(anchor="w", padx=12, pady=(2, 6))

        # Symbol Mapping Table header
        ctk.CTkLabel(
            left_pane, text="Supported Operations & Output Symbols",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        # Scrollable symbols grid
        sym_scroll = ctk.CTkScrollableFrame(left_pane, height=200)
        sym_scroll.pack(fill="both", expand=True)
        sym_scroll.grid_columnconfigure((0, 1), weight=1)

        # Grid headers
        ctk.CTkLabel(sym_scroll, text="Operation Name", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=4)
        ctk.CTkLabel(sym_scroll, text="Console Math Symbol", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, sticky="w", padx=10, pady=4)

        symbols = getattr(self.profile, 'op_symbols', {})
        for idx, (op_name, symbol) in enumerate(symbols.items(), start=1):
            ctk.CTkLabel(sym_scroll, text=op_name, font=ctk.CTkFont(size=11)).grid(row=idx, column=0, sticky="w", padx=10, pady=2)
            ctk.CTkLabel(sym_scroll, text=symbol, font=ctk.CTkFont(size=11, weight="bold"), text_color="#0084c7").grid(row=idx, column=1, sticky="w", padx=10, pady=2)

        # ======================================================================
        # RIGHT PANE: Binary Opcodes & AI Rules
        # ======================================================================
        right_pane = ctk.CTkFrame(self, fg_color="transparent")
        right_pane.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)

        # Opcode lookup
        ctk.CTkLabel(
            right_pane, text="Binary Instruction Opcode Mapping",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        opcode_scroll = ctk.CTkScrollableFrame(right_pane, height=130)
        opcode_scroll.pack(fill="x", pady=(0, 16))
        opcode_scroll.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(opcode_scroll, text="CSV Command", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=4)
        ctk.CTkLabel(opcode_scroll, text="FPGA Hex Opcode", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, sticky="w", padx=10, pady=4)

        opcodes = getattr(self.profile, 'OPCODES', {})
        for idx, (op_name, code) in enumerate(opcodes.items(), start=1):
            hex_code = f"0x{code:02X}"
            ctk.CTkLabel(opcode_scroll, text=op_name.upper(), font=ctk.CTkFont(size=11)).grid(row=idx, column=0, sticky="w", padx=10, pady=2)
            ctk.CTkLabel(opcode_scroll, text=hex_code, font=ctk.CTkFont(size=11, family="Consolas", weight="bold"), text_color="#7c3aed").grid(row=idx, column=1, sticky="w", padx=10, pady=2)

        # AI Behaviour Prompt display
        ctk.CTkLabel(
            right_pane, text="Profile AI System Instructions",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        prompt_tabs = ctk.CTkTabview(right_pane, height=210)
        prompt_tabs.pack(fill="both", expand=True)

        tab_gen = prompt_tabs.add("Generation Rules")
        tab_analysis = prompt_tabs.add("Analysis Rules")

        # Generation textbox (editable)
        self.tb_gen = ctk.CTkTextbox(tab_gen, font=ctk.CTkFont(family="Consolas", size=10))
        self.tb_gen.pack(fill="both", expand=True, padx=4, pady=4)
        self.tb_gen.insert("1.0", self.profile.ai_generation_prompt)

        # Analysis textbox (editable)
        self.tb_anal = ctk.CTkTextbox(tab_analysis, font=ctk.CTkFont(family="Consolas", size=10))
        self.tb_anal.pack(fill="both", expand=True, padx=4, pady=4)
        self.tb_anal.insert("1.0", self.profile.ai_analysis_prompt)

        # Save Prompts Button
        self.btn_save = ctk.CTkButton(
            right_pane, text="Save AI Prompts", height=32,
            command=self.save_prompts,
            fg_color="#00c853", hover_color="#00e676",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.btn_save.pack(fill="x", pady=(10, 0))

    def save_prompts(self):
        """Save edited generation and analysis prompts to config and apply them."""
        gen_text = self.tb_gen.get("1.0", "end-1c").strip()
        anal_text = self.tb_anal.get("1.0", "end-1c").strip()

        if not gen_text or not anal_text:
            from tkinter import messagebox
            messagebox.showwarning("Validation Error", "AI Generation and Analysis prompts cannot be empty.")
            return

        try:
            # Update profile instance directly
            self.profile.ai_generation_prompt = gen_text
            self.profile.ai_analysis_prompt = anal_text

            # Update config manager
            gen_key = f"prompt_gen_{self.profile.device_name.lower().replace(' ', '_')}"
            anal_key = f"prompt_anal_{self.profile.device_name.lower().replace(' ', '_')}"
            self.config.set(gen_key, gen_text)
            self.config.set(anal_key, anal_text)
            self.config.save()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Save Error", f"Failed to save prompts to config.json:\n\n{e}")
            return

        # Visual feedback: update button text temporarily
        original_colour = self.btn_save.cget("fg_color")
        self.btn_save.configure(text="Prompts Saved!", fg_color="#0284c7")
        self.after(2000, lambda: self.btn_save.configure(text="Save AI Prompts", fg_color=original_colour))
