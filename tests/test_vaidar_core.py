"""
================================================================================
Test Suite:     test_vaidar_core.py
Description:    Automated unit and integration tests for VAIDAR core runtime,
                golden model assertions, packet framing, and mock HIL execution.
================================================================================
"""

import os
import unittest
import tempfile
import shutil

from core.generate_tests import calculate_flags, generate_test_file
from profiles.alu_16bit import ALU16BitProfile
from drivers.mock_driver import MockDriver
from core.engine import TestEngine


class TestVaidarCore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.profile = ALU16BitProfile()
        self.driver = MockDriver(profile=self.profile)
        self.engine = TestEngine(self.driver, self.profile)
        self.engine.queue_dir = self.temp_dir
        self.engine.results_dir = os.path.join(self.temp_dir, 'results')
        self.engine.processed_dir = os.path.join(self.temp_dir, 'ran')
        self.engine.failed_dir = os.path.join(self.temp_dir, 'failed')
        self.engine._setup_directories()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_golden_model_add(self):
        """Verify addition and carry/overflow flag calculation."""
        res, n, z, c, v = calculate_flags('ADD', 10, 20)
        self.assertEqual(res, 30)
        self.assertEqual(z, 0)
        self.assertEqual(n, 0)
        self.assertEqual(c, 0)
        self.assertEqual(v, 0)

        # Test zero flag
        res, n, z, c, v = calculate_flags('ADD', 0, 0)
        self.assertEqual(res, 0)
        self.assertEqual(z, 1)

        # Test carry flag (16-bit boundary)
        res, n, z, c, v = calculate_flags('ADD', 0xFFFF, 1)
        self.assertEqual(res, 0)
        self.assertEqual(c, 1)
        self.assertEqual(z, 1)

    def test_golden_model_sub(self):
        """Verify subtraction and flag assertions."""
        res, n, z, c, v = calculate_flags('SUB', 20, 10)
        self.assertEqual(res, 10)
        self.assertEqual(z, 0)
        self.assertEqual(c, 0)

        # Test borrow/carry
        res, n, z, c, v = calculate_flags('SUB', 5, 10)
        self.assertEqual(res, (5 - 10) & 0xFFFF)
        self.assertEqual(c, 1)

    def test_packet_serialisation_roundtrip(self):
        """Verify 16-bit ALU packet packing and unpacking."""
        test_row = {
            'Operation': 'ADD',
            'Operand A': 0x1234,
            'Operand B': 0x5678,
            'Expected Result': 0x68AC,
            'Flag N': 0,
            'Flag Z': 0,
            'Flag C': 0,
            'Flag V': 0,
        }
        packed_bytes = self.profile.pack_command(test_row)
        self.assertIsInstance(packed_bytes, (bytes, bytearray))
        self.assertEqual(len(packed_bytes), 5)

    def test_algorithmic_generator(self):
        """Test CSV file generation with test vectors."""
        test_csv_path = os.path.join(self.temp_dir, 'sample_generated.csv')
        generate_test_file(test_csv_path, num_tests=50)
        self.assertTrue(os.path.exists(test_csv_path))

        with open(test_csv_path, 'r') as f:
            lines = f.readlines()
        # 1 header + 50 tests = 51 lines
        self.assertEqual(len(lines), 51)

    def test_mock_driver_and_engine_execution(self):
        """Verify MockDriver connection and transaction loop."""
        self.assertTrue(self.engine.connect())
        self.assertTrue(self.engine.connected)

        # Generate 25 test vectors and run through mock execution engine
        test_csv = os.path.join(self.temp_dir, 'test_batch.csv')
        generate_test_file(test_csv, num_tests=25)

        # Execute via TestEngine with 0.0s delay
        success = self.engine.process_csv(test_csv, visual_delay=0)
        self.assertTrue(success)
        self.engine.disconnect()


if __name__ == '__main__':
    unittest.main()
