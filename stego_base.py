import numpy as np

class SteganographyBase:
    """Base class with common functionality for all steganography methods"""
    
    def __init__(self, terminator='00000000'):
        self.terminator = terminator
        
    def message_to_binary(self, message):
        """Convert a text message to binary string"""
        if not message:
            return ""
        return ''.join(format(ord(char), '08b') for char in message) + self.terminator
    
    def binary_to_message(self, binary):
        """Convert a binary string to text message"""
        if not binary:
            return ""
            
        # Find terminator
        terminator_pos = binary.find(self.terminator)
        if terminator_pos >= 0:
            binary = binary[:terminator_pos]
        
        # Convert to text
        text = ""
        for i in range(0, len(binary), 8):
            if i + 8 <= len(binary):
                byte = binary[i:i+8]
                try:
                    text += chr(int(byte, 2))
                except ValueError:
                    # Skip invalid bytes
                    pass
        
        return text
    
    def clean_message(self, message):
        """Clean a message by removing non-printable characters"""
        if not message:
            return message
            
        cleaned = ""
        for char in message:
            # Keep printable ASCII and common whitespace
            if 32 <= ord(char) <= 126 or ord(char) in [9, 10, 13]:
                cleaned += char
                
        return cleaned
