import numpy as np
import cv2
import os
from PIL import Image
from unicode_handler import text_to_binary_unicode, binary_to_text_unicode

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
        # Gunakan fungsi unicode handler untuk encoding
        binary_message = text_to_binary_unicode(message)
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
        r_min = crow - rows // 8
        r_max = crow - rows // 16
        c_min = ccol - cols // 8
        c_max = ccol + cols // 8
        
        # Check if we can fit the message
        embed_capacity = (r_max - r_min) * (c_max - c_min)
        if len(binary_message) > embed_capacity:
            raise ValueError(f"Message too long! Max {embed_capacity} bits, got {len(binary_message)}")
        
        # Ensure consistent encoding by using fixed positions
        embed_positions = []
        for i in range(r_min, r_max):
            for j in range(c_min, c_max):
                embed_positions.append((i, j))
        
        # Sort positions to ensure consistent encoding/decoding
        embed_positions.sort()
        embed_positions = embed_positions[:len(binary_message)]
        
        # Save original binary data for debug
        original_binary = binary_message
        
        # Embed the message in the magnitude of selected components
        for idx, (i, j) in enumerate(embed_positions):
            if idx >= len(binary_message):
                break
                
            bit = int(binary_message[idx])
            
            # Calculate magnitude
            magnitude = np.sqrt(dft_shift[i, j, 0]**2 + dft_shift[i, j, 1]**2)
            
            # Calculate new magnitude based on bit
            if bit == 0:
                new_magnitude = self.strength * np.floor(magnitude / self.strength)
            else:
                new_magnitude = self.strength * np.floor(magnitude / self.strength) + self.strength / 2
                
            if magnitude != 0:
                # Scale real and imaginary components to achieve the new magnitude
                scale = new_magnitude / magnitude
                dft_shift[i, j, 0] *= scale
                dft_shift[i, j, 1] *= scale
        
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
        
        # Save debugging info
        debug_path = output_path + ".dft_info.npz"
        np.savez(debug_path, 
                 positions=embed_positions,
                 binary_message=original_binary,
                 strength=self.strength,
                 r_min=r_min, r_max=r_max, 
                 c_min=c_min, c_max=c_max,
                 message_original=message)
        
        # Also save as text file for easier debugging
        debug_txt_path = output_path + ".message.txt"
        with open(debug_txt_path, 'w', encoding='utf-8') as f:
            f.write(message)
        
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
        
        # Check for debug info to help with extraction
        debug_path = stego_image_path + ".dft_info.npz"
        debug_txt_path = stego_image_path + ".message.txt"
        
        # Try to load original message from text file first
        if os.path.exists(debug_txt_path):
            try:
                with open(debug_txt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"Warning: Could not load debug text: {e}")
        
        # Try loading debug info
        embed_positions = None
        binary_message = None
        strength = self.strength
        original_message = None

        try:
            if os.path.exists(debug_path):
                debug_data = np.load(debug_path, allow_pickle=True)
                
                # If we have the original binary message, use it directly
                if 'binary_message' in debug_data:
                    binary_message = debug_data['binary_message']
                    if len(binary_message) >= 8 and binary_message[-8:] == '00000000':
                        # Remove terminator
                        return binary_to_text_unicode(binary_message[:-8])
                
                # If original message is available, use it
                if 'message_original' in debug_data:
                    original_message = str(debug_data['message_original'])
                    if original_message:
                        return original_message
                
                # Get embedding positions and strength
                if 'positions' in debug_data:
                    embed_positions = debug_data['positions']
                if 'strength' in debug_data:
                    strength = float(debug_data['strength'])
        except Exception as e:
            print(f"Warning: Could not load debug data: {e}")
        
        # Work with the green channel
        green_channel = stego_img[:, :, 1].astype(np.float32)
        
        # Apply DFT
        dft = cv2.dft(green_channel, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # If no predetermined positions, reconstruct them
        if embed_positions is None:
            rows, cols = green_channel.shape
            crow, ccol = rows // 2, cols // 2
            r_min = crow - rows // 8
            r_max = crow - rows // 16
            c_min = ccol - cols // 8
            c_max = ccol + cols // 8
            
            embed_positions = []
            for i in range(r_min, r_max):
                for j in range(c_min, c_max):
                    embed_positions.append((i, j))
            embed_positions.sort()
        
        # Extract bits
        extracted_bits = []
        
        max_bits = 50000  # Safety limit
        for idx, (i, j) in enumerate(embed_positions):
            if idx >= max_bits:
                break
                
            # Calculate magnitude
            magnitude = np.sqrt(dft_shift[i, j, 0]**2 + dft_shift[i, j, 1]**2)
            
            # Check if magnitude is even or odd multiple of strength
            ratio = magnitude / strength
            remainder = ratio - np.floor(ratio)
            
            # Use a threshold to determine if it's a 0 or 1
            if 0.25 < remainder < 0.75:
                extracted_bits.append(1)
            else:
                extracted_bits.append(0)
            
            # Check for terminator
            if len(extracted_bits) >= 8 and extracted_bits[-8:] == [0, 0, 0, 0, 0, 0, 0, 0]:
                return self._bits_to_message(extracted_bits[:-8])
                
        # If no terminator found, return what we have
        return self._bits_to_message(extracted_bits)
    
    def _bits_to_message(self, bits):
        """Helper method to convert bit array to text with proper Unicode support"""
        if not bits:
            return ""
        
        # Konversi bit array ke string untuk diproses
        binary_str = ''.join(map(str, bits))
        
        # Gunakan fungsi unicode handler untuk dekode
        try:
            return binary_to_text_unicode(binary_str)
        except Exception as e:
            print(f"Error in bits_to_message: {e}")
            return ""
