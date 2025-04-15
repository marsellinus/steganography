import numpy as np
import cv2
from PIL import Image

class DFTSteganography:
    def __init__(self, strength=10.0):
        self.strength = strength
    
    def encode(self, cover_image_path, message, output_path):
        """
        Hide a message in a cover image using DFT transform domain steganography
        
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
        
        # Work with the green channel for DFT
        green_channel = cover_img[:, :, 1].astype(np.float32)
        
        # Apply DFT
        dft = cv2.dft(green_channel, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)  # Shift zero frequency to the center
        
        rows, cols = green_channel.shape
        crow, ccol = rows // 2, cols // 2  # Center of the image
        
        # Create a mask for the region where we'll hide data
        # We choose mid-frequency components for embedding
        mask = np.zeros((rows, cols, 2), np.uint8)
        r_min = crow - rows // 8
        r_max = crow - rows // 16
        c_min = ccol - cols // 8
        c_max = ccol + cols // 8
        
        # Check if we can fit the message
        embed_capacity = (r_max - r_min) * (c_max - c_min)
        if len(binary_message) > embed_capacity:
            raise ValueError(f"Message too long! Max {embed_capacity} bits, got {len(binary_message)}")
        
        # Embed the message in the magnitude of selected components
        message_index = 0
        
        for i in range(r_min, r_max):
            if message_index >= len(binary_message):
                break
                
            for j in range(c_min, c_max):
                if message_index >= len(binary_message):
                    break
                
                # Get magnitude
                magnitude = np.sqrt(dft_shift[i, j, 0]**2 + dft_shift[i, j, 1]**2)
                
                # Embed bit
                bit = int(binary_message[message_index])
                
                if bit == 0:
                    # Make magnitude even multiple of strength
                    new_magnitude = self.strength * np.floor(magnitude / self.strength)
                else:
                    # Make magnitude odd multiple of strength
                    new_magnitude = self.strength * np.floor(magnitude / self.strength) + self.strength / 2
                
                # If magnitude is close to zero, enforce minimum
                if new_magnitude < self.strength / 2:
                    new_magnitude = self.strength / 2 if bit == 1 else self.strength
                
                # Calculate scaling factor for real and imaginary components
                if magnitude > 0:
                    scale = new_magnitude / magnitude
                    
                    # Apply scaling to real and imaginary components
                    dft_shift[i, j, 0] *= scale
                    dft_shift[i, j, 1] *= scale
                
                message_index += 1
        
        # Inverse shift and inverse DFT
        dft_ishift = np.fft.ifftshift(dft_shift)
        img_back = cv2.idft(dft_ishift)
        img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])
        
        # Normalize the values to the range [0, 255]
        img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Create stego image by replacing the green channel
        stego_img = cover_img.copy()
        stego_img[:, :, 1] = img_back
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        return output_path
    
    def decode(self, stego_image_path):
        """
        Extract hidden message from a stego image using DFT transform domain
        
        Args:
            stego_image_path: Path to the stego image
            
        Returns:
            Extracted message as a string
        """
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Extract green channel
        green_channel = stego_img[:, :, 1].astype(np.float32)
        
        # Apply DFT
        dft = cv2.dft(green_channel, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        rows, cols = green_channel.shape
        crow, ccol = rows // 2, cols // 2
        
        # Define the same region used during embedding
        r_min = crow - rows // 8
        r_max = crow - rows // 16
        c_min = ccol - cols // 8
        c_max = ccol + cols // 8
        
        # Extract bits
        extracted_bits = []
        
        for i in range(r_min, r_max):
            for j in range(c_min, c_max):
                # Get magnitude
                magnitude = np.sqrt(dft_shift[i, j, 0]**2 + dft_shift[i, j, 1]**2)
                
                # Check if magnitude is even or odd multiple of strength
                # Allow some tolerance for numerical precision
                remainder = (magnitude % self.strength) / self.strength
                
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
