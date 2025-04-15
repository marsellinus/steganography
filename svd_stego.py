import numpy as np
import cv2
from PIL import Image

class SVDSteganography:
    def __init__(self, strength=10.0, block_size=8):
        self.strength = strength
        self.block_size = block_size
    
    def encode(self, cover_image_path, message, output_path):
        """
        Hide a message in a cover image using SVD transform domain steganography
        
        Args:
            cover_image_path: Path to the cover image
            message: Secret message to hide
            output_path: Where to save the resulting stego image
        """
        # Convert message to binary
        binary_message = ''.join(format(ord(c), '08b') for c in message)
        binary_message += '00000000'  # Add terminator
        
        # Load the cover image
        cover_img = cv2.imread(cover_image_path, cv2.IMREAD_COLOR)
        if cover_img is None:
            raise ValueError("Could not load cover image")
        
        # Work with the red channel for SVD
        red_channel = cover_img[:, :, 2].astype(np.float64)
        
        height, width = red_channel.shape
        
        # Calculate how many blocks we have and if we can fit the message
        blocks_h = height // self.block_size
        blocks_w = width // self.block_size
        total_blocks = blocks_h * blocks_w
        
        if len(binary_message) > total_blocks:
            raise ValueError(f"Message too long! Max {total_blocks} bits, got {len(binary_message)}")
        
        # Process each block to embed message bits
        message_index = 0
        modified_channel = red_channel.copy()
        
        for y in range(0, blocks_h * self.block_size, self.block_size):
            for x in range(0, blocks_w * self.block_size, self.block_size):
                if message_index >= len(binary_message):
                    break
                    
                # Extract the block
                block = red_channel[y:y+self.block_size, x:x+self.block_size]
                
                # Apply SVD
                U, S, Vt = np.linalg.svd(block, full_matrices=False)
                
                # Modify the largest singular value based on the message bit
                bit = int(binary_message[message_index])
                
                if bit == 0:
                    # Make the largest singular value even multiple of strength
                    S[0] = self.strength * np.floor(S[0] / self.strength)
                else:
                    # Make the largest singular value odd multiple of strength
                    S[0] = self.strength * np.floor(S[0] / self.strength) + self.strength / 2
                
                # Reconstruct the block
                modified_block = U @ np.diag(S) @ Vt
                modified_channel[y:y+self.block_size, x:x+self.block_size] = modified_block
                
                message_index += 1
            
            if message_index >= len(binary_message):
                break
        
        # Create stego image by replacing the red channel
        stego_img = cover_img.copy()
        stego_img[:, :, 2] = np.clip(modified_channel, 0, 255).astype(np.uint8)
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        return output_path
    
    def decode(self, stego_image_path):
        """
        Extract hidden message from a stego image using SVD transform domain
        
        Args:
            stego_image_path: Path to the stego image
            
        Returns:
            Extracted message as a string
        """
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Extract red channel
        red_channel = stego_img[:, :, 2].astype(np.float64)
        
        height, width = red_channel.shape
        blocks_h = height // self.block_size
        blocks_w = width // self.block_size
        
        # Extract bits from each block
        extracted_bits = []
        
        for y in range(0, blocks_h * self.block_size, self.block_size):
            for x in range(0, blocks_w * self.block_size, self.block_size):
                # Extract the block
                block = red_channel[y:y+self.block_size, x:x+self.block_size]
                
                # Apply SVD
                U, S, Vt = np.linalg.svd(block, full_matrices=False)
                
                # Check if the largest singular value is even or odd multiple of strength
                remainder = (S[0] % self.strength) / self.strength
                
                if 0.35 < remainder < 0.65:  # Close to half-step
                    extracted_bits.append(1)
                else:
                    extracted_bits.append(0)
                
                # Check for terminator sequence
                if len(extracted_bits) >= 8 and extracted_bits[-8:] == [0, 0, 0, 0, 0, 0, 0, 0]:
                    # Found terminator, remove it and stop
                    return self._bits_to_message(extracted_bits[:-8])
        
        # If no terminator was found, try to convert all bits
        return self._bits_to_message(extracted_bits)
    
    def _bits_to_message(self, bits):
        """Convert a sequence of bits to an ASCII message"""
        if not bits:
            return ""
            
        # Make sure we have a multiple of 8 bits
        while len(bits) % 8 != 0:
            bits.append(0)
        
        # Convert each byte to a character
        message = ""
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = bits[i:i+8]
                try:
                    char_code = int(''.join(map(str, byte)), 2)
                    # Only accept printable ASCII characters
                    if 32 <= char_code <= 126:
                        message += chr(char_code)
                    else:
                        # Found a non-printable character, might be end of message
                        break
                except:
                    break
        
        return message
