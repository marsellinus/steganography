"""
Modul untuk analisis audio dalam konteks steganografi.
Menyediakan fungsi-fungsi untuk visualisasi dan analisis kualitas audio.
"""

import numpy as np
import matplotlib
# Set non-interactive backend to avoid thread issues
matplotlib.use('Agg')  # Must be before importing pyplot
import matplotlib.pyplot as plt
import soundfile as sf
import librosa
import librosa.display
import os
from scipy import signal
from scipy.fft import fft, fftfreq
import math
import datetime
import threading

# Thread lock for matplotlib operations
plt_lock = threading.Lock()

def load_audio(file_path):
    """
    Loads audio file and returns data and sample rate
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        audio_data, sample_rate
    """
    try:
        audio_data, sample_rate = sf.read(file_path)
        return audio_data, sample_rate
    except Exception as e:
        print(f"Error loading audio file: {str(e)}")
        return None, None

def create_waveform_plot(audio_data, sample_rate, title="Audio Waveform"):
    """
    Creates a waveform plot for the audio data
    
    Args:
        audio_data: The audio data
        sample_rate: Sample rate of the audio
        title: Title for the plot
        
    Returns:
        A matplotlib figure
    """
    with plt_lock:  # Use lock for thread safety
        fig = plt.figure(figsize=(10, 4))
        if len(audio_data.shape) > 1:  # Stereo
            plt.plot(np.arange(len(audio_data)) / sample_rate, audio_data[:, 0], alpha=0.7)
            plt.plot(np.arange(len(audio_data)) / sample_rate, audio_data[:, 1], alpha=0.7)
            plt.legend(['Left Channel', 'Right Channel'])
        else:  # Mono
            plt.plot(np.arange(len(audio_data)) / sample_rate, audio_data)
            plt.legend(['Mono Channel'])
            
        plt.title(title)
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.tight_layout()
        
        return fig

def create_spectrogram(audio_data, sample_rate, title="Spectrogram"):
    """
    Creates a spectrogram for the audio data
    
    Args:
        audio_data: The audio data (if stereo, only first channel is used)
        sample_rate: Sample rate of the audio
        title: Title for the plot
        
    Returns:
        A matplotlib figure
    """
    with plt_lock:  # Use lock for thread safety
        fig = plt.figure(figsize=(10, 4))
        
        # If stereo, use only left channel for spectrogram
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
        
        D = librosa.amplitude_to_db(np.abs(librosa.stft(audio_data)), ref=np.max)
        librosa.display.specshow(D, sr=sample_rate, x_axis='time', y_axis='log')
        plt.colorbar(format='%+2.0f dB')
        plt.title(title)
        plt.tight_layout()
        
        return fig

