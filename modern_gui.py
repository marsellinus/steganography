import PySimpleGUI as sg
import os
import threading
import time
from PIL import Image, ImageTk
import io
import cv2
import numpy as np
import math

# Import steganography classes
from dct_stego import DCTSteganography
from wavelet_stego import WaveletSteganography
from dft_stego import DFTSteganography
from svd_stego import SVDSteganography
from lbp_stego import LBPSteganography
from audio_dct_stego import AudioDCTSteganography
from audio_wavelet_stego import AudioWaveletSteganography

# Global settings
APP_NAME = "Transform Domain Steganography"
THEME = "DarkBlue"  # Try alternatives: DarkTeal9, DarkGrey12, DarkAmber
MAX_IMAGE_SIZE = (400, 300)  # For display in GUI

# Make sure necessary directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('outputs', exist_ok=True)
os.makedirs('temp', exist_ok=True)

def resize_image(image_path, max_size=MAX_IMAGE_SIZE):
    """Resize image for display in the GUI"""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size)
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        return bio.getvalue()
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def image_to_data(image_path):
    """Convert image to bytes for PySimpleGUI"""
    return resize_image(image_path)

def calculate_image_quality(original_path, stego_path):
    """Calculate PSNR and MSE between two images"""
    original = cv2.imread(original_path)
    stego = cv2.imread(stego_path)
    
    if original.shape != stego.shape:
        stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
    
    mse = np.mean((original - stego) ** 2)
    if mse == 0:
        psnr = float('inf')
    else:
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        
    return round(psnr, 2), round(mse, 4)

def binary_to_text(binary_str):
    """Convert a binary string to ASCII text"""
    if not binary_str:
        return ""
    
    # Split into 8-bit chunks and convert
    result = ""
    for i in range(0, len(binary_str), 8):
        if i + 8 > len(binary_str):
            break
        byte = binary_str[i:i+8]
        try:
            char_code = int(byte, 2)
            if 32 <= char_code <= 126 or char_code in [9, 10, 13]:  # Printable ASCII + control chars
                result += chr(char_code)
            else:
                result += '�'
        except:
            break
    
    return result

