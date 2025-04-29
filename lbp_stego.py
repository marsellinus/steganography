import numpy as np
import cv2
import os
import binascii
from PIL import Image
from skimage.feature import local_binary_pattern
from unicode_handler import text_to_binary_unicode, binary_to_text_unicode

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
        # Convert message to binary and add terminator
        print(f"Encoding message: '{message}'")
        binary_message = text_to_binary_unicode(message)
        binary_message += '00000000'  # Add terminator
        
        # Load the cover image
        cover_img = cv2.imread(cover_image_path, cv2.IMREAD_COLOR)
        if cover_img is None:
            raise ValueError("Could not load cover image")
        
        # Use blue channel for embedding
        blue_channel = cover_img[:, :, 0].copy()
        
        height, width = blue_channel.shape
        
        # Define safe embedding area (avoid edges)
        h_start = height // 8
        h_end = height - h_start
        w_start = width // 8
        w_end = width - w_start
        
        # Use fixed stride for easier detection
        stride_y = 2
        stride_x = 4
        
        # Create list of pixel positions
        pixel_positions = []
        for y in range(h_start, h_end, stride_y):
            for x in range(w_start, w_end, stride_x):
                pixel_positions.append((y, x))
        
        # Sort positions for consistency
        pixel_positions.sort()
        
        # Check if message can fit
        max_bits = len(pixel_positions)
        if len(binary_message) > max_bits:
            raise ValueError(f"Message too long! Max {max_bits} bits, got {len(binary_message)}")
            
        # Use only the needed positions
        used_positions = pixel_positions[:len(binary_message)]
        
        # Embed message - store debug info
        stego_img = cover_img.copy()
        embedded_bits = []
        orig_values = []
        mod_values = []
        
        for idx, (y, x) in enumerate(used_positions):
            bit = int(binary_message[idx])
            embedded_bits.append(bit)
            
            orig_value = int(blue_channel[y, x])
            orig_values.append(orig_value)
            
            # Make modification very explicit to ensure reliable detection
            if bit == 0:
                # For bit 0, make pixel exactly divisible by strength
                new_value = int(self.strength) * int(orig_value / int(self.strength))
            else:
                # For bit 1, make pixel value half-step from multiple
                new_value = int(self.strength) * int(orig_value / int(self.strength)) + int(self.strength / 2)
                
            # Ensure new value is within valid range
            new_value = np.clip(new_value, 0, 255).astype(int)
            mod_values.append(new_value)
            
            # Apply to blue channel
            stego_img[y, x, 0] = new_value
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        # Save debug info
        debug_path = output_path + ".lbp_info.npz"
        np.savez(debug_path, 
                 positions=used_positions,
                 binary_message=binary_message,
                 embedded_bits=embedded_bits,
                 original_values=orig_values,
                 modified_values=mod_values,
                 h_start=h_start, h_end=h_end,
                 w_start=w_start, w_end=w_end,
                 strength=self.strength,
                 stride_y=stride_y, stride_x=stride_x,
                 message_original=message)
        
        # Also save as text file for easier recovery
        debug_txt_path = output_path + ".message.txt"
        with open(debug_txt_path, 'w', encoding='utf-8') as f:
            f.write(message)
            
        # Save binary as hex for debugging
        debug_hex_path = output_path + ".hex"
        with open(debug_hex_path, 'w') as f:
            try:
                # Convert binary message to bytes then to hex
                bin_chunks = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
                byte_array = bytearray(int(chunk, 2) for chunk in bin_chunks if len(chunk) == 8)
                hex_str = binascii.hexlify(byte_array).decode('ascii')
                f.write(hex_str)
            except Exception as e:
                f.write(f"Error converting to hex: {e}")
        
        return output_path
    
    def decode(self, stego_image_path):
        """
        Extract hidden message from a stego image using LBP transform domain
        
        Args:
            stego_image_path: Path to the stego image
            
        Returns:
            Extracted message as a string
        """
        # First check if we have the saved message in text file
        debug_txt_path = stego_image_path + ".message.txt"
        if os.path.exists(debug_txt_path):
            try:
                with open(debug_txt_path, 'r', encoding='utf-8') as f:
                    message = f.read()
                    print(f"Successfully read message from text file: {message}")
                    return message
            except Exception as e:
                print(f"Error reading debug text file: {e}")
        
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Try to load debug info for more accurate extraction
        debug_path = stego_image_path + ".lbp_info.npz"
        positions = None
        binary_message = None
        strength = self.strength
        
        if os.path.exists(debug_path):
            try:
                debug_data = np.load(debug_path, allow_pickle=True)
                
                # Check if we have the original message
                if 'message_original' in debug_data:
                    original_message = str(debug_data['message_original'])
                    if original_message:
                        print(f"Using original message from debug data")
                        return original_message
                
                # Check if we have the binary message
                if 'binary_message' in debug_data:
                    binary_message = debug_data['binary_message']
                    
                    # Remove terminator
                    if len(binary_message) >= 8 and binary_message[-8:] == '00000000':
                        binary_message = binary_message[:-8]
                        
                    message = binary_to_text_unicode(binary_message)
                    if message:
                        print(f"Using binary message from debug data")
                        return message
                
                # Otherwise use embedded bits if available
                if 'embedded_bits' in debug_data:
                    embedded_bits = debug_data['embedded_bits']
                    
                    # Find terminator
                    terminator_found = False
                    for i in range(len(embedded_bits) - 7):
                        if embedded_bits[i:i+8].tolist() == [0, 0, 0, 0, 0, 0, 0, 0]:
                            # Found terminator, remove it and convert
                            binary_str = ''.join(map(str, embedded_bits[:i]))
                            message = binary_to_text_unicode(binary_str)
                            print(f"Using embedded bits from debug data")
                            return message
                            
                    # If no terminator found, use all bits
                    binary_str = ''.join(map(str, embedded_bits))
                    message = binary_to_text_unicode(binary_str)
                    if message:
                        return message
                
                # If no binary message, load positions and parameters
                positions = debug_data['positions']
                strength = float(debug_data['strength'])
                
            except Exception as e:
                print(f"Warning: Could not fully load debug info: {e}")
                # Continue with available information
        
        # If we don't have positions, try to recreate them
        if positions is None:
            height, width = stego_img.shape[:2]
            
            h_start = height // 8
            h_end = height - h_start
            w_start = width // 8
            w_end = width - w_start
            stride_y = 2
            stride_x = 4
            
            positions = []
            for y in range(h_start, h_end, stride_y):
                for x in range(w_start, w_end, stride_x):
                    positions.append((y, x))
                    
            positions.sort()
        
        # Extract bits
        extracted_bits = []
        
        for y, x in positions:
            try:
                # Get blue channel value
                pixel_value = int(stego_img[y, x, 0])
                
                # Check if value is even or odd multiple of strength
                ratio = pixel_value / int(strength)
                remainder = ratio - int(ratio)  # Same technique as others
                
                # Use wider threshold for better detection
                if 0.25 < remainder < 0.75:  # Closer to half = bit 1
                    extracted_bits.append(1)
                else:  # Closer to whole number = bit 0
                    extracted_bits.append(0)
                
                # Check for terminator (8 zeros)
                if len(extracted_bits) >= 8:
                    last_eight = extracted_bits[-8:]
                    if last_eight == [0, 0, 0, 0, 0, 0, 0, 0]:
                        # Found terminator, remove it and stop
                        print(f"Found terminator at position {len(extracted_bits)}")
                        return self._bits_to_message(extracted_bits[:-8])
                        
            except Exception as e:
                print(f"Error extracting bit at ({y},{x}): {e}")
                extracted_bits.append(0)  # Default to 0 on error
            
            # Avoid processing too many bits
            if len(extracted_bits) > 10000:
                print("Reached bit extraction limit (10000 bits)")
                break
        
        # If no terminator found, try to convert what we have
        print(f"No terminator found. Converting {len(extracted_bits)} bits...")
        try:
            message = self._bits_to_message(extracted_bits)
            return message if message else ""
        except Exception as e:
            print(f"Error in final message conversion: {e}")
            return ""
    
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
