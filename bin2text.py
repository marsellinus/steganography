#!/usr/bin/env python3
"""
Command-line binary to text converter
Usage: python bin2text.py [binary_string or filename]
"""
import sys
import os
from binary_decoder import binary_to_text
from unicode_handler import binary_to_text_unicode

def process_binary(binary_input):
    # Clean input - keep only 0s, 1s and spaces
    clean_binary = ''.join(c for c in binary_input if c in '01 \n\t')
    
    # Remove all spaces
    binary_only = ''.join(c for c in clean_binary if c in '01')
    
    if not binary_only:
        print("Error: No valid binary data found")
        return
    
    print("\nDecoding binary...")
    
    # Try both decoders for comparison
    print("\n1. Basic decoder result:")
    try:
        result1 = binary_to_text(binary_only)
        print(result1)
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n2. Unicode handler result:")
    try:
        result2 = binary_to_text_unicode(binary_only)
        print(result2)
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    if len(sys.argv) > 1:
        # Check if argument is a file path
        if os.path.exists(sys.argv[1]):
            try:
                with open(sys.argv[1], 'r') as f:
                    binary_input = f.read()
                process_binary(binary_input)
            except Exception as e:
                print(f"Error reading file: {str(e)}")
        else:
            # Assume the argument is a binary string
            process_binary(sys.argv[1])
    else:
        # No arguments - read from stdin
        print("Enter binary data (Ctrl+D or Ctrl+Z+Enter when done):")
        binary_input = sys.stdin.read()
        process_binary(binary_input)

if __name__ == "__main__":
    main()
