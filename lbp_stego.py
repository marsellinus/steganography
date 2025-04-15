import numpy as np
import cv2
from PIL import Image
from skimage.feature import local_binary_pattern

class LBPSteganography:
    def __init__(self, strength=10.0, radius=3, n_points=24):
        self.strength = strength
        self.radius = radius
        self.n_points = n_points
    
    def encode(self, cover_image_path, message, output_path):
        """
        Hide a message in a cover image using LBP transform domain steganography
        
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
        
        # Convert to grayscale for LBP
        gray = cv2.cvtColor(cover_img, cv2.COLOR_BGR2GRAY)
        
        # Calculate LBP
        lbp = local_binary_pattern(gray, self.n_points, self.radius, method='uniform')
        
        # Normalize LBP to 0-255
        lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Create a mask for hiding message bits
        height, width = gray.shape
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # We'll use selected regions in the LBP image (avoiding edges)
        h_start = height // 8
        h_end = height - h_start
        w_start = width // 8
        w_end = width - w_start
        
        # Calculate capacity
        max_bits = (h_end - h_start) * (w_end - w_start) // 8  # Using every 8th pixel
        
        if len(binary_message) > max_bits:
            raise ValueError(f"Message too long! Max {max_bits} bits, got {len(binary_message)}")
        
        # Embed message
        message_index = 0
        stego_lbp = lbp_normalized.copy()
        
        for y in range(h_start, h_end, 2):
            if message_index >= len(binary_message):
                break
                
            for x in range(w_start, w_end, 4):  # Using every 4th pixel horizontally
                if message_index >= len(binary_message):
                    break
                
                bit = int(binary_message[message_index])
                pixel_val = int(lbp_normalized[y, x])
                
                # Modify pixel value based on bit
                if bit == 0:
                    # Make pixel value even multiple of strength
                    stego_lbp[y, x] = int(self.strength * np.floor(pixel_val / self.strength))
                else:
                    # Make pixel value odd multiple of strength
                    stego_lbp[y, x] = int(self.strength * np.floor(pixel_val / self.strength) + self.strength / 2)
                
                message_index += 1
                mask[y, x] = 255  # Mark this pixel in the mask
        
        # Create a stego image by modifying the blue channel based on LBP changes
        stego_img = cover_img.copy()
        
        # Apply changes where mask is set
        for y in range(height):
            for x in range(width):
                if mask[y, x] == 255:
                    # Apply the modified value with some attenuation to make it less visible
                    diff = int(stego_lbp[y, x] - lbp_normalized[y, x])
                    stego_img[y, x, 0] = np.clip(cover_img[y, x, 0] + diff // 4, 0, 255)
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        return output_path
    
    def decode(self, stego_image_path):
        """
        Extract hidden message from a stego image using LBP transform domain
        
        Args:
            stego_image_path: Path to the stego image
            
        Returns:
            Extracted message as a string
        """
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Extract blue channel and convert to grayscale
        gray = cv2.cvtColor(stego_img, cv2.COLOR_BGR2GRAY)
        
        # Calculate LBP
        lbp = local_binary_pattern(gray, self.n_points, self.radius, method='uniform')
        lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Define same regions as used in encoding
        height, width = gray.shape
        h_start = height // 8
        h_end = height - h_start
        w_start = width // 8
        w_end = width - w_start
        
        # Extract bits
        extracted_bits = []
        
        for y in range(h_start, h_end, 2):
            for x in range(w_start, w_end, 4):
                pixel_val = int(stego_img[y, x, 0])
                
                # Check if pixel value is even or odd multiple of strength
                remainder = (pixel_val % self.strength) / self.strength
                
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
