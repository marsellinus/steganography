import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image, ImageTk
import threading

from dct_stego import DCTSteganography
from wavelet_stego import WaveletSteganography
from dft_stego import DFTSteganography
from svd_stego import SVDSteganography
from lbp_stego import LBPSteganography
from simple_dft_stego import SimpleDFTSteganography
from reliable_stego import ReliableSteganography

class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transform Domain Steganography")
        self.root.geometry("900x650")
        
        # Set the app icon if available
        try:
            self.root.iconphoto(True, tk.PhotoImage(file=os.path.join("static", "icon.png")))
        except:
            pass
            
        self.cover_image_path = ""
        self.stego_image_path = ""
        self.method = tk.StringVar(value="DCT")
        self.strength = tk.DoubleVar(value=10.0)  # Embedding strength
        self.encoding_options = {"Terminator": tk.StringVar(value="00000000")}
        
        # Status bar variables
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.progress_var = tk.DoubleVar()
        self.progress_var.set(0)
        
        self.create_widgets()
        
        # Create a style for the application
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#2a9d8f")
        self.style.configure("TLabel", padding=4)
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title Label
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
        ttk.Label(title_frame, text="Transform Domain Steganography", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Method selection
        method_frame = ttk.LabelFrame(main_frame, text="Steganography Method", padding="10")
        method_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        ttk.Radiobutton(method_frame, text="DCT Transform", variable=self.method, value="DCT").grid(row=0, column=0, sticky=tk.W, padx=10)
        ttk.Radiobutton(method_frame, text="Wavelet Transform", variable=self.method, value="Wavelet").grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(method_frame, text="DFT Transform", variable=self.method, value="DFT").grid(row=0, column=2, sticky=tk.W, padx=10)
        ttk.Radiobutton(method_frame, text="SVD Transform", variable=self.method, value="SVD").grid(row=0, column=3, sticky=tk.W, padx=10)
        ttk.Radiobutton(method_frame, text="LBP Transform", variable=self.method, value="LBP").grid(row=0, column=4, sticky=tk.W, padx=10)
        
        # Embedding strength slider
        strength_frame = ttk.Frame(main_frame)
        strength_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(strength_frame, text="Embedding Strength:").pack(side=tk.LEFT, padx=5)
        strength_slider = ttk.Scale(strength_frame, from_=1, to=50, orient=tk.HORIZONTAL, variable=self.strength, length=200)
        strength_slider.pack(side=tk.LEFT, padx=5)
        ttk.Label(strength_frame, textvariable=tk.StringVar(value=lambda: f"{self.strength.get():.1f}")).pack(side=tk.LEFT)
        
        # Notebook for Encode/Decode tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.N, tk.S, tk.E, tk.W), pady=10)
        
        # Encode tab
        encode_frame = ttk.Frame(notebook, padding="10")
        notebook.add(encode_frame, text="  Encode  ")
        
        ttk.Label(encode_frame, text="Cover Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cover_image_entry = ttk.Entry(encode_frame, width=50)
        self.cover_image_entry.grid(row=0, column=1, pady=5)
        ttk.Button(encode_frame, text="Browse...", command=self.browse_cover_image).grid(row=0, column=2, padx=5)
        
        ttk.Label(encode_frame, text="Secret Message:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.secret_text = tk.Text(encode_frame, height=6, width=50)
        self.secret_text.grid(row=1, column=1, columnspan=2, pady=5)
        
        # Buttons frame for encoding
        encode_buttons_frame = ttk.Frame(encode_frame)
        encode_buttons_frame.grid(row=2, column=1, pady=10)
        ttk.Button(encode_buttons_frame, text="Encode", command=self.encode_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(encode_buttons_frame, text="Clear", command=lambda: self.secret_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        # Image preview frame for encoding
        self.encode_preview_frame = ttk.LabelFrame(encode_frame, text="Image Preview", padding="10")
        self.encode_preview_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        cover_frame = ttk.Frame(self.encode_preview_frame)
        cover_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(cover_frame, text="Cover Image:").pack()
        self.cover_image_label = ttk.Label(cover_frame, text="No image selected")
        self.cover_image_label.pack(pady=5)
        
        stego_frame = ttk.Frame(self.encode_preview_frame)
        stego_frame.pack(side=tk.RIGHT, padx=10)
        ttk.Label(stego_frame, text="Stego Image:").pack()
        self.stego_image_label = ttk.Label(stego_frame, text="No output yet")
        self.stego_image_label.pack(pady=5)
        
        # Decode tab
        decode_frame = ttk.Frame(notebook, padding="10")
        notebook.add(decode_frame, text="  Decode  ")
        
        ttk.Label(decode_frame, text="Stego Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stego_image_entry = ttk.Entry(decode_frame, width=50)
        self.stego_image_entry.grid(row=0, column=1, pady=5)
        ttk.Button(decode_frame, text="Browse...", command=self.browse_stego_image).grid(row=0, column=2, padx=5)
        
        # Buttons frame for decoding
        decode_buttons_frame = ttk.Frame(decode_frame)
        decode_buttons_frame.grid(row=1, column=1, pady=10)
        ttk.Button(decode_buttons_frame, text="Decode", command=self.decode_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(decode_buttons_frame, text="Clear Results", command=lambda: self.extracted_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(decode_frame, text="Extracted Message:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.extracted_text = tk.Text(decode_frame, height=6, width=50)
        self.extracted_text.grid(row=2, column=1, columnspan=2, pady=5)
        
        # Image preview for decoding
        self.decode_preview_frame = ttk.LabelFrame(decode_frame, text="Image Preview", padding="10")
        self.decode_preview_frame.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(self.decode_preview_frame, text="Stego Image:").pack()
        self.stego_preview_label = ttk.Label(self.decode_preview_frame, text="No image selected")
        self.stego_preview_label.pack(padx=10, pady=5)
        
        # Analysis tab
        analysis_frame = ttk.Frame(notebook, padding="10")
        notebook.add(analysis_frame, text="  Analysis  ")
        
        # Add analysis widgets
        ttk.Label(analysis_frame, text="Image Analysis").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Compare original and stego images
        ttk.Button(analysis_frame, text="Compare Images", command=self.compare_images).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Show histogram
        ttk.Button(analysis_frame, text="Show Histogram", command=self.show_histogram).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Calculate PSNR
        ttk.Button(analysis_frame, text="Calculate PSNR", command=self.calculate_psnr).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # Results frame
        self.analysis_results_frame = ttk.LabelFrame(analysis_frame, text="Analysis Results")
        self.analysis_results_frame.grid(row=1, column=1, rowspan=3, padx=10, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Results text widget
        self.analysis_results = tk.Text(self.analysis_results_frame, height=12, width=40)
        self.analysis_results.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        ttk.Progressbar(status_frame, variable=self.progress_var, length=200, mode='determinate').pack(side=tk.RIGHT, padx=5)
        
        # Make the grid expandable
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Set up the expandable rows and columns for the encode and decode frames
        encode_frame.columnconfigure(1, weight=1)
        encode_frame.rowconfigure(1, weight=1)
        decode_frame.columnconfigure(1, weight=1)
        decode_frame.rowconfigure(2, weight=1)
    
    def browse_cover_image(self):
        filename = filedialog.askopenfilename(title="Select Cover Image",
                                           filetypes=(("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")))
        if filename:
            self.cover_image_path = filename
            self.cover_image_entry.delete(0, tk.END)
            self.cover_image_entry.insert(0, filename)
            self.update_image_preview(self.cover_image_label, filename)
    
    def browse_stego_image(self):
        filename = filedialog.askopenfilename(title="Select Stego Image",
                                           filetypes=(("Image files", "*.png;*.bmp"), ("All files", "*.*")))
        if filename:
            self.stego_image_path = filename
            self.stego_image_entry.delete(0, tk.END)
            self.stego_image_entry.insert(0, filename)
            self.update_image_preview(self.stego_preview_label, filename)
    
    def update_image_preview(self, label, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((200, 200))  # Resize for preview
            photo_img = ImageTk.PhotoImage(img)
            label.config(image=photo_img)
            label.image = photo_img  # Keep a reference
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
    
    def encode_message(self):
        if not self.cover_image_path:
            messagebox.showerror("Error", "Please select a cover image")
            return
        
        message = self.secret_text.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to hide")
            return
        
        try:
            output_path = filedialog.asksaveasfilename(
                title="Save Stego Image",
                defaultextension=".png",
                filetypes=(("PNG files", "*.png"), ("BMP files", "*.bmp"))
            )
            
            if not output_path:
                return
            
            # Update status
            self.status_var.set("Encoding message...")
            self.progress_var.set(20)
            self.root.update_idletasks()
            
            # Get the selected strength value
            strength = self.strength.get()
            
            # Run encoding in a separate thread to keep UI responsive
            def encode_thread():
                try:
                    self.progress_var.set(40)
                    self.root.update_idletasks()
                    
                    if self.method.get() == "DCT":
                        stego = DCTSteganography(quantization_factor=strength)
                        stego.encode(self.cover_image_path, message, output_path)
                    elif self.method.get() == "Wavelet":
                        stego = WaveletSteganography(threshold=strength)
                        stego.encode(self.cover_image_path, message, output_path)
                    elif self.method.get() == "DFT":
                        stego = DFTSteganography(strength=strength)
                        stego.encode(self.cover_image_path, message, output_path)
                    elif self.method.get() == "SVD":
                        stego = SVDSteganography(strength=strength)
                        stego.encode(self.cover_image_path, message, output_path)
                    else:  # LBP
                        stego = LBPSteganography(strength=strength)
                        stego.encode(self.cover_image_path, message, output_path)
                    
                    self.progress_var.set(80)
                    self.root.update_idletasks()
                    
                    # Update UI from the main thread
                    self.root.after(0, lambda: self.finish_encode(output_path))
                    
                except Exception as e:
                    # Handle errors on the main thread
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Encoding failed: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("Encoding failed"))
                    self.root.after(0, lambda: self.progress_var.set(0))
            
            # Start the encoding thread
            threading.Thread(target=encode_thread, daemon=True).start()
                
        except Exception as e:
            messagebox.showerror("Error", f"Encoding failed: {str(e)}")
            self.status_var.set("Ready")
            self.progress_var.set(0)
    
    def finish_encode(self, output_path):
        messagebox.showinfo("Success", "Message encoded successfully!")
        self.update_image_preview(self.stego_image_label, output_path)
        self.status_var.set("Encoding completed")
        self.progress_var.set(100)
        # Reset progress bar after a delay
        self.root.after(2000, lambda: self.progress_var.set(0))
        self.root.after(2000, lambda: self.status_var.set("Ready"))
    
    def decode_message(self):
        if not self.stego_image_path:
            messagebox.showerror("Error", "Please select a stego image")
            return
        
        # Update status
        self.status_var.set("Decoding message...")
        self.progress_var.set(20)
        self.root.update_idletasks()
        
        # Get the selected strength value
        strength = self.strength.get()
        
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
        
        # Run decoding in a separate thread
        def decode_thread():
            try:
                self.progress_var.set(40)
                self.root.update_idletasks()
                
                message = None
                decode_error = None
                found_strength = None
                
                try:
                    # First try with the specified strength
                    if self.method.get() == "DCT":
                        stego = DCTSteganography(quantization_factor=strength)
                        message = stego.decode(self.stego_image_path)
                    elif self.method.get() == "Wavelet":
                        stego = WaveletSteganography(threshold=strength)
                        message = stego.decode(self.stego_image_path)
                    elif self.method.get() in ["DFT", "SVD", "LBP"]:
                        stego = ReliableSteganography(strength=strength)
                        message = stego.decode(self.stego_image_path)
                    
                    # Validate the message
                    if message and not is_valid_message(message):
                        print("Message found but seems corrupt, trying auto-detection...")
                        message = None  # Trigger auto-detection
                    
                    # If decoding failed or produced invalid results, try with different strength values
                    if message is None or message.strip() == "":
                        self.status_var.set("Trying different strength values...")
                        
                        # For DFT, try these specific values known to work well
                        if self.method.get() == "DFT":
                            test_strengths = [1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 20.0]
                        else:
                            test_strengths = [1.0, 5.0, 10.0, 15.0, 20.0, 25.0]

                        for test_strength in test_strengths:
                            if abs(test_strength - strength) < 0.1:
                                continue  # Skip if very close to the original strength
                            
                            self.progress_var.set(40 + (test_strength / 50.0) * 30)  # Progressive update
                            self.root.update_idletasks()
                            
                            try:
                                if self.method.get() == "DFT":
                                    stego = SimpleDFTSteganography(strength=test_strength)
                                    test_message = stego.decode(self.stego_image_path)
                                    
                                    if test_message and is_valid_message(test_message):
                                        message = test_message
                                        found_strength = test_strength
                                        break
                                elif self.method.get() == "DCT":
                                    stego = DCTSteganography(quantization_factor=test_strength)
                                    test_message = stego.decode(self.stego_image_path)
                                    
                                    if test_message and is_valid_message(test_message):
                                        message = test_message
                                        found_strength = test_strength
                                        break
                                elif self.method.get() == "Wavelet":
                                    stego = WaveletSteganography(threshold=test_strength)
                                    test_message = stego.decode(self.stego_image_path)
                                    
                                    if test_message and is_valid_message(test_message):
                                        message = test_message
                                        found_strength = test_strength
                                        break
                                elif self.method.get() == "SVD":
                                    stego = SVDSteganography(strength=test_strength)
                                    test_message = stego.decode(self.stego_image_path)
                                    
                                    if test_message and is_valid_message(test_message):
                                        message = test_message
                                        found_strength = test_strength
                                        break
                                else:  # LBP
                                    stego = LBPSteganography(strength=test_strength)
                                    test_message = stego.decode(self.stego_image_path)
                                    
                                    if test_message and is_valid_message(test_message):
                                        message = test_message
                                        found_strength = test_strength
                                        break
                            except Exception:
                                pass  # Ignore errors during auto-detection
                                
                except Exception as e:
                    decode_error = str(e)
                
                self.progress_var.set(80)
                self.root.update_idletasks()
                
                # Handle the result
                if (message is None or message.strip() == "") and decode_error:
                    self.root.after(0, lambda: messagebox.showerror("Decoding Error", 
                                   f"Decoding failed: {decode_error}\n\nTry adjusting the strength parameter."))
                    self.root.after(0, lambda: self.status_var.set("Decoding failed"))
                    self.root.after(0, lambda: self.progress_var.set(0))
                    return
                
                # Show success message if auto-detection worked
                if found_strength is not None:
                    self.root.after(0, lambda: messagebox.showinfo("Success", 
                                   f"Successfully decoded using strength = {found_strength}"))
                
                # Update UI from the main thread
                self.root.after(0, lambda: self.finish_decode(message))
                
            except Exception as e:
                # Handle general errors on the main thread
                self.root.after(0, lambda: messagebox.showerror("Error", f"Decoding failed: {str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Decoding failed"))
                self.root.after(0, lambda: self.progress_var.set(0))
        
        # Start the decoding thread
        threading.Thread(target=decode_thread, daemon=True).start()
    
    def finish_decode(self, message):
        if not message:
            messagebox.showwarning("Warning", 
                                  "No message found or decoding failed.\n\n"
                                  "Tips:\n"
                                  "1. Make sure you selected the correct steganography method.\n"
                                  "2. Try adjusting the strength parameter to match the encoding strength.\n"
                                  "3. Ensure the image hasn't been modified after encoding.")
        else:
            self.extracted_text.delete("1.0", tk.END)
            self.extracted_text.insert("1.0", message)
        
        self.status_var.set("Decoding completed")
        self.progress_var.set(100)
        # Reset progress bar after a delay
        self.root.after(2000, lambda: self.progress_var.set(0))
        self.root.after(2000, lambda: self.status_var.set("Ready"))
    
    def compare_images(self):
        """Compare original and stego images"""
        if not self.cover_image_path or not (hasattr(self, 'stego_image_label') and hasattr(self.stego_image_label, 'image')):
            messagebox.showerror("Error", "Please encode a message first to compare images")
            return
            
        import cv2
        import numpy as np
        
        try:
            original = cv2.imread(self.cover_image_path)
            stego_path = filedialog.askopenfilename(
                title="Select Stego Image to Compare",
                filetypes=(("Image files", "*.png;*.bmp;*.jpg;*.jpeg"), ("All files", "*.*"))
            )
            
            if not stego_path:
                return
                
            stego = cv2.imread(stego_path)
            
            if original.shape != stego.shape:
                messagebox.showerror("Error", "Images have different dimensions and cannot be compared")
                return
            
            # Calculate absolute difference
            diff = cv2.absdiff(original, stego)
            diff_amplified = cv2.convertScaleAbs(diff, alpha=5)  # Amplify differences for visibility
            
            # Save difference image
            temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_diff.png")
            cv2.imwrite(temp_path, diff_amplified)
            
            # Show difference image
            img = Image.open(temp_path)
            img.show(title="Image Difference (Amplified 5x)")
            
            # Update the analysis results
            self.analysis_results.delete(1.0, tk.END)
            self.analysis_results.insert(tk.END, f"Image Comparison Results:\n\n")
            
            # Calculate statistics
            mean_diff = np.mean(diff)
            max_diff = np.max(diff)
            std_dev = np.std(diff)
            
            self.analysis_results.insert(tk.END, f"Mean Absolute Difference: {mean_diff:.4f}\n")
            self.analysis_results.insert(tk.END, f"Maximum Difference: {max_diff:.4f}\n")
            self.analysis_results.insert(tk.END, f"Standard Deviation: {std_dev:.4f}\n\n")
            
            if mean_diff < 1.0:
                self.analysis_results.insert(tk.END, "Very small differences detected - excellent steganography!")
            elif mean_diff < 3.0:
                self.analysis_results.insert(tk.END, "Small differences detected - good steganography.")
            else:
                self.analysis_results.insert(tk.END, "Significant differences detected - steganography might be visible.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Image comparison failed: {str(e)}")
    
    def show_histogram(self):
        """Show histogram of the stego image"""
        if not self.stego_image_path:
            messagebox.showerror("Error", "Please select a stego image first")
            return
        
        try:
            import matplotlib.pyplot as plt
            import cv2
            import numpy as np
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Create a new window for the histogram
            hist_window = tk.Toplevel(self.root)
            hist_window.title("Image Histogram")
            hist_window.geometry("800x600")
            
            # Read the image
            img = cv2.imread(self.stego_image_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Create a figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(10, 8))
            fig.suptitle("Image Histogram Analysis")
            
            # Original RGB image
            axes[0, 0].imshow(img_rgb)
            axes[0, 0].set_title("Stego Image")
            axes[0, 0].axis('off')
            
            # RGB Histogram
            colors = ('r', 'g', 'b')
            for i, color in enumerate(colors):
                hist = cv2.calcHist([img], [i], None, [256], [0, 256])
                axes[0, 1].plot(hist, color=color)
            
            axes[0, 1].set_title("RGB Histogram")
            axes[0, 1].set_xlim([0, 256])
            axes[0, 1].grid(True)
            
            # Grayscale image
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            axes[1, 0].imshow(gray, cmap='gray')
            axes[1, 0].set_title("Grayscale Image")
            axes[1, 0].axis('off')
            
            # Grayscale histogram
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            axes[1, 1].plot(hist, color='black')
            axes[1, 1].set_title("Grayscale Histogram")
            axes[1, 1].set_xlim([0, 256])
            axes[1, 1].grid(True)
            
            # Adjust layout
            plt.tight_layout()
            
            # Embed the plot in the Tkinter window
            canvas = FigureCanvasTkAgg(fig, master=hist_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Update the analysis results
            self.analysis_results.delete(1.0, tk.END)
            self.analysis_results.insert(tk.END, f"Histogram Analysis Results:\n\n")
            
            # Calculate histogram statistics
            mean_val = np.mean(gray)
            std_dev = np.std(gray)
            median_val = np.median(gray)
            
            self.analysis_results.insert(tk.END, f"Mean Pixel Value: {mean_val:.2f}\n")
            self.analysis_results.insert(tk.END, f"Standard Deviation: {std_dev:.2f}\n")
            self.analysis_results.insert(tk.END, f"Median Value: {median_val:.2f}\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate histogram: {str(e)}")
    
    def calculate_psnr(self):
        """Calculate PSNR between original and stego images"""
        if not self.cover_image_path:
            messagebox.showerror("Error", "Please select a cover image first")
            return
        
        try:
            import cv2
            import numpy as np
            import math
            
            stego_path = filedialog.askopenfilename(
                title="Select Stego Image for PSNR Calculation",
                filetypes=(("Image files", "*.png;*.bmp;*.jpg;*.jpeg"), ("All files", "*.*"))
            )
            
            if not stego_path:
                return
            
            # Read images
            original = cv2.imread(self.cover_image_path)
            stego = cv2.imread(stego_path)
            
            if original.shape != stego.shape:
                messagebox.showerror("Error", "Images have different dimensions")
                return
            
            # Calculate MSE
            mse = np.mean((original - stego) ** 2)
            if mse == 0:  # Images are identical
                psnr = float('inf')
            else:
                # Calculate PSNR
                max_pixel = 255.0
                psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
            
            # Calculate SSIM
            try:
                from skimage.metrics import structural_similarity as ssim
                s_sim = ssim(original, stego, multichannel=True)
            except:
                s_sim = "Not available (skimage required)"
            
            # Update analysis results
            self.analysis_results.delete(1.0, tk.END)
            self.analysis_results.insert(tk.END, f"Image Quality Metrics:\n\n")
            self.analysis_results.insert(tk.END, f"PSNR: {psnr:.2f} dB\n")
            self.analysis_results.insert(tk.END, f"MSE: {mse:.4f}\n")
            self.analysis_results.insert(tk.END, f"SSIM: {s_sim}\n\n")
            
            # Interpretation
            if psnr > 40:
                quality = "Excellent - differences virtually imperceptible"
            elif psnr > 30:
                quality = "Good - differences hardly noticeable"
            elif psnr > 20:
                quality = "Acceptable - some visible differences"
            else:
                quality = "Poor - visible differences"
                
            self.analysis_results.insert(tk.END, f"Quality Assessment: {quality}\n")
            
            messagebox.showinfo("PSNR Calculation", f"PSNR = {psnr:.2f} dB\n\nHigher values indicate better quality.")
            
        except Exception as e:
            messagebox.showerror("Error", f"PSNR calculation failed: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()
