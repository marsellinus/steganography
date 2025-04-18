import numpy as np
import soundfile as sf
import math
from scipy.fftpack import dct, idct

class AudioDCTSteganography:
    """DCT-based audio steganography implementation"""
    
    def __init__(self, block_size=1024, quantization_factor=0.1):
        self.block_size = block_size
        self.quantization_factor = quantization_factor
        
    def encode(self, audio_path, message, output_path):
        """
        Hide a message in an audio file using DCT transform domain steganography
        
        Args:
            audio_path: Path to the cover audio file
            message: Secret message to hide
            output_path: Where to save the resulting stego audio
        """
        # Convert message to binary
        binary_message = ''.join(format(ord(c), '08b') for c in message)
        binary_message += '00000000'  # Add terminator
        
        # Load the audio file
        audio, sample_rate = sf.read(audio_path)
        
        # Handle stereo audio by using only the first channel
        if len(audio.shape) > 1:
            audio_channel = audio[:, 0].copy()
        else:
            audio_channel = audio.copy()
        
        # Calculate how many blocks we need
        total_samples = len(audio_channel)
        total_blocks = total_samples // self.block_size
        
        # Check if message can fit
        if len(binary_message) > total_blocks:
            raise ValueError(f"Message too long! Max {total_blocks} bits, got {len(binary_message)}")
        
        # Process each audio block
        message_index = 0
        for block_idx in range(total_blocks):
            if message_index >= len(binary_message):
                break
                
            # Extract the current block
            start_idx = block_idx * self.block_size
            end_idx = start_idx + self.block_size
            block = audio_channel[start_idx:end_idx]
            
            # Apply DCT to the block
            dct_block = dct(block, type=2, norm='ortho')
            
            # Get the current bit to embed
            bit = int(binary_message[message_index])
            
            # Modify a mid-frequency coefficient to hide 1 bit
            # We choose a mid-frequency region to balance robustness and imperceptibility
            coef_idx = self.block_size // 8  # Select a mid-frequency coefficient
            
            if bit == 0:
                # Make coefficient even multiple of quantization factor
                dct_block[coef_idx] = self.quantization_factor * round(dct_block[coef_idx] / self.quantization_factor)
            else:
                # Make coefficient odd multiple of quantization factor
                dct_block[coef_idx] = self.quantization_factor * (round(dct_block[coef_idx] / self.quantization_factor - 0.5) + 0.5)
            
            # Apply inverse DCT
            modified_block = idct(dct_block, type=2, norm='ortho')
            
            # Update the audio channel with the modified block
            audio_channel[start_idx:end_idx] = modified_block
            
            message_index += 1
        
        # Create stego audio
        if len(audio.shape) > 1:  # If stereo
            stego_audio = audio.copy()
            stego_audio[:, 0] = audio_channel
        else:  # If mono
            stego_audio = audio_channel
            
        # Save the stego audio
        sf.write(output_path, stego_audio, sample_rate)
        
        return output_path
    
    def decode(self, stego_audio_path):
        """
        Extract hidden message from a stego audio using DCT transform domain
        
        Args:
            stego_audio_path: Path to the stego audio
            
        Returns:
            Extracted message as a string
        """
        # Load the stego audio file
        stego_audio, sample_rate = sf.read(stego_audio_path)
        
        # Handle stereo audio by using only the first channel
        if len(stego_audio.shape) > 1:
            audio_channel = stego_audio[:, 0]
        else:
            audio_channel = stego_audio
            
        # Calculate total blocks
        total_samples = len(audio_channel)
        total_blocks = total_samples // self.block_size
        
        # Extract bits from each block
        extracted_bits = []
        
        for block_idx in range(total_blocks):
            # Extract the current block
            start_idx = block_idx * self.block_size
            end_idx = start_idx + self.block_size
            block = audio_channel[start_idx:end_idx]
            
            # Apply DCT to the block
            dct_block = dct(block, type=2, norm='ortho')
            
            # Extract bit from the mid-frequency coefficient
            coef_idx = self.block_size // 8
            coef_val = dct_block[coef_idx]
            
            # Check if coefficient is even or odd multiple of quantization factor
            remainder = abs((coef_val / self.quantization_factor) % 1.0)
            
            # Use a threshold to determine if it's even or odd
            if remainder > 0.25 and remainder < 0.75:
                extracted_bits.append(1)
            else:
                extracted_bits.append(0)
            
            # Check for terminator sequence
            if len(extracted_bits) >= 8 and extracted_bits[-8:] == [0, 0, 0, 0, 0, 0, 0, 0]:
                # Found terminator, remove it and stop
                return self._bits_to_message(extracted_bits[:-8])
            
            # Limit the message size we try to extract
            if len(extracted_bits) > 10000:  # Arbitrary limit to avoid processing huge files
                break
        
        # If no terminator found, try to convert what we have
        return self._bits_to_message(extracted_bits)
    
    def _bits_to_message(self, bits):
        """Convert a sequence of bits to a string message"""
        if not bits:
            return ""
            
        # Ensure we have a multiple of 8 bits
        while len(bits) % 8 != 0:
            bits.append(0)
            
        # Convert each byte to a character
        message = ""
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = bits[i:i+8]
                try:
                    char_code = int(''.join(map(str, byte)), 2)
                    # Only accept printable ASCII and common control characters
                    if 32 <= char_code <= 126 or char_code in [9, 10, 13]:
                        message += chr(char_code)
                    else:
                        # Use placeholder for non-printable characters
                        message += "�"
                except:
                    break
        
        return message
