"""
Helper module for decoding binary strings and troubleshooting Unicode issues
"""
import os
import binascii
import sys

def binary_to_text(binary_string):
    """
    Convert binary string to readable text
    
    Args:
        binary_string: String containing only 0s and 1s
        
    Returns:
        Decoded text
    """
    # Remove any spaces or invalid characters
    binary_string = ''.join(c for c in binary_string if c in '01')
    
    # Make sure the length is a multiple of 8
    if len(binary_string) % 8 != 0:
        remainder = len(binary_string) % 8
        # Pad with zeros if necessary
        binary_string = binary_string + '0' * (8 - remainder)
    
    result = ""
    # Process 8 bits at a time
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        # Convert binary to decimal
        decimal = int(byte, 2)
        # Convert to character
        char = chr(decimal)
        # Add to result if it's a printable ASCII character or common unicode
        if decimal < 128 or (decimal > 191 and decimal < 65536):
            result += char
    
    return result

def text_to_binary(text):
    """
    Convert text to binary string
    
    Args:
        text: String to convert
        
    Returns:
        Binary string (0s and 1s)
    """
    # Convert each character to its binary representation
    binary = ''.join(format(ord(char), '08b') for char in text)
    return binary

def chunks(lst, n):
    """Split a list into chunks of size n"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def format_binary(binary_string):
    """Format binary string for readability"""
    # Group by bytes (8 bits)
    bytes_list = list(chunks(binary_string, 8))
    # Group by words (8 bytes)
    words = list(chunks(bytes_list, 8))
    # Format
    result = []
    for word in words:
        result.append(' '.join(word))
    return '\n'.join(result)

def binary_to_hex(binary_str):
    """
    Convert binary string to hexadecimal representation
    
    Args:
        binary_str: String of 0s and 1s
        
    Returns:
        Hexadecimal representation
    """
    # Clean the input - keep only 0s and 1s
    clean_binary = ''.join(c for c in binary_str if c in '01')
    
    # Ensure length is multiple of 8
    while len(clean_binary) % 8 != 0:
        clean_binary += '0'  # Pad with zeros
    
    # Group into bytes and convert to hex
    hex_result = ""
    for i in range(0, len(clean_binary), 8):
        byte = clean_binary[i:i+8]
        try:
            hex_byte = format(int(byte, 2), '02X')
            hex_result += hex_byte + " "
        except:
            hex_result += "?? "
    
    return hex_result

def analyze_binary(binary_str):
    """
    Analyze binary string and provide diagnostic information
    
    Args:
        binary_str: String of 0s and 1s
        
    Returns:
        Dictionary with analysis results
    """
    # Clean the input - keep only 0s and 1s
    clean_binary = ''.join(c for c in binary_str if c in '01')
    
    # Ensure length is multiple of 8
    padding = 0
    while len(clean_binary) % 8 != 0:
        clean_binary += '0'  # Pad with zeros
        padding += 1
    
    # Basic stats
    total_bytes = len(clean_binary) // 8
    terminator_pos = None
    
    # Look for terminator sequences
    for i in range(0, len(clean_binary) - 7, 8):
        byte = clean_binary[i:i+8]
        if byte == '00000000':  # Null byte terminator
            terminator_pos = i // 8
            break
    
    # Try different encodings
    try:
        # Convert to bytes
        byte_array = bytearray(int(clean_binary[i:i+8], 2) for i in range(0, len(clean_binary), 8))
        
        # Try decoding with different encodings
        encodings = {
            'utf-8': None,
            'latin-1': None,
            'utf-16': None,
            'ascii': None
        }
        
        for enc in encodings:
            try:
                encodings[enc] = byte_array.decode(enc, errors='replace')
            except:
                encodings[enc] = "Decoding failed"
    except:
        encodings = {enc: "Analysis failed" for enc in ['utf-8', 'latin-1', 'utf-16', 'ascii']}
    
    # Return analysis
    return {
        'length': len(clean_binary),
        'bytes': total_bytes,
        'padding_added': padding,
        'terminator_found': terminator_pos is not None,
        'terminator_position': terminator_pos,
        'useful_bytes': terminator_pos if terminator_pos else total_bytes,
        'hex_representation': binary_to_hex(clean_binary[:min(len(clean_binary), 240)]) + "..." if len(clean_binary) > 240 else binary_to_hex(clean_binary),
        'encodings': encodings
    }

def debug_file(file_path):
    """
    Debug a steganography info file (.npz) or binary file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Analysis of file contents
    """
    if not os.path.exists(file_path):
        return {'error': f"File not found: {file_path}"}
        
    results = {'file': file_path}
    
    try:
        if file_path.endswith('.npz'):
            # Handle numpy save file
            import numpy as np
            data = np.load(file_path, allow_pickle=True)
            
            results['file_type'] = 'numpy_archive'
            results['keys'] = list(data.keys())
            
            # Check for binary message
            if 'binary_message' in data:
                binary_message = str(data['binary_message'])
                results['binary_message'] = {
                    'length': len(binary_message),
                    'analysis': analyze_binary(binary_message)
                }
            
            # Check for original message
            if 'message_original' in data:
                results['original_message'] = str(data['message_original'])
            
            # Check for other common keys
            for key in ['strength', 'positions', 'used_blocks', 'block_size']:
                if key in data:
                    results[key] = data[key]
                    if key == 'positions' or key == 'used_blocks':
                        results[f'{key}_count'] = len(data[key])
        
        elif file_path.endswith('.txt'):
            # Handle text file
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            results['file_type'] = 'text'
            results['content'] = content
            results['length'] = len(content)
            
            # If it looks like a binary string
            if all(c in '01 \n\t' for c in content):
                clean_binary = ''.join(c for c in content if c in '01')
                results['binary_analysis'] = analyze_binary(clean_binary)
        
        elif file_path.endswith('.hex'):
            # Handle hex file
            with open(file_path, 'r') as f:
                content = f.read()
            
            results['file_type'] = 'hex'
            results['content'] = content
            
            # Convert hex to binary
            try:
                # Remove whitespace and non-hex characters
                clean_hex = ''.join(c for c in content if c in '0123456789ABCDEFabcdef')
                binary = ''.join(format(int(clean_hex[i:i+2], 16), '08b') for i in range(0, len(clean_hex), 2))
                results['binary'] = binary
                results['binary_analysis'] = analyze_binary(binary)
            except:
                results['conversion_error'] = "Failed to convert hex to binary"
                
        else:
            # Generic file
            results['file_type'] = 'unknown'
            results['size'] = os.path.getsize(file_path)
    
    except Exception as e:
        results['error'] = f"Analysis error: {str(e)}"
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python binary_decoder.py <binary_string>")
        print("  or   python binary_decoder.py -f <file_path>")
        sys.exit(1)
    
    if sys.argv[1] == '-f' and len(sys.argv) >= 3:
        # Debug a file
        results = debug_file(sys.argv[2])
        print("\n=== File Analysis Results ===\n")
        
        for key, value in results.items():
            if key == 'binary_analysis' or key == 'encodings':
                print(f"\n{key.upper()}:")
                for subkey, subvalue in value.items():
                    print(f"  {subkey}: {subvalue}")
            elif isinstance(value, dict):
                print(f"\n{key.upper()}:")
                for subkey, subvalue in value.items():
                    print(f"  {subkey}: {subvalue}")
            else:
                print(f"{key}: {value}")
    else:
        # Analyze a binary string
        binary = ''.join(c for c in sys.argv[1] if c in '01')
        
        if not binary:
            print("Error: No valid binary data found.")
            sys.exit(1)
        
        analysis = analyze_binary(binary)
        
        print("\n=== Binary Analysis ===")
        for key, value in analysis.items():
            if key == 'encodings':
                print("\nEncoding Results:")
                for enc, result in value.items():
                    print(f"  {enc}: {result}")
            else:
                print(f"{key}: {value}")

        print("\nDecoded text (ASCII):", binary_to_text(binary))
