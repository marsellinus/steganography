import numpy as np
import soundfile as sf
import pywt

class AudioWaveletSteganography:
    """Wavelet-based audio steganography implementation"""
    
    def __init__(self, wavelet='db4', level=2, threshold=0.05):
        self.wavelet = wavelet
        self.level = level
        self.threshold = threshold
        
    def encode(self, audio_path, message, output_path):
        """
        Hide a message in an audio file using wavelet transform domain steganography
        
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
        
        # Apply wavelet decomposition
        coeffs = pywt.wavedec(audio_channel, self.wavelet, level=self.level)
        
        # We'll embed in the detail coefficients of the first level
        # (which represents high frequency content and is less audible)
        cD1 = coeffs[-1]
        
        # Check if message can fit
        if len(binary_message) > len(cD1) // 4:  # Using every 4th coefficient
            raise ValueError(f"Message too long! Max {len(cD1) // 4} bits, got {len(binary_message)}")
        
        # Embed message in the detail coefficients
        message_index = 0
        
        for i in range(0, len(cD1), 4):  # Use every 4th coefficient
            if message_index >= len(binary_message):
                break
                
            bit = int(binary_message[message_index])
            
            # Modify coefficient based on bit
            if bit == 0:
                # Make coefficient even multiple of threshold
                cD1[i] = self.threshold * round(cD1[i] / self.threshold)
            else:
                # Make coefficient odd multiple of threshold
                cD1[i] = self.threshold * (round(cD1[i] / self.threshold - 0.5) + 0.5)
            
            message_index += 1
        
        # Update the coefficients
        coeffs[-1] = cD1
        
        # Reconstruct the modified audio
        modified_channel = pywt.waverec(coeffs, self.wavelet)
        
        # Handle potential length mismatch due to wavelet transform
        if len(modified_channel) > len(audio_channel):
            modified_channel = modified_channel[:len(audio_channel)]
        elif len(modified_channel) < len(audio_channel):
            padding = np.zeros(len(audio_channel) - len(modified_channel))
            modified_channel = np.concatenate((modified_channel, padding))
        
        # Create stego audio
        if len(audio.shape) > 1:  # If stereo
            stego_audio = audio.copy()
            stego_audio[:, 0] = modified_channel
        else:  # If mono
            stego_audio = modified_channel
            
        # Save the stego audio
        sf.write(output_path, stego_audio, sample_rate)
        
        return output_path
    
    def decode(self, stego_audio_path):
        """
        Extract hidden message from a stego audio using wavelet transform domain
        
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
            
        # Apply wavelet decomposition
        coeffs = pywt.wavedec(audio_channel, self.wavelet, level=self.level)
        
        # Extract from the same detail coefficients
        cD1 = coeffs[-1]
        
        # Extract bits
        extracted_bits = []
        
        for i in range(0, len(cD1), 4):  # Same step as encoding
            # Check if coefficient is even or odd multiple of threshold
            coef = cD1[i]
            remainder = abs((coef / self.threshold) % 1.0)
            
            if remainder > 0.25 and remainder < 0.75:  # Near half step
                extracted_bits.append(1)
            else:
                extracted_bits.append(0)
            
            # Check for terminator sequence
            if len(extracted_bits) >= 8 and extracted_bits[-8:] == [0, 0, 0, 0, 0, 0, 0, 0]:
                # Found terminator, remove it and stop
                return self._bits_to_message(extracted_bits[:-8])
            
            # Limit extraction to avoid excessive processing
            if len(extracted_bits) > 10000:
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
