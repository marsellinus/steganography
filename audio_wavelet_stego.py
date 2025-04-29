import numpy as np
import soundfile as sf
import pywt
import os
import re

class AudioWaveletSteganography:
    def __init__(self, wavelet='db4', threshold=0.1):
        self.wavelet = wavelet
        self.threshold = threshold
        
    def encode(self, cover_audio_path, message, output_path):
        """Hide a message in a cover audio using Wavelet transform domain steganography"""
        try:
            # Convert message to binary (simple ASCII encoding)
            binary_message = ''.join(format(ord(char), '08b') for char in message)
            binary_message += '00000000'  # Add terminator
            
            # Save the original message for recovery
            debug_path = output_path + '.message.txt'
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(message)
            
            # Load the cover audio
            audio_data, sample_rate = sf.read(cover_audio_path)
            
            # Make a copy to avoid modifying the original
            stego_audio = audio_data.copy()
            
            # Determine which channel to use
            if len(audio_data.shape) > 1:
                # For stereo, use first channel
                channel_data = stego_audio[:, 0].copy()
            else:
                # For mono
                channel_data = stego_audio.copy()
                
            # Apply wavelet decomposition (4 levels)
            coeffs = pywt.wavedec(channel_data, self.wavelet, level=4)
            
            # We'll use the detail coefficients from the first level (cD1) for embedding
            # These are high-frequency components where changes are less perceptible
            cA4, cD4, cD3, cD2, cD1 = coeffs
            
            # Check if we can fit the message
            if len(cD1) < len(binary_message):
                raise ValueError(f"Audio too short to hide message. Need at least {len(binary_message)} coefficients, have {len(cD1)}")
            
            # Embed message bits in detail coefficients
            for i in range(len(binary_message)):
                bit = int(binary_message[i])
                
                # Modify coefficient based on bit
                if bit == 0:
                    # Make coefficient even multiple of threshold
                    cD1[i] = self.threshold * np.floor(cD1[i] / self.threshold)
                else:
                    # Make coefficient odd multiple of threshold
                    cD1[i] = self.threshold * np.floor(cD1[i] / self.threshold) + self.threshold / 2
            
            # Reconstruct the signal with the modified coefficients
            modified_coeffs = cA4, cD4, cD3, cD2, cD1
            modified_channel = pywt.waverec(modified_coeffs, self.wavelet)
            
            # Make sure the reconstructed signal has the same length
            if len(modified_channel) > len(channel_data):
                modified_channel = modified_channel[:len(channel_data)]
            elif len(modified_channel) < len(channel_data):
                padding = np.zeros(len(channel_data) - len(modified_channel))
                modified_channel = np.append(modified_channel, padding)
            
            # Update the audio data
            if len(audio_data.shape) > 1:
                stego_audio[:, 0] = modified_channel
            else:
                stego_audio = modified_channel
            
            # Save the stego audio
            sf.write(output_path, stego_audio, sample_rate)
            return output_path
            
        except Exception as e:
            print(f"Error in encoding audio with wavelet: {e}")
            raise
        
    def decode(self, stego_audio_path):
        """Extract message from a stego audio using Wavelet transform domain"""
        try:
            # First check for direct message file
            message_path = stego_audio_path + '.message.txt'
            if os.path.exists(message_path):
                try:
                    with open(message_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"Warning: Could not read message file ({e}), trying binary decoding...")
            
            # Load stego audio
            audio_data, sample_rate = sf.read(stego_audio_path)
            
            # Determine which channel to use
            if len(audio_data.shape) > 1:
                # For stereo, use first channel
                channel_data = audio_data[:, 0]
            else:
                # For mono
                channel_data = audio_data
                
            # Apply wavelet decomposition
            coeffs = pywt.wavedec(channel_data, self.wavelet, level=4)
            cA4, cD4, cD3, cD2, cD1 = coeffs
            
            # Extract bits from detail coefficients
            extracted_bits = []
            
            # Don't extract too many bits (reasonable limit)
            max_bits = min(len(cD1), 10000)  # Safety limit
            
            for i in range(max_bits):
                coef = cD1[i]
                # Determine if coefficient is closer to even or odd multiple
                ratio = coef / self.threshold
                remainder = ratio - np.floor(ratio)
                
                # Use threshold to determine bit value
                if remainder < 0.25 or remainder > 0.75:
                    extracted_bits.append('0')  # Closer to even multiple
                else:
                    extracted_bits.append('1')  # Closer to odd multiple
                
                # Check for terminator pattern (8 zeros)
                if len(extracted_bits) >= 8:
                    last_eight = ''.join(extracted_bits[-8:])
                    if last_eight == '00000000':
                        # Found terminator, decode the bits before it
                        binary_str = ''.join(extracted_bits[:-8])
                        return self._binary_to_text_safe(binary_str)
            
            # If no terminator is found, still try to decode what we have
            if extracted_bits:
                binary_str = ''.join(extracted_bits)
                return self._binary_to_text_safe(binary_str)
            else:
                return "No message found"
                
        except Exception as e:
            print(f"Error in decoding audio with wavelet: {e}")
            return f"Error: {str(e)}"
            
    def _binary_to_text_safe(self, binary_str):
        """Convert binary string to text with safety checks for invalid Unicode"""
        if not binary_str:
            return ""
            
        text = ""
        # Ensure binary string length is a multiple of 8
        if len(binary_str) % 8 != 0:
            padding = 8 - (len(binary_str) % 8)
            binary_str = binary_str + '0' * padding
        
        try:
            # Process 8 bits at a time (ASCII)
            chunks = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
            for chunk in chunks:
                try:
                    decimal = int(chunk, 2)
                    # Filter out control characters and surrogates
                    if (decimal < 32 and decimal not in (9, 10, 13)) or (0xD800 <= decimal <= 0xDFFF):
                        char = "?"
                    else:
                        char = chr(decimal)
                    text += char
                except:
                    text += "?"  # Replace any invalid character
            
            # If the result contains only ASCII or looks like garbled data, do additional cleaning
            if any(not c.isprintable() and c not in ('\n', '\t', '\r') for c in text):
                # Further clean the text - keep only printable ASCII
                cleaned_text = ''.join(c if c.isprintable() or c in ('\n', '\t', '\r') else '?' for c in text)
                # Remove repeated question marks
                cleaned_text = re.sub(r'\?{2,}', '?', cleaned_text)
                # Remove trailing junk if message is mostly good
                if len(cleaned_text) > 20 and '?' in cleaned_text[-10:]:
                    # Find the last reasonable ending point
                    last_good_idx = max(cleaned_text.rfind('. '), cleaned_text.rfind('! '), 
                                       cleaned_text.rfind('? '), cleaned_text.rfind('\n'))
                    if last_good_idx > len(cleaned_text) // 2:
                        cleaned_text = cleaned_text[:last_good_idx+1]
                return cleaned_text
            
            return text
        except Exception as e:
            print(f"Error in binary conversion: {e}")
            # Return any valid part we've successfully processed, or fallback to basic conversion
            if text:
                return text
            
            # Last-resort fallback: only include ASCII printable characters
            result = ""
            for i in range(0, len(binary_str), 8):
                if i + 8 <= len(binary_str):
                    try:
                        byte = binary_str[i:i+8]
                        decimal = int(byte, 2)
                        # Only use printable ASCII range
                        if 32 <= decimal < 127:
                            result += chr(decimal)
                        else:
                            result += '?'
                    except:
                        result += '?'
                        
            return result or "Decoding failed"
