"""
Diagnostic tool for debugging steganography algorithms
"""

import os
import cv2
import numpy as np
import time
import argparse
from dft_stego import DFTSteganography
from svd_stego import SVDSteganography
from lbp_stego import LBPSteganography
from dct_stego import DCTSteganography
from wavelet_stego import WaveletSteganography
from unicode_handler import debug_binary_analysis, text_to_binary_unicode, binary_to_text_unicode

def run_diagnostics(method_name, image_path, message, strength=10.0):
    """
    Run comprehensive diagnostics on a steganography method
    
    Args:
        method_name: 'DFT', 'SVD', 'LBP', 'DCT', or 'Wavelet'
        image_path: Path to cover image
        message: Secret message to encode
        strength: Embedding strength parameter
    """
    print(f"\n{'=' * 60}")
    print(f"DIAGNOSTIC TEST FOR {method_name} STEGANOGRAPHY")
    print(f"{'=' * 60}")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostics")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output paths
    timestamp = int(time.time())
    filename = os.path.basename(image_path)
    basename = os.path.splitext(filename)[0]
    
    stego_path = os.path.join(output_dir, f"{method_name}_{basename}_{timestamp}.png")
    
    # 1. Basic message analysis
    print("\n1. MESSAGE ANALYSIS:")
    print(f"   - Message length: {len(message)} characters")
    print(f"   - Message preview: '{message[:30]}...' (truncated)")
    
    # 2. Binary conversion check
    binary = text_to_binary_unicode(message)
    print("\n2. BINARY CONVERSION CHECK:")
    print(f"   - Binary length: {len(binary)} bits")
    print(f"   - Binary preview: {binary[:32]}... (truncated)")
    print(f"   - Byte count: {len(binary) // 8} bytes")
    
    # 3. Binary conversion round-trip test
    converted_back = binary_to_text_unicode(binary)
    conversion_success = message == converted_back
    print("\n3. ROUND-TRIP CONVERSION TEST:")
    print(f"   - Success: {'✓' if conversion_success else '✗'}")
    if not conversion_success:
        print(f"   - Original: '{message[:30]}...' (truncated)")
        print(f"   - Converted back: '{converted_back[:30]}...' (truncated)")
        
        # Calculate match percentage
        match_count = sum(1 for a, b in zip(message, converted_back) if a == b)
        match_percentage = (match_count / max(len(message), len(converted_back))) * 100
        print(f"   - Character match: {match_percentage:.1f}%")
    
    # 4. Image capacity analysis
    print("\n4. IMAGE CAPACITY ANALYSIS:")
    img = cv2.imread(image_path)
    if img is None:
        print("   - Error: Could not load image")
        return
    
    height, width = img.shape[:2]
    print(f"   - Image dimensions: {width}x{height} pixels")
    
    # Estimate capacity based on method
    if method_name == 'DCT':
        capacity_bits = (height // 8) * (width // 8)
        print(f"   - Estimated capacity: {capacity_bits} bits ({capacity_bits // 8} bytes)")
    elif method_name == 'DFT':
        rows, cols = height, width
        crow, ccol = rows // 2, cols // 2
        r_min = crow - rows // 8
        r_max = crow - rows // 16
        c_min = ccol - cols // 8
        c_max = ccol + cols // 8
        capacity_bits = (r_max - r_min) * (c_max - c_min)
        print(f"   - Estimated capacity: {capacity_bits} bits ({capacity_bits // 8} bytes)")
    elif method_name == 'SVD':
        capacity_bits = (height // 8) * (width // 8)
        print(f"   - Estimated capacity: {capacity_bits} bits ({capacity_bits // 8} bytes)")
    elif method_name == 'LBP':
        h_start = height // 8
        h_end = height - h_start
        w_start = width // 8
        w_end = width - w_start
        stride_y = 2
        stride_x = 4
        capacity_bits = ((h_end - h_start) // stride_y) * ((w_end - w_start) // stride_x)
        print(f"   - Estimated capacity: {capacity_bits} bits ({capacity_bits // 8} bytes)")
    elif method_name == 'Wavelet':
        capacity_bits = (height // 2) * (width // 2)  # Horizontal detail coefficients
        print(f"   - Estimated capacity: {capacity_bits} bits ({capacity_bits // 8} bytes)")
    
    # Check if message fits
    binary_length = len(binary) + 8  # Add terminator length
    if binary_length > capacity_bits:
        print(f"   - ⚠️ WARNING: Message too long! Needs {binary_length} bits, but capacity is {capacity_bits} bits")
    else:
        print(f"   - Message fits in image (uses {binary_length}/{capacity_bits} bits, {binary_length/capacity_bits*100:.1f}%)")
    
    # 5. Encoding test
    print("\n5. ENCODING TEST:")
    print(f"   - Method: {method_name}")
    print(f"   - Strength: {strength}")
    
    try:
        start_time = time.time()
        
        if method_name == 'DFT':
            stego = DFTSteganography(strength=strength)
            stego.encode(image_path, message, stego_path)
        elif method_name == 'SVD':
            stego = SVDSteganography(strength=strength)
            stego.encode(image_path, message, stego_path)
        elif method_name == 'LBP':
            stego = LBPSteganography(strength=strength)
            stego.encode(image_path, message, stego_path)
        elif method_name == 'DCT':
            stego = DCTSteganography(quantization_factor=strength)
            stego.encode(image_path, message, stego_path)
        elif method_name == 'Wavelet':
            stego = WaveletSteganography(threshold=strength)
            stego.encode(image_path, message, stego_path)
        
        encoding_time = time.time() - start_time
        print(f"   - Encoding completed in {encoding_time:.2f} seconds")
        print(f"   - Stego image saved to: {stego_path}")
        
        # Calculate image quality metrics
        print("\n6. IMAGE QUALITY METRICS:")
        try:
            psnr, mse = calculate_image_quality(image_path, stego_path)
            print(f"   - PSNR: {psnr:.2f} dB")
            print(f"   - MSE: {mse:.4f}")
        except Exception as e:
            print(f"   - Error calculating metrics: {str(e)}")
    except Exception as e:
        print(f"   - ❌ ERROR during encoding: {str(e)}")
        return
    
    # 7. Decoding test
    print("\n7. DECODING TEST:")
    try:
        start_time = time.time()
        
        if method_name == 'DFT':
            stego = DFTSteganography(strength=strength)
            decoded_message = stego.decode(stego_path)
        elif method_name == 'SVD':
            stego = SVDSteganography(strength=strength)
            decoded_message = stego.decode(stego_path)
        elif method_name == 'LBP':
            stego = LBPSteganography(strength=strength)
            decoded_message = stego.decode(stego_path)
        elif method_name == 'DCT':
            stego = DCTSteganography(quantization_factor=strength)
            decoded_message = stego.decode(stego_path)
        elif method_name == 'Wavelet':
            stego = WaveletSteganography(threshold=strength)
            decoded_message = stego.decode(stego_path)
        
        decoding_time = time.time() - start_time
        print(f"   - Decoding completed in {decoding_time:.2f} seconds")
        
        # Check if message was correctly decoded
        if decoded_message == message:
            print("   - ✓ SUCCESS: Message decoded correctly!")
        else:
            print("   - ⚠️ WARNING: Decoded message doesn't match original")
            print(f"   - Original (first 30 chars): '{message[:30]}...'")
            print(f"   - Decoded (first 30 chars): '{decoded_message[:30]}...'")
            
            # Calculate matching percentage
            common_length = min(len(message), len(decoded_message))
            if common_length > 0:
                matching_chars = sum(a == b for a, b in zip(message[:common_length], decoded_message[:common_length]))
                match_percentage = (matching_chars / common_length) * 100
                print(f"   - Character match: {match_percentage:.2f}%")
            
            # Print binary comparison for diagnostic
            print("\n8. BINARY ANALYSIS OF MISMATCHED RESULT:")
            original_binary = text_to_binary_unicode(message)
            decoded_binary = text_to_binary_unicode(decoded_message)
            
            min_len = min(len(original_binary), len(decoded_binary))
            error_count = 0
            first_error_pos = -1
            
            for i in range(min_len):
                if original_binary[i] != decoded_binary[i]:
                    if first_error_pos == -1:
                        first_error_pos = i
                    error_count += 1
            
            print(f"   - Binary errors: {error_count}/{min_len} bits ({error_count/min_len*100:.2f}%)")
            
            if first_error_pos != -1:
                context_start = max(0, first_error_pos - 8)
                context_end = min(min_len, first_error_pos + 8)
                
                print(f"   - First error at bit position {first_error_pos}:")
                print(f"     Original: {original_binary[context_start:context_end]}")
                print(f"     Decoded:  {decoded_binary[context_start:context_end]}")
                print(f"               {''.join([' ' for _ in range(first_error_pos-context_start)]) + '^'}")
    except Exception as e:
        print(f"   - ❌ ERROR during decoding: {str(e)}")
    
    print(f"\n{'=' * 60}")
    print(f"END OF DIAGNOSTIC TEST FOR {method_name}")
    print(f"{'=' * 60}")

def calculate_image_quality(original_path, stego_path):
    """Calculate PSNR and MSE between two images"""
    import math
    
    original = cv2.imread(original_path)
    stego = cv2.imread(stego_path)
    
    # Resize if dimensions don't match
    if original.shape != stego.shape:
        stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
    
    mse = np.mean((original - stego) ** 2)
    if mse == 0:  # Images are identical
        psnr = float('inf')
    else:
        # Calculate PSNR
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        
    return psnr, mse

def try_multiple_strengths(method_name, image_path, message, start=5.0, end=50.0, steps=5):
    """Try different strength values to find optimal settings"""
    print(f"\nTesting {method_name} with different strength values:")
    
    strength_values = np.linspace(start, end, steps)
    results = []
    
    for strength in strength_values:
        print(f"\n--- Testing strength = {strength:.1f} ---")
        try:
            # Create output directory
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostics")
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output paths
            timestamp = int(time.time())
            basename = os.path.splitext(os.path.basename(image_path))[0]
            stego_path = os.path.join(output_dir, f"{method_name}_{basename}_s{strength:.1f}_{timestamp}.png")
            
            # Encode
            if method_name == 'DFT':
                stego = DFTSteganography(strength=strength)
            elif method_name == 'SVD':
                stego = SVDSteganography(strength=strength)
            elif method_name == 'LBP':
                stego = LBPSteganography(strength=strength)
            elif method_name == 'DCT':
                stego = DCTSteganography(quantization_factor=strength)
            else:  # Wavelet
                stego = WaveletSteganography(threshold=strength)
            
            stego.encode(image_path, message, stego_path)
            
            # Calculate quality
            psnr, mse = calculate_image_quality(image_path, stego_path)
            
            # Decode
            decoded_message = stego.decode(stego_path)
            success = (decoded_message == message)
            
            # Calculate match percentage if not exact match
            if not success:
                common_length = min(len(message), len(decoded_message))
                if common_length > 0:
                    matching_chars = sum(a == b for a, b in zip(message[:common_length], decoded_message[:common_length]))
                    match_percentage = (matching_chars / common_length) * 100
                else:
                    match_percentage = 0
            else:
                match_percentage = 100
            
            results.append({
                'strength': strength,
                'success': success,
                'match_percentage': match_percentage,
                'psnr': psnr,
                'mse': mse,
                'stego_path': stego_path
            })
            
            print(f"Strength: {strength:.1f}, Success: {'✓' if success else '✗'}, " +
                  f"Match: {match_percentage:.1f}%, PSNR: {psnr:.2f} dB")
            
        except Exception as e:
            print(f"Error at strength {strength:.1f}: {str(e)}")
    
    # Print summary
    print("\n--- RESULTS SUMMARY ---")
    print(f"{'Strength':<10} {'Success':<10} {'Match %':<10} {'PSNR (dB)':<10}")
    print("-" * 40)
    
    for result in results:
        success_mark = '✓' if result['success'] else '✗'
        print(f"{result['strength']:<10.1f} {success_mark:<10} {result['match_percentage']:<10.1f} {result['psnr']:<10.2f}")
    
    # Find optimal strength
    successful_results = [r for r in results if r['success']]
    if successful_results:
        # Sort by PSNR (higher is better)
        optimal = sorted(successful_results, key=lambda x: x['psnr'], reverse=True)[0]
        print(f"\nOptimal strength: {optimal['strength']:.1f} (PSNR: {optimal['psnr']:.2f} dB)")
    else:
        # Find best match percentage if no perfect matches
        best_match = sorted(results, key=lambda x: x['match_percentage'], reverse=True)[0]
        print(f"\nNo perfect matches found. Best match at strength {best_match['strength']:.1f}" +
              f" with {best_match['match_percentage']:.1f}% character match")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Steganography Diagnostic Tool")
    parser.add_argument("--method", "-m", choices=['DFT', 'SVD', 'LBP', 'DCT', 'Wavelet'], 
                        default='DFT', help="Steganography method")
    parser.add_argument("--image", "-i", required=True, help="Path to cover image")
    parser.add_argument("--message", "-t", default="This is a test message for steganography!",
                        help="Secret message to encode")
    parser.add_argument("--strength", "-s", type=float, default=10.0,
                        help="Embedding strength parameter")
    parser.add_argument("--find-optimal", "-o", action="store_true",
                        help="Find optimal strength parameter")
    
    args = parser.parse_args()
    
    if args.find_optimal:
        try_multiple_strengths(args.method, args.image, args.message)
    else:
        run_diagnostics(args.method, args.image, args.message, args.strength)
