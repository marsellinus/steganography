"""
Configuration and parameter management for steganography methods
"""
import os
import json

# Default configuration parameters for each steganography method
DEFAULT_CONFIG = {
    "DCT": {
        "block_size": 8,
        "quantization_factor": 10,
        "target_coefficient": [4, 5],  # [row, col] in DCT block
        "min_strength": 1,
        "max_strength": 50,
        "recommended_strength": 10
    },
    "Wavelet": {
        "wavelet": "haar",
        "level": 1,
        "threshold": 30,
        "target_subband": "cH",  # Horizontal detail coefficients
        "min_strength": 5,
        "max_strength": 100,
        "recommended_strength": 30
    },
    "DFT": {
        "strength": 10,
        "min_strength": 1, 
        "max_strength": 50,
        "recommended_strength": 10,
        "frequency_range": "mid"  # Options: low, mid, high
    },
    "SVD": {
        "block_size": 8,
        "strength": 10,
        "min_strength": 1,
        "max_strength": 50,
        "recommended_strength": 10,
        "target_value": 0  # Index of singular value to modify
    },
    "LBP": {
        "radius": 3,
        "n_points": 24,
        "strength": 10, 
        "min_strength": 1,
        "max_strength": 40,
        "recommended_strength": 10,
        "method": "uniform"  # LBP method
    }
}

# File paths
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, "stego_settings.json")

def load_config():
    """Load configuration from file or use defaults"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
            # Validate and fill in any missing values
            for method in DEFAULT_CONFIG:
                if method not in config:
                    config[method] = DEFAULT_CONFIG[method]
                else:
                    for param in DEFAULT_CONFIG[method]:
                        if param not in config[method]:
                            config[method][param] = DEFAULT_CONFIG[method][param]
                            
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_method_params(method):
    """Get parameters for a specific steganography method"""
    config = load_config()
    if method in config:
        return config[method]
    return DEFAULT_CONFIG.get(method, {})

def reset_to_defaults():
    """Reset all configuration to defaults"""
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def update_method_param(method, param, value):
    """Update a specific parameter for a method"""
    config = load_config()
    if method not in config:
        config[method] = DEFAULT_CONFIG.get(method, {})
    
    config[method][param] = value
    save_config(config)
    return config

# Initialize configuration on first import
if not os.path.exists(CONFIG_FILE):
    save_config(DEFAULT_CONFIG)
