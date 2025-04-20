import cv2
import numpy as np

class SVDSteganography:
    def __init__(self, strength=10.0):
        self.strength = strength
        self.terminator = '00000000'  # 8 zeros as terminator
        
    def encode(self, cover_image_path, message, output_path):
        # Load the image
        img = cv2.imread(cover_image_path)
        if img is None:
            raise ValueError("Could not read the cover image")
            
        # Convert message to binary
        binary_message = ''.join(format(ord(char), '08b') for char in message) + self.terminator
        message_length = len(binary_message)
        
        # Work with blue channel for simplicity
        blue_channel = img[:,:,0].copy()
        height, width = blue_channel.shape
        
        # Simple LSB substitution for SVD method
        idx = 0
        modified_blue = blue_channel.copy()
        
        for y in range(height):
            for x in range(width):
                if idx < message_length:
                    pixel = int(modified_blue[y, x])
                    # Clear the LSB
                    pixel = pixel & 0xFE
                    # Set LSB according to message bit
                    if binary_message[idx] == '1':
                        pixel = pixel | 1
                    # Update pixel
                    modified_blue[y, x] = pixel
                    idx += 1
                else:
                    break
            if idx >= message_length:
                break
        
        # Create output image
        stego_img = img.copy()
        stego_img[:,:,0] = modified_blue
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
    def decode(self, stego_image_path):
        # Load the stego image
        img = cv2.imread(stego_image_path)
        if img is None:
            raise ValueError("Could not read the stego image")
            
        # Extract blue channel
        blue_channel = img[:,:,0]
        height, width = blue_channel.shape
        
        # Extract message from LSBs
        binary_message = ""
        
        for y in range(height):
            for x in range(width):
                # Get LSB
                bit = '1' if blue_channel[y, x] & 1 else '0'
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
                if len(binary_message) > 100000:  # ~12KB of text
                    break
            if len(binary_message) > 100000:
                break
        
        return None
