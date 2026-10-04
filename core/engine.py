"""
================================================================================
File:         engine.py
Written by:   Harry Rogers
Date:         May 2026
Description:  High-throughput verification test engine and hardware-in-the-loop coordinator
================================================================================
"""

import os
import time
import csv
import json
import shutil
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from core.interfaces import CommDriver, DeviceProfile


class TestEngine:
    def __init__(self, driver: CommDriver, profile: DeviceProfile, log_callback=None):
        self.driver = driver
        self.profile = profile
        self.log_callback = log_callback
        self.observer = None
        self.connected = False
        
        self.port = getattr(driver, 'port', 'N/A')
        self.baud = getattr(driver, 'baud_rate', 0)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.base_dir)
        self.queue_dir = os.path.join(self.base_dir, 'test_queue')
        self.results_dir = os.path.join(self.queue_dir, 'results')
        self.processed_dir = os.path.join(self.queue_dir, 'ran')
        self.failed_dir = os.path.join(self.queue_dir, 'failed')
        
        self._setup_directories()

    @property
    def op_symbols(self):
        return self.profile.op_symbols

    def _setup_directories(self):
        for d in [self.queue_dir, self.results_dir, self.processed_dir, self.failed_dir]:
            os.makedirs(d, exist_ok=True)

    def log(self, msg, level="INFO"):
        if self.log_callback:
            self.log_callback(msg, level)
        else:
            print(msg)

    def connect(self):
        try:
            if self.driver.connect():
                self.connected = True
                self.log(f"Successfully connected to hardware on {self.port}.", "INFO")
                return True
        except Exception as e:
            self.log(f"CRITICAL ERROR: Failed to establish hardware connection: {e}", "ERROR")
        self.log(f"ERROR: Connection failed on port {self.port}. Please verify that the device is powered on, connected, and that no other application is using this port.", "ERROR")
        return False

    def disconnect(self):
        self.driver.disconnect()
        self.connected = False

    def process_csv(self, csv_path, visual_delay=0):
        if not self.connected:
            self.log("Not connected to FPGA.", level="ERROR")
            return False

        filename = os.path.basename(csv_path)
        log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"results_{log_timestamp}_{filename}.log"
        log_path = os.path.join(self.results_dir, log_filename)

        try:
            with open(csv_path, 'r') as f:
                progress_total = sum(1 for _ in f) - 1
        except Exception as e:
            self.log(f"Error reading {filename}: {e}", level="ERROR")
            return False

        if progress_total <= 0:
            self.log(f"ERROR: {filename} contains no test vectors. Aborting verification.", level="ERROR")
            return False

        header_top = (
            f"============================================================\n"
            f"  HIL VERIFICATION REPORT\n"
            f"============================================================\n"
            f"SYSTEM INFO:\n"
            f"  Device:          {self.profile.device_name}\n"
            f"  Interface:        {self.port} @ {self.baud} baud\n"
            f"  Driver:           {type(self.driver).__name__}\n\n"
            f"TEST DETAILS:\n"
            f"  File Name:        {filename}\n"
            f"  Timestamp:        {report_timestamp}\n"
            f"  Visual Delay:     {visual_delay}s per test\n"
        )
        
        report_header = header_top + f"============================================================"

        self.log(report_header, level="INFO")
        self.log(f"[PROGRESS_START] Total tests: {progress_total}", level="INFO")
        
        passed = 0
        total = 0
        start_time = time.time()
        last_progress_update = start_time

        self.driver.clear_buffer()

        try:
            with open(log_path, 'w') as f_out:
                f_out.write(report_header + "\n\n")

            with open(csv_path, 'r') as f_in, open(log_path, 'a') as f_out:
                reader = csv.DictReader(f_in)
                
                # Gather inputs and outputs from profile schema
                profile_inputs = getattr(self.profile, 'inputs', [])
                profile_outputs = getattr(self.profile, 'outputs', [])
                
                # Check for operation column
                op_col = None
                if getattr(self.profile, 'OPCODES', None):
                    for col in ['Operation', 'command', 'op']:
                        if col in reader.fieldnames:
                            op_col = col
                            break
                    if not op_col:
                        op_col = 'Operation'
                
                required_cols = []
                if op_col:
                    required_cols.append(op_col)
                
                input_mappings = {}  # maps profile input name -> CSV fieldname
                for inp_name, bit_width in profile_inputs:
                    found_col = None
                    for f in reader.fieldnames:
                        if f.lower() == inp_name.lower():
                            found_col = f
                            break
                    if found_col:
                        input_mappings[inp_name] = found_col
                    else:
                        required_cols.append(inp_name)
                        
                output_mappings = {} # maps profile output name -> CSV fieldname
                for out_name, bit_width in profile_outputs:
                    found_col = None
                    # 1. Try "Expected [name]"
                    for f in reader.fieldnames:
                        if f.lower() == f"expected {out_name.lower()}":
                            found_col = f
                            break
                    # 2. Try "[name]" directly
                    if not found_col:
                        for f in reader.fieldnames:
                            if f.lower() == out_name.lower():
                                found_col = f
                                break
                    # 3. Try "Flag [name]" (compatibility with Flag N, Flag Z, etc.)
                    if not found_col:
                        for f in reader.fieldnames:
                            if f.lower() == f"flag {out_name.lower()}":
                                found_col = f
                                break
                    if found_col:
                        output_mappings[out_name] = found_col
                    else:
                        required_cols.append(f"Expected {out_name}")

                missing_columns = [col for col in required_cols if col not in reader.fieldnames]
                if missing_columns:
                    msg = f"CRITICAL ERROR: CSV file '{filename}' is missing required columns: {', '.join(missing_columns)}"
                    self.log(msg, level="ERROR")
                    f_out.write(msg + "\n")
                    return False

                for row in reader:
                    total += 1

                    # Parse operation name if applicable
                    op_name = ""
                    if op_col:
                        op_name = str(row.get(op_col, '')).upper().strip()

                    # Parse inputs dynamically
                    inputs_parsed = {}
                    parse_error = False
                    for inp_name, bit_width in profile_inputs:
                        csv_col = input_mappings.get(inp_name)
                        try:
                            val = int(row.get(csv_col, 0))
                            inputs_parsed[inp_name] = val
                        except (ValueError, TypeError):
                            msg = f"ERROR: Row {total} - Invalid numeric format for input '{inp_name}' (value='{row.get(csv_col)}'). Skipping test."
                            self.log(msg, level="ERROR")
                            f_out.write(msg + "\n")
                            parse_error = True
                            break
                    
                    if parse_error:
                        continue

                    # Validate input ranges based on bit width
                    for inp_name, bit_width in profile_inputs:
                        val = inputs_parsed[inp_name]
                        max_val = (1 << bit_width) - 1
                        if val < 0 or val > max_val:
                            self.log(
                                f"WARNING: Row {total} - Input '{inp_name}' ({val}) is out of bounds for {self.profile.device_name} (range: 0-{max_val}). Value will be truncated by hardware.",
                                level="WARN"
                            )

                    # Validate register bounds or division by zero (generically checked)
                    if op_name in ["STO", "RCL"]:
                        for inp_name, val in inputs_parsed.items():
                            if "b" in inp_name.lower() or "operand_b" in inp_name.lower() or "address" in inp_name.lower():
                                if val < 0 or val > 3:
                                    self.log(f"WARNING: Row {total} - Register address '{inp_name}' ({val}) is out of range for STO/RCL (expected 0-3). Undefined hardware behaviour may result.", level="WARN")

                    if op_name in ["DIV", "MOD"]:
                        for inp_name, val in inputs_parsed.items():
                            if "b" in inp_name.lower() or "operand_b" in inp_name.lower():
                                if val == 0:
                                    self.log(f"WARNING: Row {total} - Division by zero detected ('{inp_name}' is 0). Division hardware may hang or return undefined results.", level="WARN")

                    # Pack command bytes
                    tx_bytes = self.profile.pack_command(row)
                    
                    if op_col and tx_bytes and tx_bytes[0] == 0xFF:
                        self.log(f"Row {total} ERROR: Unknown operation '{row.get(op_col)}' unsupported by active device profile.", level="ERROR")
                        continue

                    # Communicate with physical hardware
                    try:
                        self.driver.send_packet(tx_bytes)
                        rx_bytes = self.driver.receive_packet(self.profile.response_size)
                    except Exception as e:
                        msg = f"[CONNECTION_LOST] Hardware communication link broken: {e}"
                        self.log(msg, level="ERROR")
                        f_out.write(msg + "\n")
                        self.disconnect()
                        return False

                    if len(rx_bytes) != self.profile.response_size:
                        msg = f"[CONNECTION_LOST] Receive timeout from physical board. Expected {self.profile.response_size} bytes, got {len(rx_bytes)}."
                        self.log(msg, level="ERROR")
                        f_out.write(msg + "\n")
                        self.disconnect()
                        return False

                    # Unpack response
                    hw = self.profile.unpack_response(rx_bytes)
                    if hw is None:
                        msg = f"ERROR: Row {total} - Failed to unpack response."
                        self.log(msg, level="ERROR")
                        f_out.write(msg + "\n")
                        continue

                    # Validate expected vs actual outputs
                    all_outputs_match = True
                    comparison_details = []
                    for out_name, bit_width in profile_outputs:
                        csv_col = output_mappings.get(out_name)
                        try:
                            exp_val = int(row.get(csv_col, 0))
                        except (ValueError, TypeError):
                            exp_val = 0
                        act_val = hw.get(out_name, 0)
                        
                        match = (act_val == exp_val)
                        if not match:
                            all_outputs_match = False
                        
                        comparison_details.append((out_name, exp_val, act_val, match))

                    status = "PASS" if all_outputs_match else "FAIL"
                    if status == "PASS":
                        passed += 1

                    # Log verification row
                    inputs_log_str = " ".join([f"{name}: {val}" for name, val in inputs_parsed.items()])
                    outputs_log_str_got = ", ".join([f"{name}={hw.get(name)}" for name, _ in profile_outputs])
                    outputs_log_str_exp = ", ".join([f"{name}={row.get(output_mappings.get(name))}" for name, _ in profile_outputs])
                    
                    symbol = self.op_symbols.get(op_name, op_name) if op_col else ""
                    if op_col and len(inputs_parsed) >= 2:
                        inp_vals = list(inputs_parsed.values())
                        test_header = f"TEST {total}: {inp_vals[0]} {symbol} {inp_vals[1]}"
                    else:
                        test_header = f"TEST {total}: {op_name if op_name else 'EXEC'} [{inputs_log_str}]"

                    log_str = (
                        f"{test_header}\n"
                        f"| {inputs_log_str}\n"
                        f"   Got: {outputs_log_str_got}\n"
                        f"   Exp: {outputs_log_str_exp}\n"
                        f"   --> {status}\n\n"
                    )
                    
                    f_out.write(log_str)
                    f_out.flush()
                    
                    if status == "FAIL" or visual_delay > 0:
                        self.log(log_str.rstrip(), level="ERROR" if status == "FAIL" else "INFO")

                    # Stream signal trace data to logic analyser safely via tagged message
                    analyser_data = {
                        "inputs": inputs_parsed,
                        "outputs": hw,
                        "is_pass": status == "PASS"
                    }
                    self.log(f"[LOGIC_ANALYSER_DATA] {json.dumps(analyser_data)}", level="INFO")
                    
                    if visual_delay > 0:
                        time.sleep(visual_delay)
                    
                    if (time.time() - last_progress_update) >= 0.5 or total == progress_total:
                        elapsed = time.time() - start_time
                        percentage = (total / progress_total) * 100
                        if total > 0:
                            rate = total / elapsed
                            remaining_tests = progress_total - total
                            eta_seconds = remaining_tests / rate if rate > 0 else 0
                            self.log(f"[PROGRESS] {percentage:.1f}% | {total}/{progress_total} | Elapsed: {int(elapsed)}s | ETA: {int(eta_seconds)}s | Rate: {rate:.1f} tests/sec", level="INFO")
                        last_progress_update = time.time()

            duration = time.time() - start_time
            tps = total / duration if duration > 0 else 0
            success = (passed == total)
            result_label = "PASS" if success else "FAIL"
            
            summary_core = (
                f"SUMMARY: {filename}\n"
                f"Result:      {result_label}\n"
                f"Score:       {passed}/{total}\n"
                f"Time Taken:  {duration:.2f}s\n"
                f"Throughput:  {tps:.1f} tests/sec\n"
            )
            
            bottom_summary = (
                f"\n============================================================\n"
                f"{summary_core}"
                f"============================================================"
            )

            self.log(bottom_summary.strip() + "\n", level="INFO")
            
            with open(log_path, 'a') as f_append:
                f_append.write(bottom_summary + "\n")

            combined_header = header_top + "\n" + summary_core + f"============================================================"
            
            with open(log_path, 'r') as f_in:
                content = f_in.read()

            final_log_content = content.replace(report_header, combined_header, 1)

            with open(log_path, 'w') as f_out:
                f_out.write(final_log_content)

            dest = self.processed_dir if success else self.failed_dir
            try: 
                shutil.move(csv_path, os.path.join(dest, filename))
            except Exception: 
                pass 

        except Exception as e:
            self.log(f"Error during test execution: {e}", level="ERROR")
            return False

        return success

    def start_watchdog(self, delay=0):
        event_handler = EngineHandler(self, delay)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.queue_dir, recursive=False)
        self.observer.start()
        self.log(f"Watchdog active on: {self.queue_dir}", level="INFO")

    def stop_watchdog(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()


class EngineHandler(FileSystemEventHandler):
    def __init__(self, engine, delay):
        self.engine = engine
        self.delay = delay

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.csv'):
            time.sleep(0.5) 
            self.engine.process_csv(event.src_path, self.delay)
