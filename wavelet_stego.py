import numpy as np
import pywt
import cv2
from PIL import Image

class WaveletSteganography:
    def __init__(self, wavelet='haar', level=1, threshold=30):
        self.wavelet = wavelet
        self.level = level
        self.threshold = threshold
    
    def encode(self, cover_image_path, message, output_path):
        """
        Hide a message in a cover image using Wavelet transform domain steganography
        
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
        
        # Work with the blue channel for simplicity
        blue_channel = cover_img[:, :, 0].astype(np.float64)
        
        # Apply wavelet transform
        coeffs = pywt.dwt2(blue_channel, self.wavelet)
        cA, (cH, cV, cD) = coeffs
        
        # Embed message in the horizontal detail coefficients (cH)
        message_index = 0
        height, width = cH.shape
        
        # Check if message can fit
        if len(binary_message) > height * width:
            raise ValueError(f"Message too long! Max {height * width} bits, got {len(binary_message)}")
        
        for y in range(height):
            for x in range(width):
                if message_index >= len(binary_message):
                    break
                    
                bit = int(binary_message[message_index])
                
                # Modify coefficient based on bit value
                if bit == 0:
                    # Make coefficient even by rounding to nearest even number
                    cH[y, x] = round(cH[y, x] / self.threshold) * self.threshold
                else:
                    # Make coefficient odd by rounding to nearest odd number
                    cH[y, x] = round(cH[y, x] / self.threshold) * self.threshold + self.threshold / 2
                
                message_index += 1
            
            if message_index >= len(binary_message):
                break
        
        # Apply inverse wavelet transform
        modified_coeffs = cA, (cH, cV, cD)
        blue_channel_modified = pywt.idwt2(modified_coeffs, self.wavelet)
        
        # Handle size mismatch due to wavelet transform
        if blue_channel_modified.shape != cover_img[:, :, 0].shape:
            blue_channel_modified = blue_channel_modified[:cover_img.shape[0], :cover_img.shape[1]]
        
        # Create stego image
        stego_img = cover_img.copy()
        stego_img[:, :, 0] = np.clip(blue_channel_modified, 0, 255).astype(np.uint8)
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        return output_path
    
    def decode(self, stego_image_path):
        """
        Extract hidden message from a stego image using Wavelet transform domain
        
        Args:
            stego_image_path: Path to the stego image
            
        Returns:
            Extracted message as a string
        """
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Extract blue channel
        blue_channel = stego_img[:, :, 0].astype(np.float64)
        
        # Apply wavelet transform
        coeffs = pywt.dwt2(blue_channel, self.wavelet)
        cA, (cH, cV, cD) = coeffs
        
        # Extract bits from the horizontal detail coefficients
        extracted_bits = []
        height, width = cH.shape
        
        # Set a reasonable limit
        max_bits_to_check = min(height * width, 50000)
        bits_checked = 0
        
        for y in range(height):
            for x in range(width):
                # Check if coefficient is even or odd
                coef = cH[y, x]
                normalized = coef / self.threshold
                
                # Improved remainder calculation with wider tolerance
                remainder = abs(normalized % 1.0)
                
                # Adjust the threshold range for more reliable detection
                if 0.2 < remainder < 0.8:  # Even wider range
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
        
        # If no terminator was found, still try to convert what we have
        message = self._bits_to_message(extracted_bits)
        
        # Return an empty string instead of None if no valid message was found
        return message if message else ""

    def _bits_to_message(self, bits):
        """Helper method to convert bit array to ASCII text"""
        if not bits:
            return ""
            
        # Ensure bits length is multiple of 8
        while len(bits) % 8 != 0:
            bits.append(0)
            
        message = ""
        # Convert each byte to a character
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = bits[i:i+8]
                try:
                    char_code = int(''.join(map(str, byte)), 2)
                    # Accept a wider range of characters
                    if 32 <= char_code <= 126 or char_code in [9, 10, 13]:
                        message += chr(char_code)
                    else:
                        # Instead of breaking, continue with a placeholder
                        message += "�"
                except:
                    # If conversion fails, we've likely hit the end
                    break
        
        return message
