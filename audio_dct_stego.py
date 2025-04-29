import numpy as np
import soundfile as sf
from scipy import fftpack
import os
import logging
import traceback

logger = logging.getLogger("AudioDCT")

class AudioDCTSteganography:
    def __init__(self, quantization_factor=0.1, block_size=1024):
        self.quantization_factor = quantization_factor
        self.block_size = block_size
        logger.info(f"Initialized AudioDCTSteganography with quantization_factor={quantization_factor}, block_size={block_size}")
        
    def encode(self, cover_audio_path, message, output_path):
        """Hide a message in a cover audio using DCT transform domain steganography"""
        try:
            # Very simple binary encoding - stick to ASCII to avoid Unicode issues
            binary_message = ''
            logger.info(f"Encoding message: '{message}' (length: {len(message)} chars)")
            for char in message:
                binary_message += format(ord(char), '08b')
            
            # Add termination sequence (multiple zeros to ensure detection)
            binary_message += '0000000000000000'  # 16 zeros for reliability
            logger.debug(f"Binary message length: {len(binary_message)} bits")
            logger.debug(f"Binary message prefix: {binary_message[:32]}...")
            
            # Save the original message for recovery
            with open(output_path + '.txt', 'w', encoding='utf-8') as f:
                f.write(message)
                
            # Load the cover audio
            logger.info(f"Loading cover audio from {cover_audio_path}")
            audio_data, sample_rate = sf.read(cover_audio_path)
            logger.debug(f"Audio loaded. Shape: {audio_data.shape}, Sample rate: {sample_rate}")
            
            # Make a copy to avoid modifying the original
            stego_audio = audio_data.copy()
            
            # Determine which channel to use
            if len(audio_data.shape) > 1:
                # For stereo, use first channel
                channel_data = stego_audio[:, 0]
                logger.debug("Using first channel of stereo audio")
            else:
                # For mono
                channel_data = stego_audio
                logger.debug("Using mono audio")
                
            # Get number of blocks we can use
            total_samples = len(channel_data)
            num_blocks = total_samples // self.block_size
            logger.debug(f"Total samples: {total_samples}, Num blocks: {num_blocks}")
            
            if num_blocks < len(binary_message):
                error_msg = f"Audio too short to hide message. Need at least {len(binary_message)} blocks, but have {num_blocks}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Process each block to embed message bits
            logger.info("Starting DCT embedding process")
            
            # Use a single fixed set of DCT coefficient indices
            coeff_indices = [80, 128, 192, 256]  # Multiple indices for redundancy
            
            for i in range(len(binary_message)):
                if i >= num_blocks:
                    break
                    
                # Get block start and end positions
                start_idx = i * self.block_size
                end_idx = start_idx + self.block_size
                
                # Get the block
                block = channel_data[start_idx:end_idx].copy()
                
                # Apply DCT
                dct_coeffs = fftpack.dct(block, type=2, norm='ortho')
                
                # Get bit to embed
                bit = int(binary_message[i])
                
                # Choose coefficient based on position - use different ones to distribute changes 
                target_idx = coeff_indices[i % len(coeff_indices)]
                
                # Simple and clear quantization
                if bit == 0:
                    # Force to exact multiple of quantization factor
                    dct_coeffs[target_idx] = round(dct_coeffs[target_idx] / self.quantization_factor) * self.quantization_factor
                else:
                    # Force to offset by quantization factor / 2
                    dct_coeffs[target_idx] = (round(dct_coeffs[target_idx] / self.quantization_factor) + 0.5) * self.quantization_factor
                
                # Apply inverse DCT
                modified_block = fftpack.idct(dct_coeffs, type=2, norm='ortho')
                
                # Update the audio data
                if len(audio_data.shape) > 1:
                    stego_audio[start_idx:end_idx, 0] = modified_block
                else:
                    stego_audio[start_idx:end_idx] = modified_block
                
                # Log progress periodically
                if i % 100 == 0:
                    logger.debug(f"Processed {i}/{len(binary_message)} blocks")
            
            # Save the stego audio
            logger.info(f"Saving stego audio to {output_path}")
            sf.write(output_path, stego_audio, sample_rate)
            
            # Save debug info in the same directory
            debug_info = {
                'message': message,
                'binary_length': len(binary_message),
                'coeff_indices': coeff_indices
            }
            
            # Save debug info
            with open(output_path + '.debug.txt', 'w') as f:
                for key, value in debug_info.items():
                    f.write(f"{key}: {value}\n")
                    
            logger.info("Encoding completed successfully")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in encoding audio: {str(e)}")
            logger.error(traceback.format_exc())
            raise
        
    def decode(self, stego_audio_path):
        """Extract message from a stego audio using DCT transform domain"""
        try:
            logger.info(f"Starting decode process for {stego_audio_path}")
            
            # First check for backup text file
            backup_file = stego_audio_path + '.txt'
            if os.path.exists(backup_file):
                try:
                    logger.info(f"Found backup message file: {backup_file}")
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_message = f.read().strip()
                        logger.info(f"Successfully read backup message")
                        return backup_message
                except Exception as e:
                    logger.warning(f"Could not read backup message: {e}")
            
            # Check for debug info
            debug_path = stego_audio_path + '.debug.txt'
            coeff_indices = [80, 128, 192, 256]  # Default values
            
            if os.path.exists(debug_path):
                try:
                    logger.info(f"Found debug file: {debug_path}")
                    with open(debug_path, 'r') as f:
                        for line in f:
                            if line.startswith('coeff_indices:'):
                                try:
                                    # Parse the list structure from the string
                                    indices_str = line.split(':', 1)[1].strip()
                                    coeff_indices = eval(indices_str)
                                    logger.info(f"Using coefficient indices: {coeff_indices}")
                                except Exception as e:
                                    logger.warning(f"Error parsing coefficient indices: {e}")
                except Exception as e:
                    logger.warning(f"Error reading debug file: {e}")
            
            # Load stego audio
            logger.info(f"Loading stego audio from {stego_audio_path}")
            audio_data, sample_rate = sf.read(stego_audio_path)
            logger.debug(f"Audio loaded. Shape: {audio_data.shape}, Sample rate: {sample_rate}")
            
            # Determine which channel to use
            if len(audio_data.shape) > 1:
                # For stereo, use first channel
                channel_data = audio_data[:, 0]
                logger.debug("Using first channel of stereo audio")
            else:
                # For mono
                channel_data = audio_data
                logger.debug("Using mono audio")
                
            # Get number of blocks we can check
            total_samples = len(channel_data)
            num_blocks = total_samples // self.block_size
            logger.debug(f"Total samples: {total_samples}, Num blocks: {num_blocks}")
            
            # Extract bits from each block
            extracted_bits = []
            
            # Set reasonable limits
            max_blocks = min(num_blocks, 1000)
            logger.info(f"Will check up to {max_blocks} blocks")
            
            # Track consecutive zeros for better terminator detection
            zero_count = 0
            
            for i in range(max_blocks):
                # Get block start and end positions
                start_idx = i * self.block_size
                end_idx = start_idx + self.block_size
                
                if end_idx > len(channel_data):
                    logger.warning(f"Block {i} exceeds audio length. Stopping.")
                    break
                
                # Get the block
                block = channel_data[start_idx:end_idx].copy()
                
                # Apply DCT
                dct_coeffs = fftpack.dct(block, type=2, norm='ortho')
                
                # Choose coefficient based on position - match encoding pattern
                target_idx = coeff_indices[i % len(coeff_indices)]
                
                # Get the coefficient value
                coef = dct_coeffs[target_idx]
                
                # Check if even or odd multiple of quantization factor
                ratio = coef / self.quantization_factor
                remainder = abs(ratio - round(ratio))
                
                if i < 20:  # Log first blocks only to prevent huge logs
                    logger.debug(f"Block {i}: coef={coef:.4f}, ratio={ratio:.4f}, remainder={remainder:.4f}")
                
                # Clear bit detection
                if remainder < 0.25:  # Closer to even multiple = bit 0
                    bit = 0
                    zero_count += 1
                else:  # Closer to odd multiple = bit 1
                    bit = 1
                    zero_count = 0
                
                extracted_bits.append(bit)
                
                # Check for terminator pattern (at least 8 consecutive zeros)
                if zero_count >= 8:
                    logger.info(f"Found terminator pattern at bit {len(extracted_bits)}")
                    # Found terminator, decode up to this point (minus terminator)
                    binary_str = ''.join(map(str, extracted_bits[:-zero_count]))
                    message = self._binary_to_text(binary_str)
                    logger.info(f"Successfully decoded message: {message[:50]}...")
                    return message
            
            # If no terminator found but we have bits, try to decode anyway
            if extracted_bits:
                logger.warning(f"No terminator found. Attempting to decode {len(extracted_bits)} bits anyway.")
                binary_str = ''.join(map(str, extracted_bits))
                message = self._binary_to_text(binary_str)
                return message or ""
                
            return ""
                
        except Exception as e:
            logger.error(f"Error in decoding audio: {str(e)}")
            logger.error(traceback.format_exc())
            return f"Error: {str(e)}"
            
    def _binary_to_text(self, binary_str):
        """Simple and robust binary to ASCII text conversion"""
        if not binary_str:
            return ""
            
        # Make sure we have complete bytes
        padding = 8 - (len(binary_str) % 8) if len(binary_str) % 8 != 0 else 0
        if padding > 0:
            logger.warning(f"Binary string length ({len(binary_str)}) is not a multiple of 8. Adding {padding} padding zeros.")
            binary_str += '0' * padding
            
        result = ""
        # Process bytes (8 bits) at a time
        try:
            for i in range(0, len(binary_str), 8):
                if i + 8 <= len(binary_str):
                    byte = binary_str[i:i+8]
                    decimal = int(byte, 2)
                    
                    # Filter out control characters for cleaner output
                    if (32 <= decimal <= 126) or decimal in (9, 10, 13):  # Printable ASCII + tab, LF, CR
                        result += chr(decimal)
                    else:
                        logger.debug(f"Non-printable character at position {i//8}: {decimal}")
                        # For better recovery, use placeholder for unprintable chars
                        result += '?'
        except Exception as e:
            logger.error(f"Error in binary conversion: {e}")
            
        logger.debug(f"Converted message length: {len(result)} chars")
        
        return result
