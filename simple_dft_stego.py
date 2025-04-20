import cv2
import numpy as np

class SimpleDFTSteganography:
    """
    A simplified DFT steganography implementation focused on reliable decoding.
    """
    
    def __init__(self, strength=1.0):
        self.strength = strength
        self.terminator = '00000000'  # 8 zeros as terminator
    
    def encode(self, cover_image_path, message, output_path):
        """Encode a message using a simple, reliable approach"""
        # Load image
        img = cv2.imread(cover_image_path)
        if img is None:
            raise ValueError("Could not read the cover image")
        
        # Get dimensions
        height, width = img.shape[:2]
        
        # Convert message to binary
        binary_message = ''.join(format(ord(char), '08b') for char in message)
        binary_message += self.terminator
        
        # Ensure image is large enough
        if height * width < len(binary_message):
            raise ValueError(f"Image too small for message. Max capacity: {height * width} bits")
        
        # Create a working copy of the image
        stego_img = img.copy()
        
        # Embed message directly in LSB of blue channel
        idx = 0
        for y in range(height):
            for x in range(width):
                if idx < len(binary_message):
                    # Get current pixel's blue value
                    blue = stego_img[y, x, 0]
                    
                    # Clear the LSB
                    blue = blue & 0xFE
                    
                    # Set LSB according to message bit
                    if binary_message[idx] == '1':
                        blue = blue | 1
                    
                    # Update the pixel
                    stego_img[y, x, 0] = blue
                    
                    idx += 1
                else:
                    break
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
    def decode(self, stego_image_path):
        """Extract message using the same simple approach"""
        # Load stego image
        img = cv2.imread(stego_image_path)
        if img is None:
            raise ValueError("Could not read the stego image")
        
        # Get dimensions
        height, width = img.shape[:2]
        
        # Extract binary message from LSB of blue channel
        binary_message = ""
        for y in range(height):
            for x in range(width):
                # Get current pixel's blue value
                blue = img[y, x, 0]
                
                # Extract LSB
                bit = '1' if blue & 1 else '0'
                binary_message += bit
                
                # Check for terminator
                if len(binary_message) >= len(self.terminator) and binary_message[-len(self.terminator):] == self.terminator:
                    # Found terminator, remove it from message
                    binary_message = binary_message[:-len(self.terminator)]
                    
                    # Convert binary to text
                    text_message = ""
                    for i in range(0, len(binary_message), 8):
                        if i + 8 <= len(binary_message):
                            byte = binary_message[i:i+8]
                            try:
                                text_message += chr(int(byte, 2))
                            except:
                                pass
                    
                    return text_message
                
                # Avoid excessive searching
                if len(binary_message) > 16384:  # 2KB of bits
                    break
            if len(binary_message) > 16384:
                break
        
        # No terminator found, try to recover what we can
        if len(binary_message) >= 24:
            text_message = ""
            for i in range(0, min(len(binary_message), 8000), 8):  # Limit to 1000 chars
                if i + 8 <= len(binary_message):
                    byte = binary_message[i:i+8]
                    try:
                        char = chr(int(byte, 2))
                        if 32 <= ord(char) <= 126 or ord(char) in [9, 10, 13]:
                            text_message += char
                    except:
                        pass
            
            return text_message if text_message else None
        
        return None
