"""
Helper functions for image processing in steganography applications
"""
import os
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

def normalize_image_format(input_path, output_path=None, format="png"):
    """
    Convert image to a consistent format for steganography
    
    Args:
        input_path: Path to input image
        output_path: Path to save normalized image (if None, overwrites input)
        format: Target format ('png' or 'bmp' recommended for steganography)
        
    Returns:
        Path to normalized image
    """
    if output_path is None:
        base_path = os.path.splitext(input_path)[0]
        output_path = f"{base_path}_normalized.{format}"
    
    try:
        # Open with PIL for better format handling
        img = Image.open(input_path)
        
        # Convert to RGB mode if needed
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Save in target format
        img.save(output_path, format=format.upper())
        
        return output_path
    except Exception as e:
        print(f"Error normalizing image: {str(e)}")
        return None

def create_difference_visualization(original_path, stego_path, output_path=None, amplification=10):
    """
    Create a visualization of differences between original and stego images
    
    Args:
        original_path: Path to original image
        stego_path: Path to stego image
        output_path: Path to save difference visualization
        amplification: Factor to amplify differences (default: 10)
        
    Returns:
        Path to difference visualization
    """
    if output_path is None:
        base_path = os.path.splitext(stego_path)[0]
        output_path = f"{base_path}_diff.png"
    
    try:
        # Read images
        original = cv2.imread(original_path)
        stego = cv2.imread(stego_path)
        
        # Resize if dimensions don't match
        if original.shape != stego.shape:
            stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
        
        # Calculate absolute difference
        diff = cv2.absdiff(original, stego)
        diff_amplified = cv2.convertScaleAbs(diff, alpha=amplification)
        
        # Apply colormap for better visualization
        diff_color = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)
        
        # Save difference image
        cv2.imwrite(output_path, diff_color)
        
        return output_path
    except Exception as e:
        print(f"Error creating difference visualization: {str(e)}")
        return None

def calculate_image_metrics(original_path, stego_path):
    """
    Calculate quality metrics between original and stego images
    
    Args:
        original_path: Path to original image
        stego_path: Path to stego image
        
    Returns:
        Dictionary with quality metrics
    """
    try:
        # Read images
        original = cv2.imread(original_path)
        stego = cv2.imread(stego_path)
        
        # Resize if dimensions don't match
        if original.shape != stego.shape:
            stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
        
        # Calculate MSE
        mse = np.mean((original.astype(float) - stego.astype(float)) ** 2)
        
        # Calculate PSNR
        if mse == 0:
            psnr = float('inf')
        else:
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        # Calculate histogram correlation for each channel
        hist_corr = []
        for i in range(3):
            hist_orig = cv2.calcHist([original], [i], None, [256], [0, 256]).flatten()
            hist_stego = cv2.calcHist([stego], [i], None, [256], [0, 256]).flatten()
            
            # Normalize histograms
            hist_orig = hist_orig / np.sum(hist_orig)
            hist_stego = hist_stego / np.sum(hist_stego)
            
            # Calculate correlation
            corr = np.correlate(hist_orig, hist_stego)[0]
            hist_corr.append(corr)
        
        # Return all metrics
        metrics = {
            'mse': float(mse),
            'psnr': float(psnr),
            'hist_correlation': {
                'blue': float(hist_corr[0]),
                'green': float(hist_corr[1]),
                'red': float(hist_corr[2]),
                'average': float(np.mean(hist_corr))
            }
        }
        
        # Calculate SSIM if scikit-image is available
        try:
            from skimage.metrics import structural_similarity as ssim
            s = ssim(original, stego, multichannel=True)
            metrics['ssim'] = float(s)
        except:
            metrics['ssim'] = None
            
        return metrics
        
    except Exception as e:
        print(f"Error calculating image metrics: {str(e)}")
        return {'error': str(e)}

def create_comparison_figure(original_path, stego_path, diff_path=None):
    """
    Create a comparison figure with original, stego, difference, and histograms
    
    Args:
        original_path: Path to original image
        stego_path: Path to stego image
        diff_path: Path to difference image (or None to generate on the fly)
        
    Returns:
        Figure object
    """
    try:
        # Read images
        original = cv2.imread(original_path)
        stego = cv2.imread(stego_path)
        
        # Resize if dimensions don't match
        if original.shape != stego.shape:
            stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
        
        # Create or load difference image
        if diff_path and os.path.exists(diff_path):
            diff = cv2.imread(diff_path)
        else:
            diff = cv2.absdiff(original, stego)
            diff = cv2.convertScaleAbs(diff, alpha=10)
            diff = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
        
        # Convert from BGR to RGB for matplotlib
        original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        stego = cv2.cvtColor(stego, cv2.COLOR_BGR2RGB)
        diff = cv2.cvtColor(diff, cv2.COLOR_BGR2RGB)
        
        # Create figure
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Display images
        axes[0, 0].imshow(original)
        axes[0, 0].set_title('Original')
        axes[0, 0].axis('off')
        
        axes[0, 1].imshow(stego)
        axes[0, 1].set_title('Stego')
        axes[0, 1].axis('off')
        
        axes[0, 2].imshow(diff)
        axes[0, 2].set_title('Difference (Amplified 10x)')
        axes[0, 2].axis('off')
        
        # Calculate histograms
        colors = ('r', 'g', 'b')
        for i, color in enumerate(colors):
            # Original histogram
            hist_orig = cv2.calcHist([original], [i], None, [256], [0, 256])
            axes[1, 0].plot(hist_orig, color=color)
            
            # Stego histogram
            hist_stego = cv2.calcHist([stego], [i], None, [256], [0, 256])
            axes[1, 1].plot(hist_stego, color=color)
            
            # Difference between histograms
            hist_diff = np.abs(hist_orig - hist_stego)
            axes[1, 2].plot(hist_diff, color=color)
        
        # Set histogram properties
        axes[1, 0].set_title('Original Histogram')
        axes[1, 0].set_xlim([0, 256])
        axes[1, 0].grid(True)
        
        axes[1, 1].set_title('Stego Histogram')
        axes[1, 1].set_xlim([0, 256])
        axes[1, 1].grid(True)
        
        axes[1, 2].set_title('Histogram Difference')
        axes[1, 2].set_xlim([0, 256])
        axes[1, 2].grid(True)
        
        # Calculate metrics
        metrics = calculate_image_metrics(original_path, stego_path)
        
        # Add metrics as text
        fig.suptitle(f"Steganography Analysis\nPSNR: {metrics['psnr']:.2f} dB | MSE: {metrics['mse']:.2f} | SSIM: {metrics.get('ssim', 'N/A') or 'N/A'}")
        
        plt.tight_layout()
        
        return fig
    except Exception as e:
        print(f"Error creating comparison figure: {str(e)}")
        return None

if __name__ == "__main__":
    # Simple test function if run directly
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python image_utils.py [original_image] [stego_image]")
        sys.exit(1)
    
    original_path = sys.argv[1]
    stego_path = sys.argv[2]
    
    # Calculate metrics
    metrics = calculate_image_metrics(original_path, stego_path)
    print("Image Quality Metrics:")
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")
    
    # Create and show comparison figure
    fig = create_comparison_figure(original_path, stego_path)
    plt.show()
