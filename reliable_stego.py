import cv2
import numpy as np

class ReliableSteganography:
    """
    A reliable LSB-based steganography implementation to replace problematic methods
    """
    
    def __init__(self, strength=10.0):
        # Keep strength parameter for compatibility, though it's not used
        self.strength = strength
        self.terminator = '00000000'  # 8 zeros as terminator
    
    def encode(self, cover_image_path, message, output_path):
        # Load image
        img = cv2.imread(cover_image_path)
        if img is None:
            raise ValueError("Could not read the cover image")
        
        # Convert message to binary
        binary_message = ''.join(format(ord(char), '08b') for char in message) + self.terminator
        message_length = len(binary_message)
        
        # Check capacity
        height, width = img.shape[:2]
        if height * width < message_length:
            raise ValueError(f"Image too small for message. Max capacity: {height * width} bits")
        
        # Create a copy of the image
        stego_img = img.copy()
        
        # Embed message in the LSB of blue channel pixels
        idx = 0
        for y in range(height):
            for x in range(width):
                if idx < message_length:
                    # Get current blue value
                    blue = stego_img[y, x, 0]
                    
                    # Clear LSB and set according to message bit
                    blue = (blue & 0xFE) | int(binary_message[idx])
                    
                    # Update pixel
                    stego_img[y, x, 0] = blue
                    idx += 1
                else:
                    break
            if idx >= message_length:
                break
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
    def decode(self, stego_image_path):
        # Load image
        img = cv2.imread(stego_image_path)
        if img is None:
            raise ValueError("Could not read the stego image")
        
        # Extract binary message from LSB
        binary_message = ""
        height, width = img.shape[:2]
        
        for y in range(height):
            for x in range(width):
                # Get LSB of blue channel
                bit = str(img[y, x, 0] & 1)
                binary_message += bit
                
                # Check for terminator
                if len(binary_message) >= len(self.terminator) and binary_message[-len(self.terminator):] == self.terminator:
                    # Found terminator, convert to text
                    binary_message = binary_message[:-len(self.terminator)]
                    
                    message = ""
                    for i in range(0, len(binary_message), 8):
                        if i + 8 <= len(binary_message):
                            byte = binary_message[i:i+8]
                            try:
                                message += chr(int(byte, 2))
                            except:
                                pass
                    
                    return message
                
                # Set a reasonable limit
                if len(binary_message) > 100000:  # ~12KB text
                    break
            
            if len(binary_message) > 100000:
                break
        
        return None
