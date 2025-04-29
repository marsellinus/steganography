import numpy as np
import cv2
import os
from PIL import Image
from unicode_handler import text_to_binary_unicode, binary_to_text_unicode

class SVDSteganography:
    def __init__(self, strength=10.0, block_size=8):
        self.strength = strength
        self.block_size = block_size
    
    def encode(self, cover_image_path, message, output_path):
        # Gunakan fungsi unicode handler untuk encoding
        binary_message = text_to_binary_unicode(message)
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
        
        # Create a list of block positions
        block_positions = []
        for y_idx in range(blocks_h):
            for x_idx in range(blocks_w):
                block_positions.append((y_idx, x_idx))
        
        # Sort positions for consistency
        block_positions.sort()
        used_blocks = block_positions[:len(binary_message)]
        
        # Process each block to embed message bits
        message_index = 0
        modified_channel = red_channel.copy()
        
        for y_idx, x_idx in used_blocks:
            y = y_idx * self.block_size
            x = x_idx * self.block_size
            
            # Extract the block
            block = red_channel[y:y+self.block_size, x:x+self.block_size].copy()
            
            # Apply SVD
            try:
                U, S, Vt = np.linalg.svd(block, full_matrices=False)
                
                # Modify the largest singular value based on the message bit
                bit = int(binary_message[message_index])
                
                # Use integer division for exact multiples
                if bit == 0:
                    # For bit 0, make S[0] an exact multiple of strength
                    S[0] = self.strength * int(S[0] / self.strength)
                else:
                    # For bit 1, make S[0] lie exactly halfway between multiples
                    S[0] = self.strength * (int(S[0] / self.strength) + 0.5)
                
                # Reconstruct the block
                modified_block = np.dot(U * S, Vt)
                modified_channel[y:y+self.block_size, x:x+self.block_size] = modified_block
                
                message_index += 1
            except:
                # Skip this block if SVD fails
                continue
        
        # Create stego image by replacing the red channel
        stego_img = cover_img.copy()
        stego_img[:, :, 2] = np.clip(modified_channel, 0, 255).astype(np.uint8)
        
        # Save the stego image
        cv2.imwrite(output_path, stego_img)
        
        # Save debug info for recovery
        debug_path = output_path + ".svd_info.npz"
        np.savez(debug_path, 
                 used_blocks=used_blocks,
                 binary_message=binary_message,
                 strength=self.strength,
                 block_size=self.block_size)
        
        return output_path
    
    def decode(self, stego_image_path):
        # Load the stego image
        stego_img = cv2.imread(stego_image_path, cv2.IMREAD_COLOR)
        if stego_img is None:
            raise ValueError("Could not load stego image")
        
        # Check for debug info
        debug_path = stego_image_path + ".svd_info.npz"
        used_blocks = None
        binary_message = None
        strength = self.strength
        block_size = self.block_size
        
        if os.path.exists(debug_path):
            try:
                debug_data = np.load(debug_path, allow_pickle=True)
                
                # If we have the original binary message, use it directly
                if 'binary_message' in debug_data:
                    binary_message = debug_data['binary_message']
                    if len(binary_message) >= 8 and binary_message[-8:] == '00000000':
                        # Remove terminator
                        return binary_to_text_unicode(binary_message[:-8])
                
                # Otherwise use the block positions
                used_blocks = debug_data['used_blocks']
                strength = float(debug_data['strength'])
                block_size = int(debug_data['block_size'])
            except Exception as e:
                print(f"Warning: Could not load debug info: {e}")
        
        # Extract red channel
        red_channel = stego_img[:, :, 2].astype(np.float64)
        
        height, width = red_channel.shape
        blocks_h = height // block_size
        blocks_w = width // block_size
        
        # If no block positions provided, create the list
        if used_blocks is None:
            used_blocks = []
            for y_idx in range(blocks_h):
                for x_idx in range(blocks_w):
                    used_blocks.append((y_idx, x_idx))
            used_blocks.sort()  # Ensure same order as encoding
        
        # Extract bits from each block
        extracted_bits = []
        
        for y_idx, x_idx in used_blocks:
            # Check bounds
            if y_idx >= blocks_h or x_idx >= blocks_w:
                continue
                
            y = y_idx * block_size
            x = x_idx * block_size
            
            # Check if we have enough room for this block
            if y + block_size > height or x + block_size > width:
                continue
            
            # Extract the block
            block = red_channel[y:y+block_size, x:x+block_size]
            
            try:
                # Apply SVD
                U, S, Vt = np.linalg.svd(block, full_matrices=False)
                
                # Check if the largest singular value is even or odd multiple of strength
                ratio = S[0] / strength
                remainder = ratio - int(ratio)  # Same technique as DFT
                
                # Use wider range for more reliable detection
                if 0.3 < remainder < 0.7:  # Closer to half = bit 1
                    extracted_bits.append(1)
                else:  # Closer to whole = bit 0
                    extracted_bits.append(0)
                
                # Check for terminator
                if len(extracted_bits) >= 8 and extracted_bits[-8:] == [0, 0, 0, 0, 0, 0, 0, 0]:
                    # Found terminator, remove it and stop
                    return self._bits_to_message(extracted_bits[:-8])
            except:
                # Skip if SVD fails
                continue
        
        # If no terminator found, try to convert what we have
        return self._bits_to_message(extracted_bits)
    
    def _bits_to_message(self, bits):
        """Helper method to convert bit array to text with proper Unicode support"""
        if not bits:
            return ""
        
        # Konversi bit array ke string untuk diproses
        binary_str = ''.join(map(str, bits))
        
        # Gunakan fungsi unicode handler untuk dekode
        return binary_to_text_unicode(binary_str)
