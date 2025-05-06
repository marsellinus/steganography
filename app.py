import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import math
import logging
import sys
try:
    from logging_config import configure_logging
except ImportError:
    # Simple fallback if the module is not found
    def configure_logging(app):
        return app

from dct_stego import DCTSteganography
from wavelet_stego import WaveletSteganography
from dft_stego import DFTSteganography
from svd_stego import SVDSteganography
from lbp_stego import LBPSteganography
from audio_dct_stego import AudioDCTSteganography
from audio_wavelet_stego import AudioWaveletSteganography
from unicode_handler import text_to_binary_unicode, binary_to_text_unicode, sanitize_text
from binary_decoder import binary_to_text
from audio_analyzer import AudioAnalyzer
from image_analyzer import ImageAnalyzer  # Add this import

# Make sure 'templates' folder exists and is properly detected
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
app.config['TEMP_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp'}
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload size (ditingkatkan dari 16MB)

# Update the app configuration
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_change_this_in_production')

# Configure session to use filesystem instead of signed cookies
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Initialize extensions
if 'SESSION_TYPE' in app.config:
    from flask_session import Session
    Session(app)

# Create necessary folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

app = configure_logging(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'cover_image' not in request.files:
            flash('No file selected')
            return redirect(request.url)
            
        file = request.files['cover_image']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if not allowed_file(file.filename):
            flash('Invalid file type. Please use PNG, JPG, JPEG, or BMP images.')
            return redirect(request.url)
            
        # Check if secret message exists
        secret_message = request.form.get('secret_message', '').strip()
        if not secret_message:
            flash('Please enter a secret message')
            return redirect(request.url)
            
        # Sanitize message to handle potentially corrupted Unicode
        secret_message = sanitize_text(secret_message)
        
        # Method selection
        method = request.form.get('method', 'DCT')
        # Embedding strength/quality 
        strength = float(request.form.get('strength', 10.0))
        
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            cover_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(cover_image_path)
            
            # Generate output filename
            output_filename = f"stego_{os.path.splitext(filename)[0]}.png"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Apply steganography based on selected method
            if method == 'DCT':
                stego = DCTSteganography(quantization_factor=strength)
                stego.encode(cover_image_path, secret_message, output_path)
            elif method == 'Wavelet':
                stego = WaveletSteganography(threshold=strength)
                stego.encode(cover_image_path, secret_message, output_path)
            elif method == 'DFT':
                stego = DFTSteganography(strength=strength)
                stego.encode(cover_image_path, secret_message, output_path)
            elif method == 'SVD':
                stego = SVDSteganography(strength=strength)
                stego.encode(cover_image_path, secret_message, output_path)
            else:  # LBP
                stego = LBPSteganography(strength=strength)
                stego.encode(cover_image_path, secret_message, output_path)
            
            # Calculate image quality metrics
            psnr, mse = calculate_image_quality(cover_image_path, output_path)
                
            # Redirect to result page with quality metrics
            return redirect(url_for('encode_result', filename=output_filename, psnr=psnr, mse=mse))
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(request.url)
    
    return render_template('encode.html')

@app.route('/encode/result')
def encode_result():
    filename = request.args.get('filename', '')
    if not filename:
        flash("No file specified")
        return redirect(url_for('encode'))
    
    # Get quality metrics if available
    psnr = request.args.get('psnr', 'Not calculated')
    mse = request.args.get('mse', 'Not calculated')
    
    return render_template('encode_result.html', filename=filename, psnr=psnr, mse=mse)

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'stego_image' not in request.files:
            flash('No file selected')
            return redirect(request.url)
            
        file = request.files['stego_image']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if not allowed_file(file.filename):
            flash('Invalid file type. Please use PNG, JPG, JPEG, or BMP images.')
            return redirect(request.url)
        
        # Method selection
        method = request.form.get('method', 'DCT')
        # Embedding strength/quality 
        strength = float(request.form.get('strength', 10.0))
        
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            stego_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(stego_image_path)
            
            # Apply steganography decoding based on selected method
            if method == 'DCT':
                stego = DCTSteganography(quantization_factor=strength)
                message = stego.decode(stego_image_path)
            elif method == 'Wavelet':
                stego = WaveletSteganography(threshold=strength)
                message = stego.decode(stego_image_path)
            elif method == 'DFT':
                stego = DFTSteganography(strength=strength)
                message = stego.decode(stego_image_path)
            elif method == 'SVD':
                stego = SVDSteganography(strength=strength)
                message = stego.decode(stego_image_path)
            else:  # LBP
                stego = LBPSteganography(strength=strength)
                message = stego.decode(stego_image_path)
            
            # Only consider completely empty messages as a failure
            # A message with just whitespace is still a valid result
            if message is None:
                flash("No hidden message found or unable to decode properly")
                return redirect(request.url)
                
            # Render result with extracted message
            return render_template('decode_result.html', message=message, filename=filename)
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(request.url)
    
    return render_template('decode.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    if request.method == 'POST':
        # Check if files are uploaded
        if 'original_image' not in request.files or 'stego_image' not in request.files:
            flash('Please select both original and stego images')
            return redirect(request.url)
        
        original_file = request.files['original_image']
        stego_file = request.files['stego_image']
        
        # Check if filenames are empty
        if original_file.filename == '' or stego_file.filename == '':
            flash('Please select both original and stego images')
            return redirect(request.url)
        
        # Process the uploaded files
        if original_file and stego_file:
            # Save uploaded files to temp directory
            original_path = os.path.join(app.config['TEMP_FOLDER'], secure_filename(original_file.filename))
            stego_path = os.path.join(app.config['TEMP_FOLDER'], secure_filename(stego_file.filename))
            
            original_file.save(original_path)
            stego_file.save(stego_path)
            
            try:
                # Analyze images
                analyzer = ImageAnalyzer(temp_dir=app.config['TEMP_FOLDER'])
                
                # Generate difference image directly to ensure it's created
                diff_path = analyzer.generate_difference_image(
                    original_path,
                    stego_path,
                    amplification=50,
                    filename=f"diff_{secure_filename(original_file.filename)}"
                )
                
                # Now run the full analysis
                result = analyzer.analyze_image_pair(original_path, stego_path)
                
                if "error" in result:
                    flash(f"Analysis error: {result['error']}")
                    return redirect(url_for('analyze'))
                
                # Process results
                metrics = result.get("metrics", {})
                visualizations = result.get("visualizations", {})
                
                # Add difference image if it wasn't in the visualizations
                if 'difference' not in visualizations and diff_path:
                    visualizations['difference'] = diff_path
                
                # Ensure all paths are basename only for session storage
                visualizations = {k: os.path.basename(v) for k, v in visualizations.items()}
                
                # Store in session
                session['metrics'] = metrics
                session['visualizations'] = visualizations
                session['original_filename'] = os.path.basename(original_path)
                session['stego_filename'] = os.path.basename(stego_path)
                session['original_img'] = visualizations.get('original', '')
                session['stego_img'] = visualizations.get('stego', '')
                session['dimensions'] = f"{metrics['dimensions'][0]} × {metrics['dimensions'][1]} px" if 'dimensions' in metrics else 'Unknown'
                session['psnr'] = float(metrics.get('psnr', 0))
                session['ssim'] = float(metrics.get('ssim', 0))
                
                if "pdf_report_path" in result:
                    session['pdf_report_path'] = os.path.basename(result["pdf_report_path"])
                
                return redirect(url_for('analyze_result'))
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                flash(f"Error during analysis: {str(e)}")
                return redirect(url_for('analyze'))

    return render_template('analyze.html')

@app.route('/analyze_result')
def analyze_result():
    """Display the results of image analysis"""
    # Get data from session
    metrics = session.get('metrics', {})
    visualizations = session.get('visualizations', {})
    pdf_report_filename = session.get('pdf_report_path', '')
    
    # Debug info
    print("Visualizations in session:", visualizations)
    print("Difference image:", visualizations.get('difference', 'Not available'))
    
    # Return template with data
    return render_template('analyze_result.html',
                          psnr=metrics.get('psnr', 'Not calculated'),
                          ssim=metrics.get('ssim', 'Not calculated'),
                          mse=metrics.get('mse', 'Not calculated'),
                          dimensions=metrics.get('dimensions', (0, 0)),
                          color_mode=metrics.get('color_mode', 'Unknown'),
                          quality_rating=metrics.get('quality_rating', 'Unknown'),
                          quality_color=metrics.get('quality_color', 'gray'),
                          unique_colors_orig=metrics.get('unique_colors_orig', 'Unknown'),
                          unique_colors_stego=metrics.get('unique_colors_stego', 'Unknown'),
                          original=visualizations.get('original', ''),
                          stego=visualizations.get('stego', ''),
                          difference=visualizations.get('difference', ''),
                          histogram_comparison=visualizations.get('histogram_comparison', ''),
                          pdf_report_filename=pdf_report_filename)

@app.route('/interactive_compare')
def interactive_compare():
    """Interactive side-by-side comparison of original and stego images"""
    original_img = session.get('original_img', '')
    stego_img = session.get('stego_img', '')
    original_filename = session.get('original_filename', 'Unknown')
    stego_filename = session.get('stego_filename', 'Unknown')
    dimensions = session.get('dimensions', 'Unknown')
    psnr = session.get('psnr', 0)
    ssim = session.get('ssim', 0)
    
    if not original_img or not stego_img:
        flash("No comparison images found in session. Please analyze images first.")
        return redirect(url_for('analyze'))
    
    return render_template('interactive_compare.html',
                         original_img=original_img,
                         stego_img=stego_img,
                         original_filename=original_filename,
                         stego_filename=stego_filename,
                         dimensions=dimensions,
                         psnr=psnr,
                         ssim=ssim)

@app.route('/audio/encode', methods=['GET', 'POST'])
def audio_encode():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'cover_audio' not in request.files:
            flash('No audio file selected')
            return redirect(request.url)
            
        file = request.files['cover_audio']
        if file.filename == '':
            flash('No audio file selected')
            return redirect(request.url)
            
        # Allow WAV, FLAC and other audio formats
        allowed_audio_extensions = {'wav', 'flac', 'mp3', 'ogg'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else None
        if not file_ext or file_ext not in allowed_audio_extensions:
            flash('Invalid file type. Please use WAV, FLAC, MP3 or OGG audio files.')
            return redirect(request.url)
            
        # Check if secret message exists
        secret_message = request.form.get('secret_message', '').strip()
        if not secret_message:
            flash('Please enter a secret message')
            return redirect(request.url)
        
        # Method selection
        method = request.form.get('method', 'DCT')
        # Embedding strength
        strength = float(request.form.get('strength', 0.1))
        
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            cover_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(cover_audio_path)
            
            # Generate output filename - always save as WAV
            base_name = os.path.splitext(filename)[0]
            output_filename = f"stego_{base_name}.wav"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Apply audio steganography based on selected method
            if method == 'DCT':
                stego = AudioDCTSteganography(quantization_factor=strength)
                stego.encode(cover_audio_path, secret_message, output_path)
            else:  # Wavelet
                stego = AudioWaveletSteganography(threshold=strength)
                stego.encode(cover_audio_path, secret_message, output_path)
                
            # Redirect to result page
            return redirect(url_for('audio_encode_result', filename=output_filename))
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(request.url)
    
    return render_template('audio_encode.html')

@app.route('/audio/encode/result')
def audio_encode_result():
    filename = request.args.get('filename', '')
    if not filename:
        flash("No file specified")
        return redirect(url_for('audio_encode'))
    
    return render_template('audio_encode_result.html', filename=filename)

@app.route('/audio/decode', methods=['GET', 'POST'])
def audio_decode():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'stego_audio' not in request.files:
            flash('No audio file selected')
            return redirect(request.url)
            
        file = request.files['stego_audio']
        if file.filename == '':
            flash('No audio file selected')
            return redirect(request.url)
            
        # Method selection
        method = request.form.get('method', 'DCT')
        # Extraction strength
        strength = float(request.form.get('strength', 0.1))
        
        try:
            # Save the uploaded file
            filename = secure_filename(file.filename)
            stego_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(stego_audio_path)
            
            # Apply audio steganography decoding based on selected method
            if method == 'DCT':
                stego = AudioDCTSteganography(quantization_factor=strength)
                message = stego.decode(stego_audio_path)
            else:  # Wavelet
                stego = AudioWaveletSteganography(threshold=strength)
                message = stego.decode(stego_audio_path)
            
            # Only consider completely empty messages as a failure
            if message is None:
                flash("No hidden message found or unable to decode properly")
                return redirect(request.url)
                
            # Render result with extracted message
            return render_template('audio_decode_result.html', message=message, filename=filename)
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(request.url)
    
    return render_template('audio_decode.html')

@app.route('/audio/analyze', methods=['GET', 'POST'])
def audio_analyze():
    """Audio analysis page for comparing original and stego audio"""
    if request.method == 'POST':
        # Check if files were uploaded
        if 'original_audio' not in request.files or 'stego_audio' not in request.files:
            flash('Please upload both original and stego audio files')
            return redirect(request.url)
            
        original_file = request.files['original_audio']
        stego_file = request.files['stego_audio']
        
        if original_file.filename == '' or stego_file.filename == '':
            flash('Please upload both original and stego audio files')
            return redirect(request.url)
            
        # Get selected analysis types
        analysis_types = request.form.getlist('analysis_type[]')
        if not analysis_types:
            analysis_types = ['waveform', 'spectrogram', 'spectrum', 'quality', 'histogram']  # Default to all
            
        try:
            # Save the uploaded files
            original_filename = secure_filename(original_file.filename)
            stego_filename = secure_filename(stego_file.filename)
            
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
            
            original_file.save(original_path)
            stego_file.save(stego_path)
            
            # Set output directory to temp folder
            output_dir = app.config['TEMP_FOLDER']
            
            # Generate unique base name for output files
            import uuid
            base_name = f"audio_analysis_{uuid.uuid4().hex[:8]}"
            
            # Create audio analyzer instance
            analyzer = AudioAnalyzer(temp_dir=output_dir)
            
            # Perform the analysis
            result = analyzer.analyze_audio_pair(original_path, stego_path, base_name)
            
            if "error" in result:
                flash(f"Error in audio analysis: {result['error']}")
                return redirect(request.url)
                
            # Get file paths from result
            visualizations = result['visualizations']
            metrics = result['metrics']
            report_path = result['report_path']
            pdf_report_path = result.get("pdf_report_path", "")
            
            # Get filenames only (not full paths)
            waveform_orig = os.path.basename(visualizations['waveform_orig'])
            waveform_stego = os.path.basename(visualizations['waveform_stego'])
            waveform_diff = os.path.basename(visualizations['difference'])
            spectrogram_orig = os.path.basename(visualizations['spectrogram_orig'])
            spectrogram_stego = os.path.basename(visualizations['spectrogram_stego'])
            spectrum_orig = os.path.basename(visualizations['spectrum_orig'])
            spectrum_stego = os.path.basename(visualizations['spectrum_stego'])
            histogram_orig = os.path.basename(visualizations['histogram_orig'])
            histogram_stego = os.path.basename(visualizations['histogram_stego'])
            histogram_comparison = os.path.basename(visualizations['histogram_comparison'])
            
            # Create metrics object for the template
            metrics_obj = type('Metrics', (), {
                'snr': metrics['SNR'],
                'psnr': metrics['PSNR'],
                'lsd': metrics['LSD'],
                'mse': metrics['MSE'],
                'histogram_correlation': metrics['histogram_correlation']
            })
            
            # Get report filename
            report_filename = os.path.basename(report_path)
            pdf_report_filename = os.path.basename(pdf_report_path) if pdf_report_path else ""
            
            # Render the results
            return render_template('audio_analyze_result.html',
                                  metrics=metrics_obj,
                                  quality_text=metrics['quality_rating'],
                                  quality_color=metrics['quality_color'],
                                  waveform_orig=waveform_orig,
                                  waveform_stego=waveform_stego,
                                  waveform_diff=waveform_diff,
                                  spectrogram_orig=spectrogram_orig,
                                  spectrogram_stego=spectrogram_stego,
                                  spectrum_orig=spectrum_orig,
                                  spectrum_stego=spectrum_stego,
                                  histogram_orig=histogram_orig,
                                  histogram_stego=histogram_stego,
                                  histogram_comparison=histogram_comparison,
                                  has_waveform_analysis='waveform' in analysis_types,
                                  has_spectrogram_analysis='spectrogram' in analysis_types,
                                  has_spectrum_analysis='spectrum' in analysis_types,
                                  has_histogram_analysis='histogram' in analysis_types,
                                  report_filename=report_filename,
                                  pdf_report_filename=pdf_report_filename,
                                  report_path=report_path)
                                  
        except Exception as e:
            flash(f"Error analyzing audio: {str(e)}")
            return redirect(request.url)
    
    return render_template('audio_analyze.html')

@app.route('/binary', methods=['GET', 'POST'])
def binary_decode():
    """Binary decoder page for converting binary to text"""
    decoded_text = None
    binary_input = None
    
    if request.method == 'POST':
        binary_input = request.form.get('binary_input', '')
        try_multiple = 'try_multiple_encodings' in request.form
        
        # Clean binary input (keep only 0s, 1s and whitespace)
        clean_binary = ''.join(c for c in binary_input if c in '01 \n\t')
        binary_only = ''.join(c for c in clean_binary if c in '01')
        
        if not binary_only:
            flash("No valid binary data found. Please enter a valid binary string.")
            return render_template('binary_decoder.html')
        
        try:
            if try_multiple:
                # Use enhanced Unicode handler for better encoding support
                decoded_text = binary_to_text_unicode(binary_only)
            else:
                # Use basic decoder
                decoded_text = binary_to_text(binary_only)
        except Exception as e:
            flash(f"Error decoding binary: {str(e)}")
    
    return render_template('binary_decoder.html', decoded_text=decoded_text, binary_input=binary_input)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve files from the UPLOAD_FOLDER directory"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/outputs/<filename>')
def output_file(filename):
    """Serve files from the OUTPUT_FOLDER directory"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/temp/<filename>')
def temp_file(filename):
    """Serve temporary files"""
    return send_from_directory(app.config['TEMP_FOLDER'], filename)

def calculate_image_quality(original_path, stego_path):
    """Calculate PSNR and MSE between two images"""
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
        
    return round(psnr, 2), round(mse, 4)

def calculate_histogram_correlation(original_path, stego_path):
    """Calculate correlation between histograms of two images"""
    from scipy.stats import pearsonr
    
    original = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)
    
    # Resize if dimensions don't match
    if original.shape != stego.shape:
        stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
    
    # Calculate histograms
    hist_original = cv2.calcHist([original], [0], None, [256], [0, 256])
    hist_stego = cv2.calcHist([stego], [0], None, [256], [0, 256])
    
    # Calculate Pearson correlation
    correlation, _ = pearsonr(hist_original.flatten(), hist_stego.flatten())
    
    return round(correlation, 4)

def create_difference_image(original_path, stego_path, output_path):
    """Create and save image showing differences between original and stego images"""
    original = cv2.imread(original_path)
    stego = cv2.imread(stego_path)
    
    # Resize if dimensions don't match
    if original.shape != stego.shape:
        stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
    
    # Calculate absolute difference and amplify for visibility
    diff = cv2.absdiff(original, stego)
    diff_amplified = cv2.convertScaleAbs(diff, alpha=10)  # Amplify by factor of 10 for better visualization
    
    # Apply colormap for better visualization
    diff_color = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)
    
    # Save difference image
    cv2.imwrite(output_path, diff_color)
    
    return output_path

if __name__ == '__main__':
    print("="*80)
    print("Transform Domain Steganography Web Application")
    print("="*80)
    print("Server is starting...")
    print("Open your browser and navigate to: http://127.0.0.1:5000/")
    print("Press Ctrl+C to stop the server")
    print("="*80)
    
    try:
        app.logger.info("Starting the application")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        app.logger.error(f"Error starting the application: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)