def create_fft_plot(audio_data, sample_rate, title="Frequency Spectrum"):
    """
    Creates a frequency spectrum plot for the audio data
    
    Args:
        audio_data: The audio data
        sample_rate: Sample rate of the audio
        title: Title for the plot
        
    Returns:
        A matplotlib figure
    """
    with plt_lock:  # Use lock for thread safety
        fig = plt.figure(figsize=(10, 4))
        
        # If stereo, use only left channel
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]
        
        # Calculate FFT
        N = len(audio_data)
        yf = fft(audio_data)
        xf = fftfreq(N, 1 / sample_rate)[:N//2]
        
        # Plot positive frequencies only
        plt.plot(xf, 2.0/N * np.abs(yf[:N//2]))
        plt.grid()
        plt.title(title)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        plt.xscale('log')
        plt.xlim(20, sample_rate/2)  # 20Hz to Nyquist frequency
        plt.tight_layout()
        
        return fig

def calculate_snr(original_audio, stego_audio):
    """
    Calculate Signal-to-Noise Ratio between original and stego audio
    
    Args:
        original_audio: Original audio data
        stego_audio: Stego audio data
        
    Returns:
        SNR value in dB
    """
    # Ensure both arrays have same shape
    min_len = min(len(original_audio), len(stego_audio))
    original_audio = original_audio[:min_len]
    stego_audio = stego_audio[:min_len]
    
    # Calculate noise (difference)
    noise = original_audio - stego_audio
    
    # Calculate signal power and noise power
    signal_power = np.sum(original_audio ** 2)
    noise_power = np.sum(noise ** 2)
    
    # Calculate SNR
    if noise_power == 0:  # No difference
        return float('inf')
    
    snr = 10 * math.log10(signal_power / noise_power)
    return snr

def calculate_psnr(original_audio, stego_audio):
    """
    Calculate Peak Signal-to-Noise Ratio between original and stego audio
    
    Args:
        original_audio: Original audio data
        stego_audio: Stego audio data
        
    Returns:
        PSNR value in dB
    """
    # Ensure both arrays have same shape
    min_len = min(len(original_audio), len(stego_audio))
    original_audio = original_audio[:min_len]
    stego_audio = stego_audio[:min_len]
    
    # Calculate MSE
    mse = np.mean((original_audio - stego_audio) ** 2)
    
    if mse == 0:  # Identical
        return float('inf')
    
    # For audio, peak value depends on format, but typically normalized to 1.0
    peak = np.max(np.abs(original_audio))
    if peak == 0:
        peak = 1.0
        
    psnr = 20 * math.log10(peak / math.sqrt(mse))
    return psnr

def calculate_lsd(original_audio, stego_audio, sample_rate):
    """
    Calculate Log-Spectral Distance between original and stego audio
    
    Args:
        original_audio: Original audio data
        stego_audio: Stego audio data
        sample_rate: Sample rate of the audio
        
    Returns:
        LSD value
    """
    # Ensure both arrays have same shape
    min_len = min(len(original_audio), len(stego_audio))
    original_audio = original_audio[:min_len]
    stego_audio = stego_audio[:min_len]
    
    # Make sure we have enough samples for nperseg
    nperseg = min(1024, min_len)  # Fix for "nperseg > input length" warning
    if min_len < 1024:
        print(f"Warning: Short audio file detected (length={min_len} samples). Using nperseg={nperseg}")
        
    try:
        # Calculate power spectral density
        f, Pxx_orig = signal.welch(original_audio, sample_rate, nperseg=nperseg)
        _, Pxx_stego = signal.welch(stego_audio, sample_rate, nperseg=nperseg)
        
        # Log-Spectral Distance
        lsd = np.sqrt(np.mean((10*np.log10(Pxx_orig + 1e-10) - 10*np.log10(Pxx_stego + 1e-10))**2))
        return lsd
    except Exception as e:
        print(f"Error calculating LSD: {str(e)}")
        return 0.0

def compare_audio_files(original_path, stego_path, output_dir=None):
    """
    Comprehensive audio comparison between original and stego files
    
    Args:
        original_path: Path to the original audio file
        stego_path: Path to the stego audio file
        output_dir: Directory to save plots (optional)
        
    Returns:
        A dictionary of metrics and figures
    """
    # Load audio files
    orig_audio, orig_sr = load_audio(original_path)
    stego_audio, stego_sr = load_audio(stego_path)
    
    if orig_audio is None or stego_audio is None:
        return {"error": "Failed to load audio files"}
    
    # Check if sample rates match
    if orig_sr != stego_sr:
        return {"error": "Sample rates don't match"}
    
    # Generate a unique base name for this analysis
    import uuid
    base_name = f"audio_analysis_{uuid.uuid4().hex[:8]}"
    
    try:
        # Calculate audio quality metrics
        snr = calculate_snr(orig_audio, stego_audio)
        psnr = calculate_psnr(orig_audio, stego_audio)
        lsd = calculate_lsd(orig_audio, stego_audio, orig_sr)
        
        # Create figures
        waveform_orig = create_waveform_plot(orig_audio, orig_sr, "Original Audio Waveform")
        waveform_stego = create_waveform_plot(stego_audio, stego_sr, "Stego Audio Waveform")
        
        # Create spectrogram plots
        spec_orig = create_spectrogram(orig_audio, orig_sr, "Original Audio Spectrogram")
        spec_stego = create_spectrogram(stego_audio, stego_sr, "Stego Audio Spectrogram")
        
        # Create FFT plots
        fft_orig = create_fft_plot(orig_audio, orig_sr, "Original Audio Frequency Spectrum")
        fft_stego = create_fft_plot(stego_audio, stego_sr, "Stego Audio Frequency Spectrum")
        
        # Create difference plot
        min_len = min(len(orig_audio), len(stego_audio))
        if len(orig_audio.shape) > 1:  # Stereo
            diff_audio = orig_audio[:min_len, 0] - stego_audio[:min_len, 0]
        else:  # Mono
            diff_audio = orig_audio[:min_len] - stego_audio[:min_len]
        
        # Amplify difference by factor for better visualization
        amplification = 50
        diff_plot = create_waveform_plot(diff_audio * amplification, orig_sr, 
                                        f"Difference Waveform (Amplified {amplification}x)")
        
        # Save plots if output directory is specified
        if output_dir and os.path.exists(output_dir):
            waveform_orig_path = os.path.join(output_dir, f"{base_name}_waveform_orig.png")
            waveform_stego_path = os.path.join(output_dir, f"{base_name}_waveform_stego.png")
            spec_orig_path = os.path.join(output_dir, f"{base_name}_spec_orig.png")
            spec_stego_path = os.path.join(output_dir, f"{base_name}_spec_stego.png")
            fft_orig_path = os.path.join(output_dir, f"{base_name}_fft_orig.png")
            fft_stego_path = os.path.join(output_dir, f"{base_name}_fft_stego.png")
            diff_path = os.path.join(output_dir, f"{base_name}_difference.png")
            
            waveform_orig.savefig(waveform_orig_path)
            waveform_stego.savefig(waveform_stego_path)
            spec_orig.savefig(spec_orig_path)
            spec_stego.savefig(spec_stego_path)
            fft_orig.savefig(fft_orig_path)
            fft_stego.savefig(fft_stego_path)
            diff_plot.savefig(diff_path)
            
            # Close figures to free memory
            plt.close(waveform_orig)
            plt.close(waveform_stego)
            plt.close(spec_orig)
            plt.close(spec_stego)
            plt.close(fft_orig)
            plt.close(fft_stego)
            plt.close(diff_plot)
        
        # Return the metrics and figures
        return {
            "metrics": {
                "SNR": snr,
                "PSNR": psnr,
                "LSD": lsd
            },
            "figures": {
                "waveform_orig": waveform_orig,
                "waveform_stego": waveform_stego,
                "spec_orig": spec_orig,
                "spec_stego": spec_stego,
                "fft_orig": fft_orig,
                "fft_stego": fft_stego,
                "difference": diff_plot
            }
        }
    except Exception as e:
        print(f"Error in audio comparison: {str(e)}")
        return {"error": str(e)}

def generate_audio_report(original_path, stego_path, output_dir):
    """
    Generates a complete HTML report with audio analysis
    
    Args:
        original_path: Path to the original audio file
        stego_path: Path to the stego audio file
        output_dir: Directory to save the report
        
    Returns:
        Path to the generated HTML report
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate plots and get metrics
    result = compare_audio_files(original_path, stego_path, output_dir)
    
    if "error" in result:
        return None
    
    metrics = result["metrics"]
    
    # Format metrics for display
    snr_formatted = f"{metrics['SNR']:.2f} dB"
    psnr_formatted = f"{metrics['PSNR']:.2f} dB"
    lsd_formatted = f"{metrics['LSD']:.4f}"
    
    # Assess quality
    if metrics['PSNR'] > 70:
        quality = "Excellent - Differences inaudible"
    elif metrics['PSNR'] > 50:
        quality = "Very Good - Differences unlikely to be heard"
    elif metrics['PSNR'] > 30:
        quality = "Good - Differences possibly audible with good equipment"
    elif metrics['PSNR'] > 20:
        quality = "Acceptable - Differences might be audible"
    else:
        quality = "Poor - Differences likely audible"
        
    # Generate base filenames for plots
    import uuid
    base_name = f"audio_analysis_{uuid.uuid4().hex[:8]}"
    
    # Paths to saved figures - use the base_name to match what was used in compare_audio_files
    waveform_orig_path = f"{base_name}_waveform_orig.png"
    waveform_stego_path = f"{base_name}_waveform_stego.png"
    spec_orig_path = f"{base_name}_spec_orig.png"
    spec_stego_path = f"{base_name}_spec_stego.png"
    fft_orig_path = f"{base_name}_fft_orig.png"
    fft_stego_path = f"{base_name}_fft_stego.png"
    diff_path = f"{base_name}_difference.png"
    
    # Create HTML content
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Steganography Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2a6496;
        }}
        .metric-box {{
            display: inline-block;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px 20px;
            margin: 10px;
            text-align: center;
            width: 150px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2a6496;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
        }}
        .plot-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            margin: 20px 0;
        }}
        .plot {{
            margin: 10px;
            max-width: 100%;
        }}
        .quality-assessment {{
            background-color: #e9f7ef;
            border-left: 5px solid #27ae60;
            padding: 15px;
            margin: 20px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>Audio Steganography Analysis Report</h1>
    
    <div>
        <p><strong>Original File:</strong> {os.path.basename(original_path)}</p>
        <p><strong>Stego File:</strong> {os.path.basename(stego_path)}</p>
        <p><strong>Analysis Date:</strong> {current_date}</p>
    </div>
    
    <h2>Audio Quality Metrics</h2>
    <div>
        <div class="metric-box">
            <div class="metric-value">{snr_formatted}</div>
            <div class="metric-label">Signal-to-Noise Ratio</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{psnr_formatted}</div>
            <div class="metric-label">Peak Signal-to-Noise Ratio</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{lsd_formatted}</div>
            <div class="metric-label">Log-Spectral Distance</div>
        </div>
    </div>
    
    <div class="quality-assessment">
        <h3>Quality Assessment</h3>
        <p>{quality}</p>
    </div>
    
    <h2>Waveform Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Waveform</h3>
            <img src="{waveform_orig_path}" alt="Original Audio Waveform">
        </div>
        <div class="plot">
            <h3>Stego Audio Waveform</h3>
            <img src="{waveform_stego_path}" alt="Stego Audio Waveform">
        </div>
    </div>
    
    <h2>Spectrogram Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Spectrogram</h3>
            <img src="{spec_orig_path}" alt="Original Audio Spectrogram">
        </div>
        <div class="plot">
            <h3>Stego Audio Spectrogram</h3>
            <img src="{spec_stego_path}" alt="Stego Audio Spectrogram">
        </div>
    </div>
    
    <h2>Frequency Spectrum Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Frequency Spectrum</h3>
            <img src="{fft_orig_path}" alt="Original Audio Frequency Spectrum">
        </div>
        <div class="plot">
            <h3>Stego Audio Frequency Spectrum</h3>
            <img src="{fft_stego_path}" alt="Stego Audio Frequency Spectrum">
        </div>
    </div>
    
    <h2>Difference Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Difference Waveform (Amplified)</h3>
            <img src="{diff_path}" alt="Difference Waveform">
            <p>Note: Differences are amplified by 50x for visibility</p>
        </div>
    </div>
    
    <footer>
        <p>Transform Domain Steganography Analysis Tool</p>
    </footer>
</body>
</html>
"""
    
    # Write HTML to file
    report_path = os.path.join(output_dir, f"{base_name}_report.html")
    with open(report_path, "w") as f:
        f.write(html_content)
    
    return report_path

if __name__ == "__main__":
    # Simple test function if run directly
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python audio_analysis.py [original_audio] [stego_audio]")
        sys.exit(1)
    
    original_path = sys.argv[1]
    stego_path = sys.argv[2]
    
    # Set output directory to current directory
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Generating audio report for {os.path.basename(original_path)} and {os.path.basename(stego_path)}...")
    report_path = generate_audio_report(original_path, stego_path, output_dir)
    
    if report_path:
        print(f"Report generated: {report_path}")
    else:
        print("Failed to generate report!")
