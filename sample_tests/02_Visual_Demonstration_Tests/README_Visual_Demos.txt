================================================================================
HIL VISUAL DEMONSTRATION RUNS (AUDITING GUIDE)
================================================================================
These test files are designed specifically for visual auditing by an external
examiner or reviewer. They use small, extremely simple calculations that are 
easy to verify at a single glance.

RECOMMENDED CONFIGURATION:
- Visual Delay: 10.0 seconds (configured as default in config.json).
  This gives you exactly 10 seconds per calculation to inspect the physical 
  Nexys A7 seven-segment display and NZCV status LEDs, correlating them 
  with the host computer's Realtime Log Console.

HOW TO RUN:
1. Launch the application by double-clicking "Launch Verification Suite.lnk" 
   at the USB root (or via the standalone gui_app.exe).
2. Connect to the board: Select the COM port corresponding to the Nexys A7, 
   set the Baud Rate to 921600, and click "Connect".
3. Check the settings (optional): Click the "⚙ Settings" button. Under the 
   "Visual Delay (seconds)" field, it will already be set to "10.0". If not, 
   set it to "10.0" and click "Save & Apply".
4. Upload and execute: Click the blue "Upload CSV Batch" button under the 
   "Current Status" panel.
5. Navigate to the "02_Visual_Demonstration_Tests" subfolder.
6. Select any of the files in this directory:
   - "visual_demo_01_arithmetic_10s_delay.csv"
   - "visual_demo_02_logicals_10s_delay.csv"
   - "visual_demo_03_shifts_and_flags_10s_delay.csv"
   - "visual_demo_04_register_loop_10s_delay.csv"
7. Watch both your screen and the Nexys A7 board! The seven-segment display will 
   cycle through the inputs and results slowly, while the status LEDs will 
   illuminate for any active NZCV flags (Negative, Zero, Carry, Overflow),
   allowing you to physically audit the hardware logic gates in real-time!
================================================================================
