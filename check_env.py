import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check if required folders exist
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

print(f"Template directory exists: {os.path.exists(template_dir)}")
print(f"Static directory exists: {os.path.exists(static_dir)}")

# Check pip packages
try:
    import pip
    print("\nInstalled packages:")
    for package in sorted(["%s==%s" % (i.key, i.version) for i in pip._vendor.pkg_resources.working_set]):
        print(f"  {package}")
except:
    print("Could not list installed packages")

# Try importing Flask
try:
    import flask
    print(f"\nFlask version: {flask.__version__}")
    print(f"Flask location: {flask.__file__}")
except Exception as e:
    print(f"\nError importing Flask: {e}")

# Try importing other required packages
packages = ['numpy', 'cv2', 'PIL', 'pywt']
for package in packages:
    try:
        exec(f"import {package}")
        print(f"{package} imported successfully")
    except Exception as e:
        print(f"Error importing {package}: {e}")

# Add test functions for debugging decode issues
def test_decode(stego_image_path, method='DCT', strength=10.0):
    """Test decoding on a specific image and method"""
    print(f"\nTesting decode with {method} method, strength={strength}...")
    
    try:
        if method == 'DCT':
            from dct_stego import DCTSteganography
            stego = DCTSteganography(quantization_factor=strength)
        elif method == 'Wavelet':
            from wavelet_stego import WaveletSteganography
            stego = WaveletSteganography(threshold=strength)
        elif method == 'DFT':
            from dft_stego import DFTSteganography
            stego = DFTSteganography(strength=strength)
        elif method == 'SVD':
            from svd_stego import SVDSteganography
            stego = SVDSteganography(strength=strength)
        else:  # LBP
            from lbp_stego import LBPSteganography
            stego = LBPSteganography(strength=strength)
        
        # Try to decode the image
        message = stego.decode(stego_image_path)
        
        print(f"Decoded message: {message if message else '(empty)'}")
        print(f"Message length: {len(message if message else '')}")
        print(f"First 50 characters: {message[:50] if message else ''}")
        
        # Check if message is valid
        if message:
            print("Message validity check: VALID (non-empty string)")
        else:
            print("Message validity check: INVALID (empty string)")
            
        # Check message binary
        if message:
            binary = ''.join(format(ord(c), '08b') for c in message[:5])
            print(f"First 5 chars binary: {binary}")
            
    except Exception as e:
        print(f"Error during decoding: {str(e)}")

# Add this at the bottom of the file
if __name__ == "__main__":
    import sys
    
    # Run basic environment checks
    print("Running basic environment checks...")
    
    # If an argument is provided, test decoding
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        method = sys.argv[2] if len(sys.argv) > 2 else 'DCT'
        strength = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
        
        print(f"\nTesting decode on: {test_path}")
        test_decode(test_path, method, strength)
