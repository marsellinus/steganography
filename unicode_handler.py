"""
Module untuk menangani konversi teks Unicode ke representasi biner dan sebaliknya
dengan fitur penanganan error yang lebih baik.
"""
import re

def text_to_binary_unicode(text):
    """
    Convert text to binary representation, properly handling Unicode
    
    Args:
        text: Text string to convert
        
    Returns:
        Binary string (0s and 1s)
    """
    if not text:
        return ""
        
    # Use UTF-8 encoding for full Unicode support
    binary = ""
    # Encode text as UTF-8 bytes and convert to binary
    for byte in text.encode('utf-8'):
        binary += bin(byte)[2:].zfill(8)  # Remove '0b' prefix and pad to 8 bits
        
    return binary

def binary_to_text_unicode(binary_str):
    """
    Convert binary string to text with proper Unicode handling
    
    Args:
        binary_str: String of 0s and 1s
        
    Returns:
        Decoded text string
    """
    if not binary_str:
        return ""
    
    # Clean binary string to ensure it contains only 0s and 1s
    binary_str = ''.join(c for c in str(binary_str) if c in '01')
    
    # Ensure length is a multiple of 8
    remainder = len(binary_str) % 8
    if remainder != 0:
        binary_str = binary_str + '0' * (8 - remainder)
    
    # Convert to bytes
    bytes_list = bytearray()
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if len(byte) == 8:  # Just to be safe
            try:
                bytes_list.append(int(byte, 2))
            except:
                continue
    
    # Decode the bytes as UTF-8
    try:
        text = bytes_list.decode('utf-8', errors='replace')
        return text
    except Exception as e:
        # If UTF-8 decoding fails, try a more lenient approach
        text = ""
        for byte in bytes_list:
            if byte == 0:  # Null terminator
                break
            if byte < 128:  # ASCII range
                text += chr(byte)
            else:
                text += "�"  # Replacement character for non-ASCII
        return text

def sanitize_text(text):
    """
    Sanitize text by removing problematic characters or fixing encoding issues
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
        
    # Re-encode to UTF-8 to fix any encoding issues
    try:
        text = text.encode('utf-8', errors='replace').decode('utf-8')
        
        # Remove null bytes and other problematic control characters
        text = ''.join(c for c in text if ord(c) > 31 or c in ('\n', '\t', '\r'))
        
        return text
    except Exception as e:
        print(f"Error sanitizing text: {e}")
        # Return a fallback safe string
        return ''.join(c for c in text if ord(c) < 128)
