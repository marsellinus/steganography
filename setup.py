"""
Setup and environment verification script for the steganography application
"""
import os
import sys
import subprocess
import platform
import importlib
import importlib.util
import pkg_resources

def check_python_version():
    """Check if Python version is compatible"""
    python_version = sys.version_info
    minimum_version = (3, 7)
    
    print(f"Checking Python version: {platform.python_version()}")
    if python_version >= minimum_version:
        print("✓ Python version is compatible")
        return True
    else:
        print(f"✗ Python version {platform.python_version()} is not compatible. Required: 3.7+")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    required_packages = {
        'numpy': '1.19.0',
        'opencv-python': '4.5.0',
        'pillow': '8.0.0',
        'pywavelets': '1.1.1',
        'flask': '2.0.0',
        'matplotlib': '3.3.0',
        'scipy': '1.5.0',
        'scikit-image': '0.17.2'
    }
    
    missing_packages = []
    outdated_packages = []
    
    print("\nChecking required packages:")
    for package, min_version in required_packages.items():
        try:
            pkg = importlib.import_module(package.replace('-', '_'))
            if hasattr(pkg, '__version__'):
                version = pkg.__version__
            elif hasattr(pkg, 'version'):
                version = pkg.version
            else:
                try:
                    version = pkg_resources.get_distribution(package).version
                except:
                    version = "Unknown"
            
            print(f"  • {package}: {version}")
            
            # Check version
            if version != "Unknown":
                if pkg_resources.parse_version(version) < pkg_resources.parse_version(min_version):
                    outdated_packages.append((package, version, min_version))
        except ImportError:
            print(f"  • {package}: Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n✗ Missing packages:")
        for package in missing_packages:
            print(f"  - {package}")
    
    if outdated_packages:
        print("\n✗ Outdated packages:")
        for package, current, minimum in outdated_packages:
            print(f"  - {package}: {current} (required: {minimum}+)")
    
    if not missing_packages and not outdated_packages:
        print("\n✓ All required packages are installed with compatible versions")
        return True
    
    return False

def install_requirements():
    """Install packages from requirements.txt"""
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    
    if not os.path.exists(req_file):
        print("✗ requirements.txt not found")
        return False
    
    print("\nInstalling required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("✓ All packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("✗ Failed to install some packages")
        return False

def check_optional_modules():
    """Check optional modules that enhance functionality"""
    optional_modules = {
        'librosa': 'Audio processing',
        'soundfile': 'Audio I/O',
        'PySimpleGUI': 'GUI interface',
        'skimage': 'Image analysis'
    }
    
    print("\nChecking optional modules:")
    for module, description in optional_modules.items():
        if importlib.util.find_spec(module) is not None:
            print(f"  • {module}: Installed - {description}")
        else:
            print(f"  • {module}: Not installed - {description}")

def create_directories():
    """Create necessary directories for the application"""
    dirs = ["uploads", "outputs", "temp"]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\nCreating necessary directories:")
    for directory in dirs:
        dir_path = os.path.join(base_dir, directory)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
                print(f"  • Created: {directory}/")
            except Exception as e:
                print(f"  • Failed to create {directory}/: {str(e)}")
        else:
            print(f"  • Already exists: {directory}/")

def check_file_structure():
    """Check if all necessary files are present"""
    required_files = [
        "app.py", 
        "dct_stego.py", 
        "wavelet_stego.py", 
        "dft_stego.py", 
        "svd_stego.py", 
        "lbp_stego.py",
        "unicode_handler.py"
    ]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\nChecking file structure:")
    missing_files = []
    for file in required_files:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            print(f"  • {file}: Found")
        else:
            print(f"  • {file}: Not found")
            missing_files.append(file)
    
    if missing_files:
        print("\n✗ Some required files are missing. The application may not work correctly.")
        return False
    else:
        print("\n✓ All required files are present")
        return True

def run_basic_test():
    """Run a basic test to make sure everything works"""
    print("\nRunning basic functionality test...")
    
    try:
        # Test unicode handler
        import unicode_handler
        test_text = "Hello, Steganography!"
        binary = unicode_handler.text_to_binary_unicode(test_text)
        decoded = unicode_handler.binary_to_text_unicode(binary)
        
        if decoded == test_text:
            print(f"✓ Unicode handler test successful: '{test_text}' → binary → '{decoded}'")
        else:
            print(f"✗ Unicode handler test failed: Expected '{test_text}', got '{decoded}'")
            return False
        
        # Test importing all steganography classes
        from dct_stego import DCTSteganography
        from wavelet_stego import WaveletSteganography
        from dft_stego import DFTSteganography
        from svd_stego import SVDSteganography
        from lbp_stego import LBPSteganography
        
        print("✓ All steganography modules imported successfully")
        
        # Quick initialization test
        DCTSteganography()
        WaveletSteganography()
        DFTSteganography()
        SVDSteganography()
        LBPSteganography()
        
        print("✓ All steganography classes initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Basic test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Transform Domain Steganography Environment Setup ===\n")
    
    if not check_python_version():
        print("\nPlease install Python 3.7 or newer.")
        sys.exit(1)
    
    if "--install" in sys.argv:
        install_requirements()
    
    check_required_packages()
    check_optional_modules()
    create_directories()
    check_file_structure()
    
    if "--test" in sys.argv:
        run_basic_test()
    
    print("\nSetup complete. You can now run the application with 'python app.py'")
