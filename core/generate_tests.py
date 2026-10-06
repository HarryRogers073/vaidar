"""
================================================================================
File:         generate_tests.py
Written by:   Harry Rogers
Date:         May 2026
Description:  Algorithmic test vector generation and arithmetic flag golden model
================================================================================
"""

import csv
import random
import math

# Simulated register file to track state between tests
simulated_registers = [0, 0, 0, 0]

def reset_registers():
    """Reset the simulated register file to initial zero state."""
    global simulated_registers
    simulated_registers = [0, 0, 0, 0]

def calculate_flags(op, a, b):
    global simulated_registers
    mask = 0xFFFF
    n, z, c, v = 0, 0, 0, 0
    res = 0

    op = op.upper()
    
    if op == 'ADD':
        res_full = a + b
        res = res_full & mask
        c = 1 if res_full > mask else 0
        if ((a ^ b) & 0x8000) == 0 and ((a ^ res) & 0x8000) != 0: v = 1
            
    elif op == 'SUB':
        res_full = a - b
        res = res_full & mask
        c = 1 if a < b else 0
        if ((a ^ b) & 0x8000) != 0 and ((a ^ res) & 0x8000) != 0: v = 1
            
    elif op == 'MUL':
        res_full = a * b
        res = res_full & mask
        if res_full > mask: 
            c = 1
            
    elif op == 'DIV':
        if b == 0:
            res = 0xEEEE 
            v = 1        
        else:
            res = int(a // b) & mask
            
    elif op == 'MOD':
        if b == 0:
            res = 0xEEEE
            v = 1
        else:
            res = (a % b) & mask
            
    elif op == 'SQRT':
        res = int(math.isqrt(a)) & mask
        
    elif op == 'POW':
        try:
            res_full = a ** b
            res = res_full & mask
            if res_full > mask: c = 1
        except OverflowError:
            res = 0xFFFF
            c = 1
            
    elif op == 'AND': res = (a & b) & mask
    elif op == 'OR':  res = (a | b) & mask
    elif op == 'XOR': res = (a ^ b) & mask
    elif op == 'NOT': res = (~a) & mask
    
    elif op == 'SHL': res = (a << (b & 0x0F)) & mask
    elif op == 'SHR': res = (a >> (b & 0x0F)) & mask
        
    elif op == 'INC':
        res_full = a + 1
        res = res_full & mask
        c = 1 if res_full > mask else 0
        
    elif op == 'DEC':
        res_full = a - 1
        res = res_full & mask
        c = 1 if a == 0 else 0
        if a == 0x8000: v = 1
        
    elif op == 'NEG':
        res_full = 0 - a
        res = res_full & mask
        c = 1 if a == 0 else 0
        if a == 0x8000: v = 1

    elif op == 'STO':
        reg_idx = b & 0x03
        simulated_registers[reg_idx] = a
        res = 0
        
    elif op == 'RCL':
        reg_idx = b & 0x03
        res = simulated_registers[reg_idx]
    
    z = 1 if res == 0 else 0
    n = 1 if (res & 0x8000) else 0
    
    return res, n, z, c, v

def generate_test_file(filename, num_tests):
    global simulated_registers
    simulated_registers = [0, 0, 0, 0]
    
    commands = ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'SQRT', 'POW', 'AND', 'OR', 'XOR', 'NOT', 'SHL', 'SHR', 'INC', 'DEC', 'NEG', 'STO', 'RCL']
    
    print(f"Generating {num_tests} tests in '{filename}'...")
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Operation', 'Operand A', 'Operand B', 'Expected Result', 'Flag N', 'Flag Z', 'Flag C', 'Flag V'])
        
        for _ in range(num_tests):
            op = random.choice(commands)
            a = random.randint(0, 65535)
            
            if op in ['STO', 'RCL']:
                b = random.randint(0, 3)
            elif op == 'POW':
                b = random.randint(0, 15)
            else:
                b = random.randint(0, 65535)
            
            res, n, z, c, v = calculate_flags(op, a, b)
            writer.writerow([op, a, b, res, n, z, c, v])
            
    print(f"Successfully generated {num_tests} test vectors in '{filename}'.")

if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    out_file = sys.argv[2] if len(sys.argv) > 2 else f"benchmark_{count}_tests.csv"
    generate_test_file(out_file, count)
