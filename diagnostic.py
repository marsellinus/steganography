"""
Diagnostic tool for debugging steganography encoding and decoding
"""
import numpy as np
import cv2
import matplotlib.pyplot as plt
import sys
import os
import math

def diagnose_encoded_image(original_path, stego_path, output_dir=None):
    """
    Diagnose differences between original and stego images
    
    Args:
        original_path: Path to the original cover image
        stego_path: Path to the stego image
        output_dir: Directory to save diagnostic images (default: current directory)
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    # Load images
    original = cv2.imread(original_path)
    stego = cv2.imread(stego_path)
    
    if original is None:
        print(f"Error: Could not load original image from {original_path}")
        return
    if stego is None:
        print(f"Error: Could not load stego image from {stego_path}")
        return
    
    # Resize stego image if dimensions don't match
    if original.shape != stego.shape:
        print(f"Warning: Image dimensions don't match. Resizing stego image.")
        stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
    
    # Convert to RGB for display
    original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    stego_rgb = cv2.cvtColor(stego, cv2.COLOR_BGR2RGB)
    
    # Calculate absolute difference
    diff = cv2.absdiff(original, stego)
    
    # Create amplified difference for visualization
    diff_x5 = cv2.convertScaleAbs(diff, alpha=5)  # 5x amplification
    diff_x20 = cv2.convertScaleAbs(diff, alpha=20)  # 20x amplification
    
    # Apply color map for better visualization
    diff_color = cv2.applyColorMap(diff_x5, cv2.COLORMAP_JET)
    diff_color_rgb = cv2.cvtColor(diff_color, cv2.COLOR_BGR2RGB)
    
    # Calculate quality metrics
    mse = np.mean((original - stego) ** 2)
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 20 * math.log10(255.0 / math.sqrt(mse))
    
    # Create histogram of differences
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    hist_diff = cv2.calcHist([diff_gray], [0], None, [256], [0, 256])
    
    # Split into channels and create difference per channel
    b_orig, g_orig, r_orig = cv2.split(original)
    b_stego, g_stego, r_stego = cv2.split(stego)
    
    b_diff = cv2.absdiff(b_orig, b_stego)
    g_diff = cv2.absdiff(g_orig, g_stego)
    r_diff = cv2.absdiff(r_orig, r_stego)
    
    # Calculate statistics per channel
    channel_stats = {
        'Blue': {
            'mean_diff': np.mean(b_diff),
            'max_diff': np.max(b_diff),
            'nonzero': np.count_nonzero(b_diff),
            'mse': np.mean(b_diff ** 2)
        },
        'Green': {
            'mean_diff': np.mean(g_diff),
            'max_diff': np.max(g_diff),
            'nonzero': np.count_nonzero(g_diff),
            'mse': np.mean(g_diff ** 2)
        },
        'Red': {
            'mean_diff': np.mean(r_diff),
            'max_diff': np.max(r_diff),
            'nonzero': np.count_nonzero(r_diff),
            'mse': np.mean(r_diff ** 2)
        }
    }
    
    # Plot the results
    plt.figure(figsize=(16, 14))
    
    # Original vs Stego
    plt.subplot(331)
    plt.imshow(original_rgb)
    plt.title('Original')
    plt.axis('off')
    
    plt.subplot(332)
    plt.imshow(stego_rgb)
    plt.title('Stego')
    plt.axis('off')
    
    plt.subplot(333)
    plt.imshow(diff_color_rgb)
    plt.title('Difference (5x amplified)')
    plt.axis('off')
    
    # Channel differences
    plt.subplot(334)
    plt.imshow(b_diff, cmap='hot')
    plt.title(f'Blue Channel Diff\nMean: {channel_stats["Blue"]["mean_diff"]:.2f}')
    plt.axis('off')
    plt.colorbar(shrink=0.7)
    
    plt.subplot(335)
    plt.imshow(g_diff, cmap='hot')
    plt.title(f'Green Channel Diff\nMean: {channel_stats["Green"]["mean_diff"]:.2f}')
    plt.axis('off')
    plt.colorbar(shrink=0.7)
    
    plt.subplot(336)
    plt.imshow(r_diff, cmap='hot')
    plt.title(f'Red Channel Diff\nMean: {channel_stats["Red"]["mean_diff"]:.2f}')
    plt.axis('off')
    plt.colorbar(shrink=0.7)
    
    # Difference histogram
    plt.subplot(337)
    plt.plot(hist_diff)
    plt.title('Histogram of Differences')
    plt.xlim([0, 50])  # Focus on the lower difference values
    plt.xlabel('Difference Value')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    # More amplified difference
    plt.subplot(338)
    diff_x20_rgb = cv2.cvtColor(diff_x20, cv2.COLOR_BGR2RGB)
    plt.imshow(diff_x20_rgb)
    plt.title('Difference (20x amplified)')
    plt.axis('off')
    
    # Text information
    plt.subplot(339)
    plt.axis('off')
    info_text = f"Image Quality Metrics:\n\n"
    info_text += f"PSNR: {psnr:.2f} dB\n"
    info_text += f"MSE: {mse:.4f}\n\n"
    info_text += "Channel Analysis:\n\n"
    
    for channel, stats in channel_stats.items():
        info_text += f"{channel} Channel:\n"
        info_text += f"  Mean Diff: {stats['mean_diff']:.4f}\n"
        info_text += f"  Max Diff: {stats['max_diff']}\n"
        info_text += f"  Non-zero: {stats['nonzero']} pixels\n"
        info_text += f"  MSE: {stats['mse']:.4f}\n\n"
    
    plt.text(0, 0.5, info_text, fontsize=9, verticalalignment='center')
    
    # Save the figure
    diagnostic_filename = os.path.join(output_dir, os.path.basename(stego_path).replace('.', '_diagnostic.'))
    plt.suptitle(f"Steganography Analysis: {os.path.basename(original_path)} → {os.path.basename(stego_path)}", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(diagnostic_filename)
    print(f"Diagnostic image saved to {diagnostic_filename}")
    
    # Show the plot
    plt.show()
    
    return {
        'psnr': psnr,
        'mse': mse,
        'channel_stats': channel_stats,
    }

def diagnose_bit_patterns(stego_path, method='DFT', strength=10.0):
    """
    Analyze and visualize bit patterns in stego image
    
    Args:
        stego_path: Path to the stego image
        method: Steganography method used ('DFT', 'SVD', 'LBP')
        strength: Strength parameter used
    """
    # Load the stego image
    stego_img = cv2.imread(stego_path)
    if stego_img is None:
        print(f"Error: Could not load stego image from {stego_path}")
        return
    
    # Example visualization for DFT method
    if method == 'DFT':
        # Extract green channel (used by DFT method)
        green_channel = stego_img[:, :, 1].astype(np.float32)
        
        # Apply DFT
        dft = cv2.dft(green_channel, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # Calculate magnitude spectrum
        magnitude_spectrum = 20 * np.log(cv2.magnitude(dft_shift[:,:,0], dft_shift[:,:,1]) + 1)
        
        # Normalize for visualization
        magnitude_spectrum_norm = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Plot DFT visualization
        plt.figure(figsize=(12, 6))
        
        plt.subplot(121)
        plt.imshow(stego_img[:,:,::-1])  # BGR to RGB
        plt.title('Stego Image')
        plt.axis('off')
        
        plt.subplot(122)
        plt.imshow(magnitude_spectrum_norm, cmap='viridis')
        plt.title('DFT Magnitude Spectrum')
        plt.colorbar(shrink=0.8)
        
        # Mark the embedding region
        rows, cols = green_channel.shape
        crow, ccol = rows // 2, cols // 2
        r_min = crow - rows // 8
        r_max = crow - rows // 16
        c_min = ccol - cols // 8
        c_max = ccol + cols // 8
        
        # Create rectangle patch for embedding region
        from matplotlib.patches import Rectangle
        rect = Rectangle((c_min, r_min), c_max - c_min, r_max - r_min, 
                         linewidth=1, edgecolor='r', facecolor='none')
        plt.gca().add_patch(rect)
        plt.axis('off')
        
        plt.suptitle(f"DFT Analysis for {os.path.basename(stego_path)}")
        plt.tight_layout()
        plt.show()
    
    # Example visualization for SVD method
    elif method == 'SVD':
        # Extract red channel (used by SVD method)
        red_channel = stego_img[:, :, 2]
        
        block_size = 8  # Default block size
        height, width = red_channel.shape
        
        # Sample some blocks for visualization
        blocks_h = height // block_size
        blocks_w = width // block_size
        
        # Create a grid showing singular values
        plt.figure(figsize=(14, 6))
        
        plt.subplot(121)
        plt.imshow(stego_img[:,:,::-1])  # BGR to RGB
        plt.title('Stego Image')
        plt.axis('off')
        
        # Create a visualization grid for singular values
        grid_h = min(10, blocks_h)
        grid_w = min(10, blocks_w)
        s_values = np.zeros((grid_h, grid_w))
        
        for i in range(grid_h):
            for j in range(grid_w):
                y = i * block_size
                x = j * block_size
                block = red_channel[y:y+block_size, x:x+block_size].astype(np.float64)
                
                try:
                    # Apply SVD and get the largest singular value
                    U, S, Vt = np.linalg.svd(block, full_matrices=False)
                    s_values[i, j] = S[0] % strength  # Get the remainder
                except:
                    s_values[i, j] = 0
        
        plt.subplot(122)
        plt.imshow(s_values, cmap='coolwarm', vmin=0, vmax=strength)
        plt.title('SVD Largest Singular Values (Modulo Strength)')
        plt.colorbar(shrink=0.8)
        plt.axis('off')
        
        plt.suptitle(f"SVD Analysis for {os.path.basename(stego_path)}")
        plt.tight_layout()
        plt.show()
    
    # Example visualization for LBP method
    elif method == 'LBP':
        # Convert to grayscale for LBP
        gray = cv2.cvtColor(stego_img, cv2.COLOR_BGR2GRAY)
        
        # Calculate LBP (using default parameters from the LBP class)
        radius = 3
        n_points = 24
        from skimage.feature import local_binary_pattern
        lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
        lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Extract blue channel where modifications were made
        blue_channel = stego_img[:, :, 0]
        
        # Create a visualization
        plt.figure(figsize=(16, 6))
        
        plt.subplot(131)
        plt.imshow(stego_img[:,:,::-1])  # BGR to RGB
        plt.title('Stego Image')
        plt.axis('off')
        
        plt.subplot(132)
        plt.imshow(lbp_normalized, cmap='gray')
        plt.title('LBP Texture')
        plt.axis('off')
        
        # Calculate the normalized values for blue channel
        plt.subplot(133)
        blue_norm = blue_channel % strength
        plt.imshow(blue_norm, cmap='coolwarm', vmin=0, vmax=strength)
        plt.title('Blue Channel (Modulo Strength)')
        plt.colorbar(shrink=0.8)
        
        plt.suptitle(f"LBP Analysis for {os.path.basename(stego_path)}")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:\npython diagnostic.py <original_image> <stego_image> [output_dir]")
        sys.exit(1)
    
    original_path = sys.argv[1]
    stego_path = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    diagnose_encoded_image(original_path, stego_path, output_dir)
