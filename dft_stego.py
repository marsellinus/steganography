import cv2
import numpy as np

class DFTSteganography:
    def __init__(self, strength=10.0):
        self.strength = strength
        self.terminator = '00000000'  # 8 zeros as terminator
        
    def encode(self, cover_image_path, message, output_path):
        # Load the image - preserve color channels
        img = cv2.imread(cover_image_path)
        if img is None:
            raise ValueError("Could not read the cover image")
            
        # Convert message to binary
        binary_message = ''.join(format(ord(char), '08b') for char in message) + self.terminator
        message_length = len(binary_message)
        
        # Process the blue channel for embedding
        blue = img[:,:,0].copy()
        rows, cols = blue.shape
            
        # Apply DFT to blue channel
        blue_float = np.float32(blue)
        dft = cv2.dft(blue_float, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # Get magnitude and phase
        magnitude, phase = cv2.cartToPolar(dft_shift[:,:,0], dft_shift[:,:,1])
        
        # Ensure the image is large enough for the message
        if rows * cols < message_length:
            raise ValueError(f"Cover image too small for the message. Maximum capacity: {rows * cols} bits")
            
        # Embed message in magnitude - focusing on mid-frequency components
        start_row, start_col = rows//4, cols//4
        
        idx = 0
        for i in range(start_row, 3*start_row):
            if idx >= message_length:
                break
            for j in range(start_col, 3*start_col):
                if idx >= message_length:
                    break
                    
                # Skip DC component (center of the spectrum)
                if i == rows//2 and j == cols//2:
                    continue
                    
                # Modify magnitude values to embed message bit
                bit = int(binary_message[idx])
                
                # Use a simple even/odd encoding - more robust
                if bit == 1:
                    # Make magnitude odd when bit is 1
                    if int(magnitude[i, j]) % 2 == 0:
                        magnitude[i, j] += 1
                else:
                    # Make magnitude even when bit is 0
                    if int(magnitude[i, j]) % 2 == 1:
                        magnitude[i, j] += 1
                idx += 1
                
        # Convert back to cartesian coordinates
        dft_shift[:,:,0], dft_shift[:,:,1] = cv2.polarToCart(magnitude, phase)
        
        # Inverse shift
        idft_shift = np.fft.ifftshift(dft_shift)
        
        # Inverse DFT
        idft = cv2.idft(idft_shift)
        blue_back = cv2.magnitude(idft[:,:,0], idft[:,:,1])
        
        # Normalize and update only the blue channel
        blue_modified = np.uint8(cv2.normalize(blue_back, None, 0, 255, cv2.NORM_MINMAX))
        
        # Create stego image by combining the modified blue channel with original green and red
        stego_img = img.copy()
        stego_img[:,:,0] = blue_modified
        
        # Save the image
        cv2.imwrite(output_path, stego_img)
        
    def decode(self, stego_image_path):
        # Load the stego image
        img = cv2.imread(stego_image_path)
        if img is None:
            raise ValueError("Could not read the stego image")
            
        # Get the blue channel for decoding
        blue = img[:,:,0]
        rows, cols = blue.shape
            
        # Apply DFT to blue channel
        blue_float = np.float32(blue)
        dft = cv2.dft(blue_float, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # Get magnitude and phase
        magnitude, phase = cv2.cartToPolar(dft_shift[:,:,0], dft_shift[:,:,1])
        
        # Extract message from magnitude - focusing on same mid-frequency components
        start_row, start_col = rows//4, cols//4
        
        # Extract message from magnitude
        binary_message = ""
        
        for i in range(start_row, 3*start_row):
            for j in range(start_col, 3*start_col):
                # Skip DC component
                if i == rows//2 and j == cols//2:
                    continue
                    
                # Extract bit using same even/odd approach
                bit = '1' if int(magnitude[i, j]) % 2 == 1 else '0'
                binary_message += bit
                
                # Check for terminator
                if len(binary_message) >= len(self.terminator) and binary_message[-len(self.terminator):] == self.terminator:
                    # Found terminator, remove it from message
                    binary_message = binary_message[:-len(self.terminator)]
                    
                    # Convert binary to text
                    text_message = ""
                    for k in range(0, len(binary_message), 8):
                        if k + 8 <= len(binary_message):
                            byte = binary_message[k:k+8]
                            try:
                                text_message += chr(int(byte, 2))
                            except:
                                pass  # Skip invalid characters
                    
                    # Clean the output - remove non-printable characters
                    cleaned_message = ""
                    for char in text_message:
                        if ord(char) >= 32 and ord(char) <= 126 or ord(char) in [9, 10, 13]:  # printable + whitespace
                            cleaned_message += char
                    
                    return cleaned_message
                
                # Avoid excessive searching
                if len(binary_message) > 8192:  # 1KB of bits is enough for most text messages
                    break
                    
            if len(binary_message) > 8192:
                break
                    
        # If we reached this point, terminator not found
        # Try recovering partial message anyway
        if len(binary_message) > 24:  # At least a few characters
            partial_message = ""
            for k in range(0, min(len(binary_message), 800), 8):  # Limit to 100 characters
                if k + 8 <= len(binary_message):
                    byte = binary_message[k:k+8]
                    try:
                        char = chr(int(byte, 2))
                        if ord(char) >= 32 and ord(char) <= 126 or ord(char) in [9, 10, 13]:
                            partial_message += char
                    except:
                        pass  # Skip invalid bytes
            
            return partial_message if partial_message else None
            
        return None
