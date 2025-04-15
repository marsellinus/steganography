import numpy as np
import cv2
from PIL import Image
import math

class DCTSteganography:
    def __init__(self, block_size=8, quantization_factor=10):
        self.block_size = block_size
        self.quantization_factor = quantization_factor
    
    def encode(self, cover_image_path, message, output_path):
        """
        Hide a message in a cover image using DCT transform domain steganography
        
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
        
        # Convert to YCrCb color space (working with Y channel)
        ycrcb_img = cv2.cvtColor(cover_img, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb_img[:,:,0].astype(float)
        
        height, width = y_channel.shape
        
        # Calculate how many message bits we can hide
        max_message_bits = (height // self.block_size) * (width // self.block_size)
        if len(binary_message) > max_message_bits:
            raise ValueError(f"Message too long! Max {max_message_bits} bits, got {len(binary_message)}")
        
        message_index = 0
        
        # Process each 8x8 block
        for y in range(0, height - self.block_size + 1, self.block_size):
            for x in range(0, width - self.block_size + 1, self.block_size):
                if message_index >= len(binary_message):
                    break
                    
                # Extract the block
                block = y_channel[y:y+self.block_size, x:x+self.block_size]
                
                # Apply DCT
                dct_block = cv2.dct(block)
                
                # Modify mid-frequency coefficient to hide 1 bit
                # Using (4,5) coefficient as an example - mid-frequency area
                bit = int(binary_message[message_index])
                
                if bit == 0:
                    # Make coefficient even
                    dct_block[4, 5] = self.quantization_factor * math.floor(dct_block[4, 5] / self.quantization_factor)
                else:
                    # Make coefficient odd
                    dct_block[4, 5] = self.quantization_factor * math.floor(dct_block[4, 5] / self.quantization_factor) + self.quantization_factor / 2
                
                message_index += 1
                
                # Apply inverse DCT
                block = cv2.idct(dct_block)
                
                # Put the block back
                y_channel[y:y+self.block_size, x:x+self.block_size] = block
            
            if message_index >= len(binary_message):
                break
        
        # Convert back to uint8 and update the Y channel
        ycrcb_img[:,:,0] = np.clip(y_channel, 0, 255).astype(np.uint8)
        
        # Convert back to RGB
        stego_img = cv2.cvtColor(ycrcb_img, cv2.COLOR_YCrCb2BGR)
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        return output_path
    
    def decode(self, stego_image_path):
        """
        Extract hidden message from a stego image using DCT transform domain
        
        Args:
            stego_image_path: Path to the stego image
            
        Returns:
            Extracted message as a string
        """
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Convert to YCrCb and extract Y channel
        ycrcb_img = cv2.cvtColor(stego_img, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb_img[:,:,0].astype(float)
        
        height, width = y_channel.shape
        
        # Extract bits from each block
        extracted_bits = []
        
        # Set a limit for how many bits to check to avoid processing the entire image
        max_bits_to_check = min(height * width, 50000)  # Reasonable limit
        bits_checked = 0
        
        for y in range(0, height - self.block_size + 1, self.block_size):
            for x in range(0, width - self.block_size + 1, self.block_size):
                # Extract the block
                block = y_channel[y:y+self.block_size, x:x+self.block_size]
                
                # Apply DCT
                dct_block = cv2.dct(block)
                
                # Check if coefficient is even or odd
                coef = dct_block[4, 5]
                quantized_coef = coef / self.quantization_factor
                
                # More reliable detection of even/odd
                remainder = abs(quantized_coef % 1.0)
                if 0.25 < remainder < 0.75:  # Wider range for detecting embedded '1'
                    extracted_bits.append(1)
                else:
                    extracted_bits.append(0)
                
                bits_checked += 1
                
                # Check for terminator sequence (8 zeros)
                if len(extracted_bits) >= 8:
                    last_byte = extracted_bits[-8:]
                    if last_byte == [0, 0, 0, 0, 0, 0, 0, 0]:
                        # Found terminator, remove it and stop
                        return self._bits_to_message(extracted_bits[:-8])
                
                # Stop if we've checked enough bits
                if bits_checked >= max_bits_to_check:
                    break
            
            if bits_checked >= max_bits_to_check:
                break
        
        # If no terminator was found or we've reached the limit, still try to convert the bits
        message = self._bits_to_message(extracted_bits)
        
        # Return an empty string instead of None if no valid message was found
        return message if message else ""

    def _bits_to_message(self, bits):
        """Helper method to convert bit array to ASCII text"""
        if not bits:
            return ""
            
        # Ensure bits length is multiple of 8 for clean byte conversion
        while len(bits) % 8 != 0:
            bits.append(0)
            
        message = ""
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = bits[i:i+8]
                try:
                    char_code = int(''.join(map(str, byte)), 2)
                    # Accept a wider range of characters, not just printable ASCII
                    if 32 <= char_code <= 126 or char_code in [9, 10, 13]:  # Include tab, LF, CR
                        message += chr(char_code)
                    else:
                        # Found a character outside our accepted range
                        # Instead of breaking, we just append a placeholder
                        message += "�"
                except:
                    # If conversion fails, we've likely hit the end
                    break
                    
        return message
