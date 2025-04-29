"""
Helper script to decode stego images using saved debug information
"""
import os
import sys
import binascii
import numpy as np

def read_debug_info(debug_path):
    """Read and display debug information from .npz file"""
    print(f"Reading debug info from {debug_path}")
    try:
        data = np.load(debug_path, allow_pickle=True)
        print("\nAvailable keys in debug file:")
        for key in data.files:
            print(f"  - {key}")
            
        # Print binary message if available
        if 'binary_message' in data:
            binary = data['binary_message']
            print(f"\nBinary message ({len(binary)} bits):")
            print(f"  {binary[:100]}..." if len(binary) > 100 else binary)
            
            # Convert to hex for inspection
            try:
                bin_chunks = [binary[i:i+8] for i in range(0, len(binary), 8)]
                byte_array = bytearray(int(chunk, 2) for chunk in bin_chunks if len(chunk) == 8)
                hex_str = binascii.hexlify(byte_array).decode('ascii')
                print(f"\nHex representation:")
                print(f"  {hex_str[:100]}..." if len(hex_str) > 100 else hex_str)
            except Exception as e:
                print(f"Error converting to hex: {e}")
        
        # Print embedded bits if available
        if 'embedded_bits' in data:
            bits = data['embedded_bits']
            print(f"\nEmbedded bits ({len(bits)} bits):")
            bits_str = ''.join(map(str, bits[:100]))
            print(f"  {bits_str}..." if len(bits) > 100 else bits_str)
        
        # Print strength parameter
        if 'strength' in data:
            print(f"\nStrength parameter: {data['strength']}")
        
        # Print original message if available
        if 'message_original' in data:
            print(f"\nOriginal message: {data['message_original']}")
            
        return data
        
    except Exception as e:
        print(f"Error reading debug file: {e}")
        return None

def convert_binary_to_text(binary_str):
    """Convert binary string to text with robust error handling"""
    print(f"\nConverting {len(binary_str)} binary bits to text")
    
    # Ensure binary_str contains only 0s and 1s
    binary_str = ''.join(c for c in binary_str if c in '01')
    
    # Pad to multiple of 8 if needed
    if len(binary_str) % 8 != 0:
        padding = 8 - (len(binary_str) % 8)
        binary_str += '0' * padding
        print(f"Added {padding} padding bits")
    
    # Convert to bytes and then to text
    try:
        # Process in chunks of 8 bits
        chunks = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
        byte_array = bytearray(int(chunk, 2) for chunk in chunks)
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        results = {}
        
        for enc in encodings:
            try:
                text = byte_array.decode(enc, errors='replace')
                results[enc] = text
            except Exception as e:
                results[enc] = f"Error: {str(e)}"
        
        # Print results
        print("\nDecoding results:")
        for enc, text in results.items():
            print(f"\n{enc}:")
            print(f"  {text[:100]}..." if len(text) > 100 else text)
            
        return results
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        return None

def direct_conversion(binary_str):
    """Manual byte-by-byte conversion"""
    result = ""
    try:
        # Process byte-by-byte directly
        for i in range(0, len(binary_str), 8):
            if i + 8 <= len(binary_str):
                byte = binary_str[i:i+8]
                char_code = int(byte, 2)
                # Only handle ASCII range to avoid issues
                if 32 <= char_code < 127:  # Printable ASCII
                    result += chr(char_code)
                else:
                    result += f"[{char_code}]"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python decode_helper.py <path_to_debug_file>")
        sys.exit(1)
        
    debug_path = sys.argv[1]
    if not os.path.exists(debug_path):
        print(f"File not found: {debug_path}")
        sys.exit(1)
        
    # Read debug info
    data = read_debug_info(debug_path)
    
    # If binary message is available, try to convert it
    if data is not None and 'binary_message' in data:
        binary = data['binary_message']
        
        # Remove terminator if present
        if len(binary) >= 8 and binary[-8:] == '00000000':
            binary = binary[:-8]
            print("Removed terminator sequence")
            
        convert_binary_to_text(binary)
        
        print("\nDirect byte conversion (ASCII only):")
        print(direct_conversion(binary))
    
    # If embedded bits are available, try those too
    elif data is not None and 'embedded_bits' in data:
        bits = data['embedded_bits']
        binary = ''.join(map(str, bits))
        
        # Look for terminator
        terminator_pos = -1
        for i in range(len(binary) - 7):
            if binary[i:i+8] == '00000000':
                terminator_pos = i
                break
                
        if terminator_pos != -1:
            print(f"Found terminator at position {terminator_pos}")
            binary = binary[:terminator_pos]
            
        convert_binary_to_text(binary)
        
        print("\nDirect byte conversion (ASCII only):")
        print(direct_conversion(binary))
