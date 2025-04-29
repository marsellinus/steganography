"""
Audio Analyzer class for steganography application.
Provides tools for analyzing and comparing audio files.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import soundfile as sf
import librosa
import librosa.display
from scipy import signal
from scipy.fft import fft, fftfreq
import math
import threading
import uuid
import datetime
from dataclasses import dataclass
from scipy import stats

# Thread lock for matplotlib operations
plt_lock = threading.Lock()

@dataclass
class AudioMetrics:
    """Data class for storing audio quality metrics"""
    snr: float
    psnr: float
    lsd: float
    mse: float
    duration: float
    sample_rate: int
    channels: int
    histogram_correlation: float = 0.0
    
    @property
    def quality_rating(self):
        """Get a quality rating based on PSNR"""
        if self.psnr > 70:
            return "Excellent", "green"
        elif self.psnr > 50:
            return "Very Good", "green"
        elif self.psnr > 30:
            return "Good", "blue"
        elif self.psnr > 20:
            return "Acceptable", "yellow"
        else:
            return "Poor", "red"

class AudioAnalyzer:
    """Class for audio analysis in steganography applications"""
    
    def __init__(self, temp_dir=None):
        """
        Initialize the analyzer
        
        Args:
            temp_dir: Directory to store temporary files
        """
        self.temp_dir = temp_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.uuid = uuid.uuid4().hex[:8]  # Unique identifier for this instance
        
    def load_audio(self, file_path):
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
            
    def calculate_metrics(self, original_path, stego_path):
        """
        Calculate quality metrics between original and stego audio
        
        Args:
            original_path: Path to the original audio file
            stego_path: Path to the stego audio file
            
        Returns:
            AudioMetrics object with calculated metrics
        """
        # Load audio files
        orig_audio, orig_sr = self.load_audio(original_path)
        stego_audio, stego_sr = self.load_audio(stego_path)
        
        if orig_audio is None or stego_audio is None:
            raise ValueError("Failed to load audio files")
        
        # Check if sample rates match
        if orig_sr != stego_sr:
            raise ValueError("Sample rates don't match")
            
        # Get audio duration and channel count
        duration = len(orig_audio) / orig_sr
        channels = 1 if len(orig_audio.shape) == 1 else orig_audio.shape[1]
            
        # Ensure both arrays have same shape for comparison
        min_len = min(len(orig_audio), len(stego_audio))
        orig_audio_trim = orig_audio[:min_len]
        stego_audio_trim = stego_audio[:min_len]
        
        # Calculate SNR
        noise = orig_audio_trim - stego_audio_trim
        signal_power = np.sum(orig_audio_trim ** 2)
        noise_power = np.sum(noise ** 2)
        
        snr = float('inf') if noise_power == 0 else 10 * math.log10(signal_power / noise_power)
        
        # Calculate MSE
        mse = np.mean((orig_audio_trim - stego_audio_trim) ** 2)
        
        # Calculate PSNR
        peak = np.max(np.abs(orig_audio_trim))
        if peak == 0:
            peak = 1.0
        psnr = float('inf') if mse == 0 else 20 * math.log10(peak / math.sqrt(mse))
        
        # Calculate LSD (Log-Spectral Distance)
        try:
            # Make sure we have enough samples for nperseg
            nperseg = min(1024, min_len)
            
            f, Pxx_orig = signal.welch(orig_audio_trim, orig_sr, nperseg=nperseg)
            _, Pxx_stego = signal.welch(stego_audio_trim, orig_sr, nperseg=nperseg)
            
            lsd = np.sqrt(np.mean((10*np.log10(Pxx_orig + 1e-10) - 10*np.log10(Pxx_stego + 1e-10))**2))
        except:
            lsd = 0.0
            
        # Calculate Histogram Correlation
        hist_corr = self.calculate_histogram_correlation(orig_audio_trim, stego_audio_trim)
            
        return AudioMetrics(
            snr=snr,
            psnr=psnr,
            lsd=lsd,
            mse=mse,
            duration=duration,
            sample_rate=orig_sr,
            channels=channels,
            histogram_correlation=hist_corr
        )
    
    def calculate_histogram_correlation(self, original_audio, stego_audio):
        """
        Calculate correlation between histograms of two audio signals
        
        Args:
            original_audio: Original audio data
            stego_audio: Stego audio data
            
        Returns:
            Correlation coefficient (Pearson's r)
        """
        # Ensure both arrays have same shape
        min_len = min(len(original_audio), len(stego_audio))
        original_audio = original_audio[:min_len]
        stego_audio = stego_audio[:min_len]
        
        # Handle stereo by using first channel
        if len(original_audio.shape) > 1 and original_audio.shape[1] > 1:
            original_audio = original_audio[:, 0]
            stego_audio = stego_audio[:, 0]
        
        # Calculate histograms
        hist_bins = 100  # Number of bins for histogram
        
        # Get min and max values across both signals to ensure same scale
        min_val = min(original_audio.min(), stego_audio.min())
        max_val = max(original_audio.max(), stego_audio.max())
        
        # Create histograms with same bins
        hist_orig, edges_orig = np.histogram(original_audio, bins=hist_bins, range=(min_val, max_val))
        hist_stego, edges_stego = np.histogram(stego_audio, bins=hist_bins, range=(min_val, max_val))
        
        # Calculate correlation
        try:
            correlation, _ = stats.pearsonr(hist_orig, hist_stego)
            return correlation
        except Exception as e:
            print(f"Error calculating histogram correlation: {e}")
            return 0.0
    
    def generate_audio_histogram(self, audio_data, title="Audio Amplitude Histogram", filename=None):
        """
        Creates a histogram of audio amplitudes
        
        Args:
            audio_data: The audio data
            title: Title for the plot
            filename: If provided, save to this filename
            
        Returns:
            Path to saved plot or the figure object if filename not provided
        """
        with plt_lock:  # Use lock for thread safety
            plt.figure(figsize=(10, 4))
            
            # If stereo, use only first channel
            if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
                audio_data = audio_data[:, 0]
            
            # Plot histogram
            plt.hist(audio_data, bins=100, alpha=0.7, color='royalblue')
            plt.title(title)
            plt.xlabel('Amplitude')
            plt.ylabel('Frequency')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if filename:
                output_path = os.path.join(self.temp_dir, filename)
                plt.savefig(output_path, dpi=100)
                plt.close()
                return output_path
            else:
                return plt.gcf()
    
    def generate_histogram_comparison(self, original_audio, stego_audio, sample_rate, 
                                     title="Audio Histogram Comparison", filename=None):
        """
        Creates a comparison of histograms between original and stego audio
        
        Args:
            original_audio: Original audio data
            stego_audio: Stego audio data
            sample_rate: Sample rate of the audio
            title: Title for the plot
            filename: If provided, save to this filename
            
        Returns:
            Path to saved plot or the figure object if filename not provided
        """
        with plt_lock:  # Use lock for thread safety
            plt.figure(figsize=(10, 6))
            
            # If stereo, use only first channel
            if len(original_audio.shape) > 1 and original_audio.shape[1] > 1:
                original_audio = original_audio[:, 0]
                stego_audio = stego_audio[:, 0]
            
            # Ensure same length
            min_len = min(len(original_audio), len(stego_audio))
            original_audio = original_audio[:min_len]
            stego_audio = stego_audio[:min_len]
            
            # Plot histograms
            plt.hist(original_audio, bins=100, alpha=0.6, color='blue', label='Original')
            plt.hist(stego_audio, bins=100, alpha=0.6, color='red', label='Stego')
            
            # Calculate correlation for display
            corr = self.calculate_histogram_correlation(original_audio, stego_audio)
            
            plt.title(f"{title}\nHistogram Correlation: {corr:.4f}")
            plt.xlabel('Amplitude')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if filename:
                output_path = os.path.join(self.temp_dir, filename)
                plt.savefig(output_path, dpi=100)
                plt.close()
                return output_path
            else:
                return plt.gcf()
    
    def generate_waveform_plot(self, audio_data, sample_rate, title="Audio Waveform", filename=None):
        """
        Creates a waveform plot for the audio data
        
        Args:
            audio_data: The audio data
            sample_rate: Sample rate of the audio
            title: Title for the plot
            filename: If provided, save to this filename
            
        Returns:
            Path to saved plot or the figure object if filename not provided
        """
        with plt_lock:  # Use lock for thread safety
            plt.figure(figsize=(10, 4))
            
            # Handle stereo vs mono
            if len(audio_data.shape) > 1:  # Stereo
                plt.plot(np.arange(len(audio_data)) / sample_rate, audio_data[:, 0], 'b-', alpha=0.7)
                if audio_data.shape[1] > 1:  # Make sure there's a right channel
                    plt.plot(np.arange(len(audio_data)) / sample_rate, audio_data[:, 1], 'g-', alpha=0.7)
                    plt.legend(['Left Channel', 'Right Channel'])
                else:
                    plt.legend(['Left Channel'])
            else:  # Mono
                plt.plot(np.arange(len(audio_data)) / sample_rate, audio_data, 'b-')
                plt.legend(['Mono Channel'])
                
            plt.title(title)
            plt.xlabel("Time (s)")
            plt.ylabel("Amplitude")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if filename:
                output_path = os.path.join(self.temp_dir, filename)
                plt.savefig(output_path, dpi=100)
                plt.close()
                return output_path
            else:
                return plt.gcf()
                
    def generate_spectrogram(self, audio_data, sample_rate, title="Spectrogram", filename=None):
        """
        Creates a spectrogram for the audio data
        
        Args:
            audio_data: The audio data
            sample_rate: Sample rate of the audio
            title: Title for the plot
            filename: If provided, save to this filename
            
        Returns:
            Path to saved plot or the figure object if filename not provided
        """
        with plt_lock:  # Use lock for thread safety
            plt.figure(figsize=(10, 4))
            
            # If stereo, use only left channel for spectrogram
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]
            
            D = librosa.amplitude_to_db(np.abs(librosa.stft(audio_data)), ref=np.max)
            librosa.display.specshow(D, sr=sample_rate, x_axis='time', y_axis='log')
            plt.colorbar(format='%+2.0f dB')
            plt.title(title)
            plt.tight_layout()
            
            if filename:
                output_path = os.path.join(self.temp_dir, filename)
                plt.savefig(output_path, dpi=100)
                plt.close()
                return output_path
            else:
                return plt.gcf()
                
    def generate_frequency_spectrum(self, audio_data, sample_rate, title="Frequency Spectrum", filename=None):
        """
        Creates a frequency spectrum plot for the audio data
        
        Args:
            audio_data: The audio data
            sample_rate: Sample rate of the audio
            title: Title for the plot
            filename: If provided, save to this filename
            
        Returns:
            Path to saved plot or the figure object if filename not provided
        """
        with plt_lock:  # Use lock for thread safety
            plt.figure(figsize=(10, 4))
            
            # If stereo, use only left channel
            if len(audio_data.shape) > 1:
                audio_data = audio_data[:, 0]
            
            # Calculate FFT
            N = len(audio_data)
            yf = fft(audio_data)
            xf = fftfreq(N, 1 / sample_rate)[:N//2]
            
            # Plot positive frequencies only with log scale for better visualization
            plt.plot(xf, 2.0/N * np.abs(yf[:N//2]))
            plt.grid(True, alpha=0.3)
            plt.title(title)
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Magnitude')
            plt.xscale('log')
            plt.xlim(20, sample_rate/2)  # 20Hz to Nyquist frequency
            plt.tight_layout()
            
            if filename:
                output_path = os.path.join(self.temp_dir, filename)
                plt.savefig(output_path, dpi=100)
                plt.close()
                return output_path
            else:
                return plt.gcf()
                
    def generate_difference_plot(self, original_audio, stego_audio, sample_rate, 
                                amplification=50, title=None, filename=None):
        """
        Creates a difference waveform plot between original and stego audio
        
        Args:
            original_audio: Original audio data
            stego_audio: Stego audio data
            sample_rate: Sample rate of the audio
            amplification: Factor to amplify differences
            title: Title for the plot
            filename: If provided, save to this filename
            
        Returns:
            Path to saved plot or the figure object if filename not provided
        """
        # Ensure both arrays have same shape
        min_len = min(len(original_audio), len(stego_audio))
        
        # Create difference for first channel (or mono)
        if len(original_audio.shape) > 1:  # Stereo
            diff_audio = original_audio[:min_len, 0] - stego_audio[:min_len, 0]
        else:  # Mono
            diff_audio = original_audio[:min_len] - stego_audio[:min_len]
        
        # Amplify difference for better visualization
        diff_audio = diff_audio * amplification
        
        # Use default title if none provided
        if title is None:
            title = f"Difference Waveform (Amplified {amplification}x)"
            
        # Generate the plot
        return self.generate_waveform_plot(
            diff_audio, 
            sample_rate, 
            title=title, 
            filename=filename
        )
        
    def analyze_audio_pair(self, original_path, stego_path, output_prefix=None):
        """
        Perform comprehensive analysis on a pair of audio files
        
        Args:
            original_path: Path to the original audio file
            stego_path: Path to the stego audio file
            output_prefix: Prefix for output filenames (if None, a unique ID is used)
            
        Returns:
            Dictionary with metrics and paths to generated visualizations
        """
        # Use unique prefix if none provided
        prefix = output_prefix or f"audio_analysis_{self.uuid}"
        
        try:
            # Load audio files
            orig_audio, orig_sr = self.load_audio(original_path)
            stego_audio, stego_sr = self.load_audio(stego_path)
            
            if orig_audio is None or stego_audio is None:
                return {"error": "Failed to load audio files"}
            
            # Check if sample rates match
            if orig_sr != stego_sr:
                return {"error": "Sample rates don't match"}
                
            # Calculate metrics
            metrics = self.calculate_metrics(original_path, stego_path)
            
            # Generate visualizations
            visualizations = {}
            
            # Waveform plots
            visualizations['waveform_orig'] = self.generate_waveform_plot(
                orig_audio, 
                orig_sr, 
                "Original Audio Waveform",
                f"{prefix}_waveform_orig.png"
            )
            
            visualizations['waveform_stego'] = self.generate_waveform_plot(
                stego_audio, 
                stego_sr, 
                "Stego Audio Waveform",
                f"{prefix}_waveform_stego.png"
            )
            
            # Spectrogram plots
            visualizations['spectrogram_orig'] = self.generate_spectrogram(
                orig_audio, 
                orig_sr, 
                "Original Audio Spectrogram",
                f"{prefix}_spectrogram_orig.png"
            )
            
            visualizations['spectrogram_stego'] = self.generate_spectrogram(
                stego_audio, 
                stego_sr, 
                "Stego Audio Spectrogram",
                f"{prefix}_spectrogram_stego.png"
            )
            
            # Frequency spectrum plots
            visualizations['spectrum_orig'] = self.generate_frequency_spectrum(
                orig_audio, 
                orig_sr, 
                "Original Audio Frequency Spectrum",
                f"{prefix}_spectrum_orig.png"
            )
            
            visualizations['spectrum_stego'] = self.generate_frequency_spectrum(
                stego_audio, 
                stego_sr, 
                "Stego Audio Frequency Spectrum",
                f"{prefix}_spectrum_stego.png"
            )
            
            # Difference plot
            visualizations['difference'] = self.generate_difference_plot(
                orig_audio, 
                stego_audio,
                orig_sr,
                amplification=50,
                filename=f"{prefix}_difference.png"
            )
            
            # Add Histogram Analysis plots
            visualizations['histogram_orig'] = self.generate_audio_histogram(
                orig_audio,
                "Original Audio Amplitude Histogram",
                f"{prefix}_histogram_orig.png"
            )
            
            visualizations['histogram_stego'] = self.generate_audio_histogram(
                stego_audio,
                "Stego Audio Amplitude Histogram",
                f"{prefix}_histogram_stego.png"
            )
            
            # Add Histogram Comparison plot
            visualizations['histogram_comparison'] = self.generate_histogram_comparison(
                orig_audio,
                stego_audio,
                orig_sr,
                "Audio Histogram Comparison",
                f"{prefix}_histogram_comparison.png"
            )
            
            # Generate HTML report
            report_path = self.generate_html_report(
                original_path,
                stego_path,
                metrics,
                visualizations,
                f"{prefix}_report.html"
            )
            
            # Return all results
            return {
                "metrics": {
                    "SNR": metrics.snr,
                    "PSNR": metrics.psnr,
                    "LSD": metrics.lsd,
                    "MSE": metrics.mse,
                    "histogram_correlation": metrics.histogram_correlation,
                    "duration": metrics.duration,
                    "sample_rate": metrics.sample_rate,
                    "channels": metrics.channels,
                    "quality_rating": metrics.quality_rating[0],
                    "quality_color": metrics.quality_rating[1]
                },
                "visualizations": visualizations,
                "report_path": report_path
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
        
    def generate_html_report(self, original_path, stego_path, metrics, visualizations, output_filename):
        """
        Generate a comprehensive HTML report of the audio analysis
        
        Args:
            original_path: Path to the original audio file
            stego_path: Path to the stego audio file
            metrics: AudioMetrics object with calculated metrics
            visualizations: Dictionary with paths to visualization images
            output_filename: Filename for the HTML report
            
        Returns:
            Path to the generated HTML report
        """
        # Format metrics for display
        snr_formatted = f"{metrics.snr:.2f} dB"
        psnr_formatted = f"{metrics.psnr:.2f} dB"
        lsd_formatted = f"{metrics.lsd:.4f}"
        mse_formatted = f"{metrics.mse:.8f}"
        histogram_corr_formatted = f"{metrics.histogram_correlation:.4f}"
        duration_formatted = f"{metrics.duration:.2f} seconds"
        
        # Get quality assessment
        quality_text, quality_color = metrics.quality_rating
        
        # Get visualizations filenames only (not full paths)
        visualization_files = {k: os.path.basename(v) for k, v in visualizations.items()}
        
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
        .additional-info {{
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
        }}
        .info-item {{
            padding: 5px 0;
        }}
        .info-label {{
            font-weight: bold;
            color: #555;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            text-align: center;
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
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{psnr_formatted}</div>
            <div class="metric-label">Peak Signal-to-Noise Ratio</div>
            <div class="metric-description">Higher is better. Measures signal quality.</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{snr_formatted}</div>
            <div class="metric-label">Signal-to-Noise Ratio</div>
            <div class="metric-description">Higher is better. Compares signal strength to noise.</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{mse_formatted}</div>
            <div class="metric-label">Mean Squared Error</div>
            <div class="metric-description">Lower is better. Measures average squared difference.</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{lsd_formatted}</div>
            <div class="metric-label">Log-Spectral Distance</div>
            <div class="metric-description">Lower is better. Measures spectral differences.</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{histogram_corr_formatted}</div>
            <div class="metric-label">Histogram Correlation</div>
            <div class="metric-description">Closer to 1 is better. Measures statistical similarity.</div>
        </div>
    </div>
    
    <div class="quality-assessment">
        <h3>Quality Assessment</h3>
        <p>{quality_text}</p>
    </div>
    
    <div class="additional-info">
        <h3>Audio File Information</h3>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Duration:</span> {duration_formatted}
            </div>
            <div class="info-item">
                <span class="info-label">Sample Rate:</span> {metrics.sample_rate} Hz
            </div>
            <div class="info-item">
                <span class="info-label">Channels:</span> {metrics.channels} ({'Stereo' if metrics.channels > 1 else 'Mono'})
            </div>
        </div>
    </div>
    
    <h2>Histogram Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Histogram</h3>
            <img src="{visualization_files['histogram_orig']}" alt="Original Audio Histogram">
        </div>
        <div class="plot">
            <h3>Stego Audio Histogram</h3>
            <img src="{visualization_files['histogram_stego']}" alt="Stego Audio Histogram">
        </div>
    </div>
    
    <div class="plot-container">
        <div class="plot">
            <h3>Histogram Comparison</h3>
            <img src="{visualization_files['histogram_comparison']}" alt="Histogram Comparison">
            <p>Histogram Correlation: {histogram_corr_formatted} (closer to 1.0 is better)</p>
        </div>
    </div>
    
    <h2>Waveform Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Waveform</h3>
            <img src="{visualization_files['waveform_orig']}" alt="Original Audio Waveform">
        </div>
        <div class="plot">
            <h3>Stego Audio Waveform</h3>
            <img src="{visualization_files['waveform_stego']}" alt="Stego Audio Waveform">
        </div>
    </div>
    
    <h2>Spectrogram Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Spectrogram</h3>
            <img src="{visualization_files['spectrogram_orig']}" alt="Original Audio Spectrogram">
        </div>
        <div class="plot">
            <h3>Stego Audio Spectrogram</h3>
            <img src="{visualization_files['spectrogram_stego']}" alt="Stego Audio Spectrogram">
        </div>
    </div>
    
    <h2>Frequency Spectrum Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Original Audio Frequency Spectrum</h3>
            <img src="{visualization_files['spectrum_orig']}" alt="Original Audio Frequency Spectrum">
        </div>
        <div class="plot">
            <h3>Stego Audio Frequency Spectrum</h3>
            <img src="{visualization_files['spectrum_stego']}" alt="Stego Audio Frequency Spectrum">
        </div>
    </div>
    
    <h2>Difference Analysis</h2>
    <div class="plot-container">
        <div class="plot">
            <h3>Difference Waveform (Amplified)</h3>
            <img src="{visualization_files['difference']}" alt="Difference Waveform">
            <p>Note: Differences are amplified by 50x for visibility</p>
        </div>
    </div>
    
    <footer>
        <p>Transform Domain Steganography Analysis Tool</p>
        <p><small>Generated on {current_date}</small></p>
    </footer>
</body>
</html>
"""
        
        # Write HTML to file
        output_path = os.path.join(self.temp_dir, output_filename)
        with open(output_path, "w") as f:
            f.write(html_content)
        
        return output_path

# Update the app.py to use this class instead of the individual functions
def update_app_py():
    # Import the new AudioAnalyzer class in app.py
    # Replace individual functions with AudioAnalyzer methods
    pass
    
if __name__ == "__main__":
    # Simple test code
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Audio Analysis Tool")
    parser.add_argument("original", help="Path to original audio file")
    parser.add_argument("stego", help="Path to stego audio file")
    parser.add_argument("--output", "-o", help="Output directory for results")
    
    args = parser.parse_args()
    
    output_dir = args.output if args.output else None
    
    analyzer = AudioAnalyzer(temp_dir=output_dir)
    
    print(f"Analyzing audio files...")
    result = analyzer.analyze_audio_pair(args.original, args.stego)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
        
    print(f"Analysis complete!")
    print(f"SNR: {result['metrics']['SNR']:.2f} dB")
    print(f"PSNR: {result['metrics']['PSNR']:.2f} dB")
    print(f"MSE: {result['metrics']['MSE']:.8f}")
    print(f"Histogram Correlation: {result['metrics']['histogram_correlation']:.4f}")
    print(f"Report saved to: {result['report_path']}")