def create_encode_tab():
    """Create the encode tab layout"""
    method_options = [
        "DCT (Discrete Cosine Transform)",
        "Wavelet Transform",
        "DFT (Discrete Fourier Transform)",
        "SVD (Singular Value Decomposition)",
        "LBP (Local Binary Pattern)"
    ]
    
    file_column = [
        [sg.Text("Cover Image:")],
        [sg.Input(key="-COVER-PATH-", size=(45, 1)), 
         sg.FileBrowse(file_types=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")))],
        [sg.Text("Cover Image Preview:")],
        [sg.Image(key="-COVER-IMAGE-", size=MAX_IMAGE_SIZE)],
    ]
    
    input_column = [
        [sg.Text("Secret Message:")],
        [sg.Multiline(key="-SECRET-MESSAGE-", size=(45, 10), font=("Courier", 10))],
        [sg.Text("Transform Method:"), 
         sg.Combo(method_options, default_value=method_options[0], key="-ENCODE-METHOD-", readonly=True, size=(30, 1))],
        [sg.Text("Embedding Strength:"), 
         sg.Slider(range=(1, 50), default_value=10, orientation="h", key="-ENCODE-STRENGTH-", size=(35, 15))],
        [sg.Button("Encode", key="-ENCODE-BUTTON-", size=(15, 1)), 
         sg.Button("Clear", key="-ENCODE-CLEAR-", size=(15, 1))],
        [sg.Text("", key="-ENCODE-STATUS-", size=(40, 1), text_color="yellow")]
    ]
    
    output_column = [
        [sg.Text("Stego Image:")],
        [sg.Image(key="-STEGO-IMAGE-", size=MAX_IMAGE_SIZE)],
        [sg.Text("Output Path:"), 
         sg.Input(key="-OUTPUT-PATH-", size=(45, 1)), 
         sg.SaveAs("Save As...", file_types=(("PNG Files", "*.png"), ("BMP Files", "*.bmp")))],
        [sg.Text("Quality Metrics:")],
        [sg.Text("PSNR:"), sg.Text("N/A", key="-PSNR-")],
        [sg.Text("MSE:"), sg.Text("N/A", key="-MSE-")]
    ]
    
    layout = [
        [sg.Column(file_column), sg.VSeperator(), sg.Column(input_column)],
        [sg.HorizontalSeparator()],
        [sg.Column(output_column)]
    ]
    
    return layout

def create_decode_tab():
    """Create the decode tab layout"""
    method_options = [
        "DCT (Discrete Cosine Transform)",
        "Wavelet Transform",
        "DFT (Discrete Fourier Transform)",
        "SVD (Singular Value Decomposition)",
        "LBP (Local Binary Pattern)"
    ]
    
    layout = [
        [sg.Text("Stego Image:"), 
         sg.Input(key="-STEGO-PATH-", size=(45, 1)), 
         sg.FileBrowse(file_types=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")))],
        [sg.Image(key="-DECODE-IMAGE-", size=MAX_IMAGE_SIZE)],
        [sg.Text("Transform Method:"), 
         sg.Combo(method_options, default_value=method_options[0], key="-DECODE-METHOD-", readonly=True)],
        [sg.Text("Extraction Strength:"), 
         sg.Slider(range=(1, 50), default_value=10, orientation="h", key="-DECODE-STRENGTH-")],
        [sg.Button("Decode", key="-DECODE-BUTTON-", size=(15, 1)), 
         sg.Button("Clear", key="-DECODE-CLEAR-", size=(15, 1)), 
         sg.Button("Show Binary", key="-SHOW-BINARY-", size=(15, 1))],
        [sg.Text("", key="-DECODE-STATUS-", size=(45, 1), text_color="yellow")],
        [sg.Text("Extracted Message:")],
        [sg.Multiline(key="-EXTRACTED-MESSAGE-", size=(80, 10), font=("Courier", 10), disabled=True)],
        [sg.Button("Copy to Clipboard", key="-COPY-MESSAGE-")]
    ]
    
    return layout

def create_analyze_tab():
    """Create the analyze tab layout"""
    layout = [
        [sg.Text("Original Image:"), 
         sg.Input(key="-ORIGINAL-PATH-", size=(45, 1)), 
         sg.FileBrowse(file_types=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")))],
        [sg.Text("Stego Image:"), 
         sg.Input(key="-COMPARE-STEGO-PATH-", size=(45, 1)), 
         sg.FileBrowse(file_types=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All Files", "*.*")))],
        [sg.Button("Compare Images", key="-COMPARE-BUTTON-"), 
         sg.Button("Calculate PSNR", key="-CALC-PSNR-"), 
         sg.Button("Show Histograms", key="-SHOW-HIST-")],
        [sg.Text("Image Comparison:"), sg.Text("", key="-ANALYZE-STATUS-", text_color="yellow")],
        [sg.Column([
            [sg.Image(key="-ORIGINAL-PREVIEW-", size=(200, 150))],
            [sg.Text("Original Image")]
        ]), sg.Column([
            [sg.Image(key="-STEGO-PREVIEW-", size=(200, 150))],
            [sg.Text("Stego Image")]
        ]), sg.Column([
            [sg.Image(key="-DIFF-PREVIEW-", size=(200, 150))],
            [sg.Text("Difference (5x amplified)")]
        ])],
        [sg.Text("Analysis Results:")],
        [sg.Multiline(key="-ANALYSIS-RESULTS-", size=(80, 10), font=("Courier", 10), disabled=True)]
    ]
    
    return layout

def create_audio_tab():
    """Create the audio steganography tab layout"""
    method_options = [
        "DCT (Discrete Cosine Transform)", 
        "Wavelet Transform"
    ]
    
    encode_frame = [
        [sg.Text("Cover Audio:"), 
         sg.Input(key="-AUDIO-COVER-PATH-", size=(45, 1)), 
         sg.FileBrowse(file_types=(("Audio Files", "*.wav;*.mp3;*.flac;*.ogg"), ("All Files", "*.*")))],
        [sg.Text("Secret Message:")],
        [sg.Multiline(key="-AUDIO-MESSAGE-", size=(45, 5))],
        [sg.Text("Transform Method:"), 
         sg.Combo(method_options, default_value=method_options[0], key="-AUDIO-METHOD-", readonly=True)],
        [sg.Text("Embedding Strength:"), 
         sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution=0.01, orientation="h", key="-AUDIO-STRENGTH-")],
        [sg.Button("Encode Audio", key="-AUDIO-ENCODE-"), 
         sg.Button("Play Original", key="-PLAY-ORIGINAL-"), 
         sg.Button("Play Stego", key="-PLAY-STEGO-", disabled=True)],
        [sg.Text("", key="-AUDIO-ENCODE-STATUS-", size=(45, 1), text_color="yellow")],
        [sg.Text("Output Path:"), 
         sg.Input(key="-AUDIO-OUTPUT-PATH-", size=(45, 1)), 
         sg.SaveAs("Save As...", file_types=(("WAV Files", "*.wav"),))]
    ]
    
    decode_frame = [
        [sg.Text("Stego Audio:"), 
         sg.Input(key="-AUDIO-STEGO-PATH-", size=(45, 1)), 
         sg.FileBrowse(file_types=(("Audio Files", "*.wav"), ("All Files", "*.*")))],
        [sg.Text("Transform Method:"), 
         sg.Combo(method_options, default_value=method_options[0], key="-AUDIO-DECODE-METHOD-", readonly=True)],
        [sg.Text("Extraction Strength:"), 
         sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution=0.01, orientation="h", key="-AUDIO-DECODE-STRENGTH-")],
        [sg.Button("Decode Audio", key="-AUDIO-DECODE-"), 
         sg.Button("Play Audio", key="-PLAY-DECODE-")],
        [sg.Text("", key="-AUDIO-DECODE-STATUS-", size=(45, 1), text_color="yellow")],
        [sg.Text("Extracted Message:")],
        [sg.Multiline(key="-AUDIO-EXTRACTED-MESSAGE-", size=(45, 5), disabled=True)]
    ]
    
    layout = [
        [sg.Frame("Audio Encoding", encode_frame), sg.Frame("Audio Decoding", decode_frame)]
    ]
    
    return layout

def create_main_window():
    """Create the main application window"""
    sg.theme(THEME)
    
    # Menu definition
    menu_def = [
        ['File', ['Open', 'Save', '---', 'Exit']],
        ['Help', ['About']]
    ]
    
    # Main layout with tabs
    layout = [
        [sg.Menu(menu_def)],
        [sg.Text(APP_NAME, font=("Helvetica", 20), justification="center", expand_x=True)],
        [sg.TabGroup([
            [sg.Tab("Encode", create_encode_tab())],
            [sg.Tab("Decode", create_decode_tab())],
            [sg.Tab("Analyze", create_analyze_tab())],
            [sg.Tab("Audio", create_audio_tab())]
        ], key="-TAB-GROUP-", expand_x=True, expand_y=True)],
        [sg.Text("Status: Ready", key="-STATUS-"), 
         sg.ProgressBar(100, orientation="h", size=(20, 20), key="-PROGRESS-", visible=False)]
    ]
    
    window = sg.Window(APP_NAME, layout, resizable=True, finalize=True)
    
    return window

def encode_image_thread(window, values):
    """Thread function for encoding to keep UI responsive"""
    try:
        window["-ENCODE-STATUS-"].update("Processing...")
        window["-PROGRESS-"].update(visible=True)
        
        # Get inputs
        cover_path = values["-COVER-PATH-"]
        message = values["-SECRET-MESSAGE-"]
        method_full = values["-ENCODE-METHOD-"]
        method = method_full.split(" ")[0]  # Extract just the method name
        strength = values["-ENCODE-STRENGTH-"]
        output_path = values["-OUTPUT-PATH-"]
        
        if not output_path:
            output_path = os.path.join("outputs", f"stego_{os.path.basename(cover_path)}")
            
        # Create steganography object based on method
        if method == "DCT":
            stego = DCTSteganography(quantization_factor=strength)
        elif method == "Wavelet":
            stego = WaveletSteganography(threshold=strength)
        elif method == "DFT":
            stego = DFTSteganography(strength=strength)
        elif method == "SVD":
            stego = SVDSteganography(strength=strength)
        else:  # LBP
            stego = LBPSteganography(strength=strength)
            
        # Update progress
        window.write_event_value("-PROGRESS-UPDATE-", 30)
        
        # Encode message
        result_path = stego.encode(cover_path, message, output_path)
        
        window.write_event_value("-PROGRESS-UPDATE-", 70)
        
        # Calculate quality metrics
        psnr, mse = calculate_image_quality(cover_path, result_path)
        
        window.write_event_value("-PROGRESS-UPDATE-", 90)
        
        # Send result to the main thread
        result = {
            "path": result_path,
            "psnr": psnr,
            "mse": mse
        }
        window.write_event_value("-ENCODE-DONE-", result)
        
    except Exception as e:
        window.write_event_value("-ENCODE-ERROR-", str(e))

def decode_image_thread(window, values):
    """Thread function for decoding to keep UI responsive"""
    try:
        window["-DECODE-STATUS-"].update("Processing...")
        window["-PROGRESS-"].update(visible=True)
        
        # Get inputs
        stego_path = values["-STEGO-PATH-"]
        method_full = values["-DECODE-METHOD-"]
        method = method_full.split(" ")[0]  # Extract just the method name
        strength = values["-DECODE-STRENGTH-"]
        
        # Create steganography object based on method
        if method == "DCT":
            stego = DCTSteganography(quantization_factor=strength)
        elif method == "Wavelet":
            stego = WaveletSteganography(threshold=strength)
        elif method == "DFT":
            stego = DFTSteganography(strength=strength)
        elif method == "SVD":
            stego = SVDSteganography(strength=strength)
        else:  # LBP
            stego = LBPSteganography(strength=strength)
            
        window.write_event_value("-PROGRESS-UPDATE-", 50)
        
        # Decode message
        message = stego.decode(stego_path)
        
        window.write_event_value("-PROGRESS-UPDATE-", 100)
        
        # Store binary message for later use
        binary_message = ''.join(format(ord(c), '08b') for c in message) if message else ""
        
        # Send result to the main thread
        result = {
            "message": message,
            "binary": binary_message
        }
        window.write_event_value("-DECODE-DONE-", result)
        
    except Exception as e:
        window.write_event_value("-DECODE-ERROR-", str(e))

def compare_images_thread(window, values):
    """Thread function for image comparison"""
    try:
        window["-ANALYZE-STATUS-"].update("Processing...")
        window["-PROGRESS-"].update(visible=True)
        
        original_path = values["-ORIGINAL-PATH-"]
        stego_path = values["-COMPARE-STEGO-PATH-"]
        
        # Read images
        original = cv2.imread(original_path)
        stego = cv2.imread(stego_path)
        
        if original.shape != stego.shape:
            stego = cv2.resize(stego, (original.shape[1], original.shape[0]))
            
        window.write_event_value("-PROGRESS-UPDATE-", 30)
        
        # Calculate absolute difference
        diff = cv2.absdiff(original, stego)
        diff_amplified = cv2.convertScaleAbs(diff, alpha=5)  # Amplify 5x for visibility
        
        # Apply colormap for better visualization
        diff_color = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)
        
        # Save the difference image
        diff_path = os.path.join("temp", "diff_image.png")
        cv2.imwrite(diff_path, diff_color)
        
        window.write_event_value("-PROGRESS-UPDATE-", 60)
        
        # Calculate statistics
        mean_diff = np.mean(diff)
        max_diff = np.max(diff)
        std_dev = np.std(diff)
        
        # Calculate PSNR and MSE
        psnr, mse = calculate_image_quality(original_path, stego_path)
        
        window.write_event_value("-PROGRESS-UPDATE-", 90)
        
        # Prepare analysis results
        analysis_text = f"Image Comparison Results:\n\n"
        analysis_text += f"PSNR: {psnr:.2f} dB\n"
        analysis_text += f"MSE: {mse:.4f}\n"
        analysis_text += f"Mean Absolute Difference: {mean_diff:.4f}\n"
        analysis_text += f"Maximum Difference: {max_diff:.4f}\n"
        analysis_text += f"Standard Deviation: {std_dev:.4f}\n\n"
        
        if psnr > 40:
            quality = "Excellent - differences virtually imperceptible"
        elif psnr > 30:
            quality = "Good - differences hardly noticeable"
        elif psnr > 20:
            quality = "Acceptable - some visible differences"
        else:
            quality = "Poor - visible differences"
            
        analysis_text += f"Quality Assessment: {quality}"
        
        # Send result to the main thread
        result = {
            "original_path": original_path,
            "stego_path": stego_path,
            "diff_path": diff_path,
            "analysis": analysis_text
        }
        window.write_event_value("-COMPARE-DONE-", result)
        
    except Exception as e:
        window.write_event_value("-COMPARE-ERROR-", str(e))

def main():
    """Main application function"""
    window = create_main_window()
    
    # For storing binary message when showing binary representation
    binary_message = ""
    
    # Main event loop
    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
            
        # File menu events
        elif event == 'About':
            sg.popup("Transform Domain Steganography", 
                     "A tool for hiding messages in images and audio using transform domain techniques.\n\n"
                     "Supports: DCT, Wavelet, DFT, SVD, and LBP methods", 
                     title="About")
            
        # Encode tab events
        elif event == "-ENCODE-BUTTON-":
            if not values["-COVER-PATH-"]:
                sg.popup_error("Please select a cover image")
                continue
                
            if not values["-SECRET-MESSAGE-"].strip():
                sg.popup_error("Please enter a secret message")
                continue
                
            # Start encoding thread
            threading.Thread(target=encode_image_thread, args=(window, values), daemon=True).start()
            
        elif event == "-ENCODE-DONE-":
            result = values[event]
            window["-STEGO-IMAGE-"].update(data=image_to_data(result["path"]))
            window["-OUTPUT-PATH-"].update(result["path"])
            window["-PSNR-"].update(f"{result['psnr']} dB")
            window["-MSE-"].update(str(result["mse"]))
            window["-ENCODE-STATUS-"].update("Encoding completed successfully")
            window["-PROGRESS-"].update(visible=False)
            
        elif event == "-ENCODE-ERROR-":
            window["-ENCODE-STATUS-"].update(f"Error: {values[event]}")
            window["-PROGRESS-"].update(visible=False)
            sg.popup_error(f"Encoding failed: {values[event]}")
            
        elif event == "-ENCODE-CLEAR-":
            window["-SECRET-MESSAGE-"].update("")
            window["-COVER-PATH-"].update("")
            window["-COVER-IMAGE-"].update(data=None)
            window["-ENCODE-STATUS-"].update("")
            
        # Decode tab events
        elif event == "-DECODE-BUTTON-":
            if not values["-STEGO-PATH-"]:
                sg.popup_error("Please select a stego image")
                continue
                
            # Start decoding thread
            threading.Thread(target=decode_image_thread, args=(window, values), daemon=True).start()
            
        elif event == "-DECODE-DONE-":
            result = values[event]
            window["-EXTRACTED-MESSAGE-"].update(result["message"])
            window["-DECODE-STATUS-"].update("Decoding completed successfully")
            window["-PROGRESS-"].update(visible=False)
            binary_message = result["binary"]
            
        elif event == "-DECODE-ERROR-":
            window["-DECODE-STATUS-"].update(f"Error: {values[event]}")
            window["-PROGRESS-"].update(visible=False)
            sg.popup_error(f"Decoding failed: {values[event]}")
            
        elif event == "-DECODE-CLEAR-":
            window["-STEGO-PATH-"].update("")
            window["-DECODE-IMAGE-"].update(data=None)
            window["-EXTRACTED-MESSAGE-"].update("")
            window["-DECODE-STATUS-"].update("")
            
        elif event == "-SHOW-BINARY-":
            if binary_message:
                sg.popup_scrolled(binary_message, title="Binary Representation", size=(80, 20))
            else:
                sg.popup_error("No message has been decoded yet")
                
        elif event == "-COPY-MESSAGE-":
            message = values["-EXTRACTED-MESSAGE-"]
            if message:
                sg.clipboard_set(message)
                window["-DECODE-STATUS-"].update("Message copied to clipboard")
            else:
                sg.popup_error("No message to copy")
                
        # Analyze tab events
        elif event == "-COMPARE-BUTTON-":
            if not values["-ORIGINAL-PATH-"] or not values["-COMPARE-STEGO-PATH-"]:
                sg.popup_error("Please select both original and stego images")
                continue
                
            # Start comparison thread
            threading.Thread(target=compare_images_thread, args=(window, values), daemon=True).start()
            
        elif event == "-COMPARE-DONE-":
            result = values[event]
            window["-ORIGINAL-PREVIEW-"].update(data=image_to_data(result["original_path"]))
            window["-STEGO-PREVIEW-"].update(data=image_to_data(result["stego_path"]))
            window["-DIFF-PREVIEW-"].update(data=image_to_data(result["diff_path"]))
            window["-ANALYSIS-RESULTS-"].update(result["analysis"])
            window["-ANALYZE-STATUS-"].update("Comparison completed")
            window["-PROGRESS-"].update(visible=False)
            
        elif event == "-COMPARE-ERROR-":
            window["-ANALYZE-STATUS-"].update(f"Error: {values[event]}")
            window["-PROGRESS-"].update(visible=False)
            sg.popup_error(f"Comparison failed: {values[event]}")
            
        elif event == "-CALC-PSNR-":
            if not values["-ORIGINAL-PATH-"] or not values["-COMPARE-STEGO-PATH-"]:
                sg.popup_error("Please select both original and stego images")
                continue
                
            try:
                psnr, mse = calculate_image_quality(values["-ORIGINAL-PATH-"], values["-COMPARE-STEGO-PATH-"])
                analysis = f"PSNR: {psnr:.2f} dB\nMSE: {mse:.4f}\n\n"
                
                if psnr > 40:
                    quality = "Excellent - differences virtually imperceptible"
                elif psnr > 30:
                    quality = "Good - differences hardly noticeable"
                elif psnr > 20:
                    quality = "Acceptable - some visible differences"
                else:
                    quality = "Poor - visible differences"
                    
                analysis += f"Quality Assessment: {quality}"
                window["-ANALYSIS-RESULTS-"].update(analysis)
                window["-ANALYZE-STATUS-"].update("PSNR calculation completed")
                
            except Exception as e:
                sg.popup_error(f"PSNR calculation failed: {str(e)}")
                
        elif event == "-SHOW-HIST-":
            if not values["-COMPARE-STEGO-PATH-"]:
                sg.popup_error("Please select at least a stego image")
                continue
                
            try:
                # This would be implemented based on your matplotlib integration preferences
                # For now, we'll just show a message
                sg.popup("Histogram functionality requires matplotlib integration.\nSee the Analyze tab in the web version for histograms.")
                
            except Exception as e:
                sg.popup_error(f"Histogram generation failed: {str(e)}")
                
        # File browser events
        elif event == "-COVER-PATH-":
            if values["-COVER-PATH-"]:
                image_data = image_to_data(values["-COVER-PATH-"])
                if image_data:
                    window["-COVER-IMAGE-"].update(data=image_data)
                    
        elif event == "-STEGO-PATH-":
            if values["-STEGO-PATH-"]:
                image_data = image_to_data(values["-STEGO-PATH-"])
                if image_data:
                    window["-DECODE-IMAGE-"].update(data=image_data)
                    
        # Progress updates
        elif event == "-PROGRESS-UPDATE-":
            window["-PROGRESS-"].update(values[event])
            
        # Audio tab events would be implemented similarly
            
    window.close()

if __name__ == "__main__":
    # Add PySimpleGUI to requirements
    if not any(line.startswith("PySimpleGUI") for line in open("requirements.txt", "r")):
        with open("requirements.txt", "a") as f:
            f.write("\nPySimpleGUI>=4.60.4  # For modern GUI interface")
    
    try:
        import PySimpleGUI as sg
    except ImportError:
        print("PySimpleGUI not found. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "PySimpleGUI"])
        import PySimpleGUI as sg
    
    main()
