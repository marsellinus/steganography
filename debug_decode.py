"""
Debug script for testing steganography decoding with different parameters
"""
import sys
import os
import numpy as np
import cv2

def test_dct_decode(image_path, strength_values=None):
    """Test DCT decoding with multiple strength values"""
    from dct_stego import DCTSteganography
    
    if strength_values is None:
        strength_values = [5, 8, 10, 12, 15, 20, 25, 30]
    
    print(f"Testing DCT decode on: {image_path}")
    print("-" * 50)
    
    for strength in strength_values:
        try:
            stego = DCTSteganography(quantization_factor=strength)
            message = stego.decode(image_path)
            
            print(f"Strength {strength}:")
            if message:
                if len(message) > 50:
                    print(f"  Message: {message[:50]}... ({len(message)} chars)")
                else:
                    print(f"  Message: {message} ({len(message)} chars)")
            else:
                print("  No message found")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print("-" * 50)

def test_wavelet_decode(image_path, strength_values=None):
    """Test Wavelet decoding with multiple strength values"""
    from wavelet_stego import WaveletSteganography
    
    if strength_values is None:
        strength_values = [5, 8, 10, 15, 20, 25, 30, 40]
    
    print(f"Testing Wavelet decode on: {image_path}")
    print("-" * 50)
    
    for strength in strength_values:
        try:
            stego = WaveletSteganography(threshold=strength)
            message = stego.decode(image_path)
            
            print(f"Strength {strength}:")
            if message:
                if len(message) > 50:
                    print(f"  Message: {message[:50]}... ({len(message)} chars)")
                else:
                    print(f"  Message: {message} ({len(message)} chars)")
            else:
                print("  No message found")
        except Exception as e:
            print(f"  Error: {str(e)}")
    
    print("-" * 50)

def analyze_image(image_path):
    """Analyze basic properties of the image"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Could not load image: {image_path}")
            return
        
        height, width, channels = img.shape
        
        print(f"Image dimensions: {width} x {height}, {channels} channels")
        print(f"File size: {os.path.getsize(image_path) / 1024:.1f} KB")
        
        # Calculate histogram
        hist_b = cv2.calcHist([img], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([img], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([img], [2], None, [256], [0, 256])
        
        # Check if histograms look unusual
        b_std = np.std(hist_b)
        g_std = np.std(hist_g)
        r_std = np.std(hist_r)
        
        print(f"Channel histogram standard deviations: R={r_std:.2f}, G={g_std:.2f}, B={b_std:.2f}")
        
        # Calculate entropy (measure of randomness)
        entropy = []
        for i in range(channels):
            entropy.append(cv2.calcHist([img], [i], None, [256], [0, 256]))
        
        print("Image seems valid for steganography analysis.")
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_decode.py <image_path> [method] [min_strength] [max_strength] [step]")
        print("Methods: dct, wavelet, dft, svd, lbp, all")
        sys.exit(1)
    
    image_path = sys.argv[1]
    method = sys.argv[2].lower() if len(sys.argv) > 2 else "all"
    
    # Optional strength range
    min_strength = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    max_strength = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
    step = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
    
    # Generate strength values
    strength_values = [min_strength + i*step for i in range(int((max_strength - min_strength) / step) + 1)]
    
    # Analyze the image first
    analyze_image(image_path)
    print("\n")
    
    # Run tests based on method
    if method in ["dct", "all"]:
        test_dct_decode(image_path, strength_values)
        
    if method in ["wavelet", "all"]:
        test_wavelet_decode(image_path, strength_values)
    
    # Add more methods as needed
