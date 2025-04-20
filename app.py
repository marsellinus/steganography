import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import math

from dct_stego import DCTSteganography
from wavelet_stego import WaveletSteganography
from reliable_stego import ReliableSteganography
from audio_dct_stego import AudioDCTSteganography
from audio_wavelet_stego import AudioWaveletSteganography
from simple_dft_stego import SimpleDFTSteganography
from svd_stego import SVDSteganography
from lbp_stego import LBPSteganography

# Make sure 'templates' folder exists and is properly detected
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
app.config['TEMP_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp'}
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Increased to 32MB max upload size

# Create necessary folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

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
                stego = SimpleDFTSteganography(strength=strength)
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
            
            # Helper function to check if a message is valid
            def is_valid_message(msg):
                if not msg:
                    return False
                # Check if message has enough printable characters
                printable_chars = 0
                for char in msg:
                    if 32 <= ord(char) <= 126:  # printable ASCII
                        printable_chars += 1
                return printable_chars > len(msg) * 0.7  # At least 70% should be printable
            
            # Try a range of strength values if decoding fails
            message = None
            decode_error = None
            found_strength = None
            
            try:
                # First try with the specified strength
                if method == 'DCT':
                    stego = DCTSteganography(quantization_factor=strength)
                    message = stego.decode(stego_image_path)
                elif method == 'Wavelet':
                    stego = WaveletSteganography(threshold=strength)
                    message = stego.decode(stego_image_path)
                elif method == 'DFT':
                    stego = SimpleDFTSteganography(strength=strength)
                    message = stego.decode(stego_image_path)
                elif method == 'SVD':
                    stego = SVDSteganography(strength=strength)
                    message = stego.decode(stego_image_path)
                elif method == 'LBP':
                    stego = LBPSteganography(strength=strength)
                    message = stego.decode(stego_image_path)
                
                # Validate the message
                if message and not is_valid_message(message):
                    print("Message found but seems corrupt, trying auto-detection...")
                    message = None  # Trigger auto-detection
                
                # If decoding failed, try with different strength values
                if message is None or message.strip() == "":
                    # For DFT, try these specific values known to work well
                    if method == 'DFT':
                        test_strengths = [1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 20.0]
                    else:
                        test_strengths = [1.0, 5.0, 10.0, 15.0, 20.0, 25.0]
                    
                    for test_strength in test_strengths:
                        if abs(test_strength - strength) < 0.1:
                            continue  # Skip if very close to the original strength
                        
                        try:
                            if method == 'DFT':
                                stego = SimpleDFTSteganography(strength=test_strength)
                                test_message = stego.decode(stego_image_path)
                                
                                if test_message and is_valid_message(test_message):
                                    message = test_message
                                    found_strength = test_strength
                                    flash(f"Successfully decoded using strength = {test_strength}")
                                    break
                        except Exception:
                            pass  # Ignore errors in automatic strength detection
                            
            except Exception as e:
                decode_error = str(e)
            
            # Only consider completely empty messages or invalid messages as failures
            if message is None or message.strip() == "" or not is_valid_message(message):
                if decode_error:
                    flash(f"Decoding error: {decode_error}. Try adjusting the strength parameter.")
                else:
                    flash("No hidden message found or message corrupted. Try adjusting the strength parameter.")
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
        # Check if original image was uploaded
        if 'original_image' not in request.files:
            flash('Original image not selected')
            return redirect(request.url)
            
        # Check if stego image was uploaded
        if 'stego_image' not in request.files:
            flash('Stego image not selected')
            return redirect(request.url)
        
        original_file = request.files['original_image']
        stego_file = request.files['stego_image']
        
        if original_file.filename == '' or stego_file.filename == '':
            flash('Both images must be selected')
            return redirect(request.url)
            
        if not (allowed_file(original_file.filename) and allowed_file(stego_file.filename)):
            flash('Invalid file type. Please use PNG, JPG, JPEG, or BMP images.')
            return redirect(request.url)
        
        try:
            # Save the uploaded files
            original_filename = secure_filename(original_file.filename)
            stego_filename = secure_filename(stego_file.filename)
            
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            stego_path = os.path.join(app.config['UPLOAD_FOLDER'], stego_filename)
            
            original_file.save(original_path)
            stego_file.save(stego_path)
            
            # Generate difference image
            diff_filename = f"diff_{os.path.splitext(original_filename)[0]}.png"
            diff_path = os.path.join(app.config['TEMP_FOLDER'], diff_filename)
            
            # Create and save difference image
            create_difference_image(original_path, stego_path, diff_path)
            
            # Calculate image quality metrics
            psnr, mse = calculate_image_quality(original_path, stego_path)
            
            # Calculate histogram correlation
            try:
                from scipy.stats import pearsonr
                correlation = calculate_histogram_correlation(original_path, stego_path)
            except:
                correlation = "Not available (scipy required)"
                
            # Render analysis results
            return render_template(
                'analyze_result.html',
                original_filename=original_filename,
                stego_filename=stego_filename,
                diff_filename=diff_filename,
                psnr=psnr,
                mse=mse,
                correlation=correlation
            )
            
        except Exception as e:
            flash(f"Analysis error: {str(e)}")
            return redirect(request.url)
    
    return render_template('analyze.html')

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
            message = None
            try:
                if method == 'DCT':
                    stego = AudioDCTSteganography(quantization_factor=strength)
                    message = stego.decode(stego_audio_path)
                else:  # Wavelet
                    stego = AudioWaveletSteganography(threshold=strength)
                    message = stego.decode(stego_audio_path)
            except Exception as decode_error:
                flash(f"Decoding error: {str(decode_error)}. Try adjusting the strength parameter.")
                return redirect(request.url)
            
            # Only consider completely empty messages as a failure
            if message is None:
                flash("No hidden message found. Try adjusting the strength parameter to match the encoding strength.")
                return redirect(request.url)
                
            # Render result with extracted message
            return render_template('audio_decode_result.html', message=message, filename=filename)
            
        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(request.url)
    
    return render_template('audio_decode.html')

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

@app.route('/generate_histogram/<filename>')
def generate_histogram(filename):
    """Generate histogram data for the given image"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'})
    
    try:
        img = cv2.imread(file_path)
        hist_data = {
            'r': cv2.calcHist([img], [0], None, [256], [0, 256]).flatten().tolist(),
            'g': cv2.calcHist([img], [1], None, [256], [0, 256]).flatten().tolist(),
            'b': cv2.calcHist([img], [2], None, [256], [0, 256]).flatten().tolist(),
        }
        return jsonify(hist_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/outputs/<filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/temp/<filename>')
def temp_file(filename):
    return send_from_directory(app.config['TEMP_FOLDER'], filename)

if __name__ == '__main__':
    print("Flask app starting on http://127.0.0.1:5000/")
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    app.run(debug=True)
