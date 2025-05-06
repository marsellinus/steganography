"""
Image Analyzer class for steganography application.
Provides tools for analyzing and comparing images.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from PIL import Image, ImageChops, ImageDraw, ImageFont
import cv2
import uuid
import datetime
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import traceback
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from utils.pdf_generator import PDFReportGenerator

class ImageAnalyzer:
    """Class for image analysis in steganography applications"""
    
    def __init__(self, temp_dir=None):
        """
        Initialize the ImageAnalyzer
        
        Args:
            temp_dir: Directory for storing temporary files like plots
        """
        self.temp_dir = temp_dir or os.path.join(os.path.dirname(__file__), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.uuid = uuid.uuid4().hex[:8]
    
    def load_image(self, image_path):
        """
        Load an image from a file path
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PIL Image object or None if failed
        """
        try:
            return Image.open(image_path)
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def calculate_metrics(self, original_path, stego_path):
        """
        Calculate quality metrics between original and stego images
        
        Args:
            original_path: Path to the original image file
            stego_path: Path to the stego image file
            
        Returns:
            Dictionary with calculated metrics
        """
        try:
            # Load images
            orig_img = self.load_image(original_path)
            stego_img = self.load_image(stego_path)
            
            if orig_img is None or stego_img is None:
                return {"error": "Failed to load images"}
                
            # Convert to RGB to ensure consistent channels
            if orig_img.mode != 'RGB':
                orig_img = orig_img.convert('RGB')
            if stego_img.mode != 'RGB':
                stego_img = stego_img.convert('RGB')
                
            # Convert to numpy arrays for calculations
            orig_array = np.array(orig_img)
            stego_array = np.array(stego_img)
            
            # Ensure both arrays have the same shape
            if orig_array.shape != stego_array.shape:
                # Resize the stego image to match original
                stego_img = stego_img.resize(orig_img.size)
                stego_array = np.array(stego_img)
                
            # Calculate MSE
            mse = float(np.mean((orig_array - stego_array) ** 2))
            
            # Calculate PSNR
            try:
                psnr_value = float(psnr(orig_array, stego_array))
            except Exception:
                psnr_value = 0.0
                
            # Calculate SSIM
            try:
                # Convert to grayscale for SSIM if images are color
                if len(orig_array.shape) == 3 and orig_array.shape[2] >= 3:
                    orig_gray = cv2.cvtColor(orig_array, cv2.COLOR_RGB2GRAY)
                    stego_gray = cv2.cvtColor(stego_array, cv2.COLOR_RGB2GRAY)
                    ssim_value = float(ssim(orig_gray, stego_gray))
                else:
                    ssim_value = float(ssim(orig_array, stego_array))
            except Exception:
                ssim_value = 0.0
            
            # Determine image color mode and dimensions
            if len(orig_array.shape) == 2:
                color_mode = "Grayscale"
            elif orig_array.shape[2] == 3:
                color_mode = "RGB"
            elif orig_array.shape[2] == 4:
                color_mode = "RGBA"
            else:
                color_mode = "Unknown"
                
            dimensions = tuple(orig_img.size)  # Convert to tuple for JSON serialization
            
            # Determine quality rating
            quality_rating = "Unable to assess quality"
            quality_color = "gray"
            
            if psnr_value > 0:
                if psnr_value > 35:
                    quality_rating = "High Quality Steganography"
                    quality_color = "green"
                elif psnr_value > 25:
                    quality_rating = "Acceptable Steganography"
                    quality_color = "yellow"
                else:
                    quality_rating = "Low Quality Steganography"
                    quality_color = "red"
            
            return {
                "psnr": psnr_value,
                "ssim": ssim_value,
                "mse": mse,
                "dimensions": dimensions,
                "color_mode": color_mode,
                "quality_rating": quality_rating,
                "quality_color": quality_color
            }
        except Exception as e:
            print(f"Error in calculate_metrics: {e}")
            return {"error": str(e)}
    
    def generate_difference_image(self, original_path, stego_path, amplification=50, filename=None):
        """
        Generate enhanced difference image between original and stego images
        
        Args:
            original_path: Path to the original image file
            stego_path: Path to the stego image file
            amplification: Factor to amplify differences (default: 50)
            filename: Output filename
            
        Returns:
            Path to the generated difference image
        """
        try:
            # Load images
            orig_img = self.load_image(original_path)
            stego_img = self.load_image(stego_path)
            
            if orig_img is None or stego_img is None:
                print("Failed to load images for difference calculation")
                return None
            
            # Convert to RGB to ensure consistent channels
            if orig_img.mode != 'RGB':
                orig_img = orig_img.convert('RGB')
            if stego_img.mode != 'RGB':
                stego_img = stego_img.convert('RGB')
                
            # Ensure both images have the same size
            if orig_img.size != stego_img.size:
                stego_img = stego_img.resize(orig_img.size)
            
            # Calculate absolute difference
            diff = ImageChops.difference(orig_img, stego_img)
            
            # Convert to numpy array for better manipulation
            diff_array = np.array(diff).astype(np.float32)
            
            # Apply a simple amplification for visibility
            amplified_diff = np.clip(diff_array * amplification, 0, 255).astype(np.uint8)
            
            # Convert back to PIL Image
            enhanced_diff = Image.fromarray(amplified_diff)
            
            if filename:
                output_path = os.path.join(self.temp_dir, filename)
                enhanced_diff.save(output_path)
                
                # Verify the file was created
                if os.path.exists(output_path):
                    print(f"Difference image saved successfully: {output_path}")
                    return output_path
                else:
                    print(f"Failed to save difference image to {output_path}")
                    return None
            else:
                return enhanced_diff
                
        except Exception as e:
            print(f"Error generating difference image: {e}")
            traceback.print_exc()
            return None
    
    def generate_histogram_comparison(self, original_path, stego_path, filename=None):
        """
        Generate histogram comparison between original and stego images
        
        Args:
            original_path: Path to the original image file
            stego_path: Path to the stego image file
            filename: Output filename
            
        Returns:
            Path to the generated histogram comparison
        """
        try:
            # Load images
            orig_img = self.load_image(original_path)
            stego_img = self.load_image(stego_path)
            
            if orig_img is None or stego_img is None:
                return None
            
            # Convert to RGB to ensure consistent channels
            if orig_img.mode != 'RGB':
                orig_img = orig_img.convert('RGB')
            if stego_img.mode != 'RGB':
                stego_img = stego_img.convert('RGB')
            
            # Handle large images by resizing
            max_size = 1000
            if max(orig_img.size) > max_size or max(stego_img.size) > max_size:
                # Calculate resize ratio to maintain aspect ratio
                orig_ratio = min(max_size / max(orig_img.size), 1.0)
                stego_ratio = min(max_size / max(stego_img.size), 1.0)
                
                orig_new_size = (int(orig_img.size[0] * orig_ratio), int(orig_img.size[1] * orig_ratio))
                stego_new_size = (int(stego_img.size[0] * stego_ratio), int(stego_img.size[1] * stego_ratio))
                
                orig_img = orig_img.resize(orig_new_size, Image.LANCZOS)
                stego_img = stego_img.resize(stego_new_size, Image.LANCZOS)
            
            # Create figure with subplots
            plt.figure(figsize=(12, 8))
            
            # Convert to numpy arrays
            orig_array = np.array(orig_img)
            stego_array = np.array(stego_img)
            
            # Check if images are grayscale or color
            if len(orig_array.shape) <= 2 or orig_array.shape[2] == 1:
                # Grayscale images
                plt.subplot(1, 2, 1)
                plt.hist(orig_array.ravel(), bins=256, range=(0, 255), alpha=0.7, color='blue')
                plt.title('Original Image')
                plt.xlabel('Pixel Value')
                plt.ylabel('Frequency')
                
                plt.subplot(1, 2, 2)
                plt.hist(stego_array.ravel(), bins=256, range=(0, 255), alpha=0.7, color='red')
                plt.title('Stego Image')
                plt.xlabel('Pixel Value')
                plt.ylabel('Frequency')
            else:
                # Color images - show RGB channels
                colors = ('r', 'g', 'b')
                channel_names = ('Red', 'Green', 'Blue')
                
                for i, (color, name) in enumerate(zip(colors, channel_names)):
                    plt.subplot(3, 2, i*2+1)
                    try:
                        plt.hist(orig_array[:, :, i].ravel(), bins=256, range=(0, 255), alpha=0.7, color=color)
                        plt.title(f'Original - {name} Channel')
                        plt.xlabel('Pixel Value')
                        plt.ylabel('Frequency')
                    except Exception as e:
                        plt.text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center', transform=plt.gca().transAxes)
                        plt.title(f'Original - {name} Channel - Error')
                    
                    plt.subplot(3, 2, i*2+2)
                    try:
                        plt.hist(stego_array[:, :, i].ravel(), bins=256, range=(0, 255), alpha=0.7, color=color)
                        plt.title(f'Stego - {name} Channel')
                        plt.xlabel('Pixel Value')
                        plt.ylabel('Frequency')
                    except Exception as e:
                        plt.text(0.5, 0.5, f"Error: {str(e)}", ha='center', va='center', transform=plt.gca().transAxes)
                        plt.title(f'Stego - {name} Channel - Error')
            
            plt.tight_layout()
            
            if filename:
                try:
                    output_path = os.path.join(self.temp_dir, filename)
                    plt.savefig(output_path, dpi=100)
                    plt.close()
                    return output_path
                except Exception as e:
                    print(f"Error saving histogram: {e}")
                    plt.close()
                    return None
            else:
                plt.close()
                return None
                
        except Exception as e:
            print(f"Error generating histogram comparison: {e}")
            traceback.print_exc()
            return None
    
    def analyze_image_pair(self, original_path, stego_path, output_prefix=None):
        """
        Perform comprehensive analysis on a pair of images
        
        Args:
            original_path: Path to the original image file
            stego_path: Path to the stego image file
            output_prefix: Prefix for output filenames
            
        Returns:
            Dictionary with metrics and paths to generated visualizations
        """
        # Use unique prefix if none provided
        prefix = output_prefix or f"image_analysis_{uuid.uuid4().hex[:8]}"
        
        try:
            # Calculate metrics
            metrics = self.calculate_metrics(original_path, stego_path)
            
            if "error" in metrics:
                return metrics
            
            # Generate visualizations
            visualizations = {}
            
            # Save copies of original and stego images
            orig_img = self.load_image(original_path)
            stego_img = self.load_image(stego_path)
            
            orig_output_path = os.path.join(self.temp_dir, f"{prefix}_original.png")
            stego_output_path = os.path.join(self.temp_dir, f"{prefix}_stego.png")
            
            orig_img.save(orig_output_path)
            stego_img.save(stego_output_path)
            
            visualizations['original'] = orig_output_path
            visualizations['stego'] = stego_output_path
            
            try:
                # Generate difference image with increased amplification
                diff_path = self.generate_difference_image(
                    original_path, 
                    stego_path, 
                    amplification=50,  # Increased amplification for better visibility
                    filename=f"{prefix}_enhanced_difference.png"
                )
                
                if diff_path:
                    print(f"Difference image generated: {diff_path}")
                    visualizations['difference'] = diff_path
                else:
                    print("Failed to generate difference image")
            except Exception as e:
                print(f"Error generating difference image: {e}")
                traceback.print_exc()
            
            # Generate histogram comparison
            hist_path = self.generate_histogram_comparison(
                original_path,
                stego_path,
                filename=f"{prefix}_histogram.png"
            )
            
            if hist_path:
                visualizations['histogram_comparison'] = hist_path
                
            # Generate PDF report
            pdf_report_path = self.generate_pdf_report(
                original_path,
                stego_path,
                metrics,
                visualizations,
                f"{prefix}_report.pdf"
            )
            
            # Return all results
            result = {
                "metrics": metrics,
                "visualizations": visualizations,
                "pdf_report_path": pdf_report_path
            }
            
            return result
            
        except Exception as e:
            traceback.print_exc()
            return {"error": str(e)}
    
    def generate_pdf_report(self, original_path, stego_path, metrics, visualizations, output_filename):
        """
        Generate a comprehensive PDF report of the image analysis
        
        Args:
            original_path: Path to the original image file
            stego_path: Path to the stego image file
            metrics: Dictionary with image quality metrics
            visualizations: Dictionary with paths to visualization images
            output_filename: Filename for the PDF report
            
        Returns:
            Path to the generated PDF report
        """
        try:
            # Import the PDF generator
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
            try:
                from utils.pdf_generator import PDFReportGenerator
            except ImportError:
                # If the module is not found, we'll create the PDF report directly here
                return self._generate_pdf_report_fallback(original_path, stego_path, metrics, visualizations, output_filename)
            
            # Format metrics for display
            psnr = metrics.get('psnr', 0)
            psnr_formatted = f"{psnr:.2f} dB"
            ssim = metrics.get('ssim', 0)
            ssim_formatted = f"{ssim:.4f}"
            mse = metrics.get('mse', 0)
            mse_formatted = f"{mse:.8f}"
            quality_text = metrics.get('quality_rating', 'Unable to assess quality')
            
            # PDF file path
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Create PDF generator
            pdf = PDFReportGenerator(output_path)
            
            # Add title and file info
            pdf.add_title("Image Steganography Analysis Report")
            pdf.add_file_info(original_path, stego_path)
            
            # Add Image Quality Metrics
            pdf.add_heading("Image Quality Metrics")
            
            # Create metrics table
            metrics_data = [
                ["Metric", "Value", "Description"],
                ["PSNR", psnr_formatted, "Higher is better. Values > 30dB indicate good quality."],
                ["SSIM", ssim_formatted, "Closer to 1 is better. Measures structural similarity."],
                ["MSE", mse_formatted, "Lower is better. Measures average squared difference."],
            ]
            
            pdf.add_metrics_table(metrics_data)
            
            # Quality Assessment
            pdf.add_heading("Quality Assessment")
            pdf.add_paragraph(quality_text)
            
            # Image Information
            pdf.add_heading("Image Information")
            
            # Create info table with dimensions and color mode
            if 'dimensions' in metrics and 'color_mode' in metrics:
                width, height = metrics['dimensions']
                info_data = [
                    ["Dimensions", f"{width} × {height} pixels"],
                    ["Color Mode", metrics['color_mode']],
                ]
                pdf.add_info_table(info_data)
            
            # Add visualizations
            if 'original' in visualizations and 'stego' in visualizations:
                pdf.add_heading("Image Comparison")
                pdf.add_subheading("Original Image")
                pdf.add_image(visualizations['original'], width=4, height=4)
                
                pdf.add_subheading("Stego Image")
                pdf.add_image(visualizations['stego'], width=4, height=4)
                
            if 'difference' in visualizations:
                pdf.add_heading("Difference Analysis")
                pdf.add_image(
                    visualizations['difference'], 
                    width=4, 
                    height=4, 
                    caption="Enhanced difference between original and stego images."
                )
            
            if 'histogram_comparison' in visualizations:
                pdf.add_heading("Histogram Analysis")
                pdf.add_image(
                    visualizations['histogram_comparison'], 
                    width=7, 
                    height=4,
                    caption="Comparison of color channel histograms between original and stego images."
                )
            
            # Add footer
            pdf.add_footer()
            
            # Generate the PDF
            return pdf.generate()
        
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            traceback.print_exc()
            return None
            
    def _generate_pdf_report_fallback(self, original_path, stego_path, metrics, visualizations, output_filename):
        """
        Fallback method to generate PDF report when the PDFReportGenerator is not available
        Uses ReportLab directly
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Format metrics for display
            psnr = metrics.get('psnr', 0)
            psnr_formatted = f"{psnr:.2f} dB"
            ssim = metrics.get('ssim', 0)
            ssim_formatted = f"{ssim:.4f}"
            mse = metrics.get('mse', 0)
            mse_formatted = f"{mse:.8f}"
            quality_text = metrics.get('quality_rating', 'Unable to assess quality')
            
            # PDF file path
            output_path = os.path.join(self.temp_dir, output_filename)
            
            # Create the document
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            
            # Create styles
            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            heading_style = styles["Heading2"]
            normal_style = styles["Normal"]
            
            # Create a centered style for subtitles
            subtitle_style = ParagraphStyle(
                'subtitle', 
                parent=styles['Heading2'], 
                alignment=TA_CENTER,
                spaceAfter=12
            )
            
            # Create content elements
            elements = []
            
            # Title
            elements.append(Paragraph("Image Steganography Analysis Report", title_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # File information
            elements.append(Paragraph(f"Original File: {os.path.basename(original_path)}", normal_style))
            elements.append(Paragraph(f"Stego File: {os.path.basename(stego_path)}", normal_style))
            elements.append(Paragraph(f"Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Quality Metrics
            elements.append(Paragraph("Image Quality Metrics", heading_style))
            
            # Create metrics table
            metrics_data = [
                ["Metric", "Value", "Description"],
                ["PSNR", psnr_formatted, "Higher is better. Values > 30dB indicate good quality."],
                ["SSIM", ssim_formatted, "Closer to 1 is better. Measures structural similarity."],
                ["MSE", mse_formatted, "Lower is better. Measures average squared difference."],
            ]
            
            metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 3.5*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(metrics_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Quality Assessment
            elements.append(Paragraph("Quality Assessment", heading_style))
            elements.append(Paragraph(quality_text, normal_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Image Information
            elements.append(Paragraph("Image Information", heading_style))
            
            # Create info table with dimensions and color mode
            if 'dimensions' in metrics and 'color_mode' in metrics:
                width, height = metrics['dimensions']
                info_data = [
                    ["Dimensions", f"{width} × {height} pixels"],
                    ["Color Mode", metrics['color_mode']],
                ]
                
                info_table = Table(info_data, colWidths=[2*inch, 4*inch])
                info_table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(info_table)
                elements.append(Spacer(1, 0.3*inch))
            
            # Add visualizations
            if 'original' in visualizations and 'stego' in visualizations:
                elements.append(Paragraph("Image Comparison", heading_style))
                elements.append(Paragraph("Original Image", subtitle_style))
                img = Image(visualizations['original'], width=4*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
                
                elements.append(Paragraph("Stego Image", subtitle_style))
                img = Image(visualizations['stego'], width=4*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.3*inch))
                
            if 'difference' in visualizations:
                elements.append(Paragraph("Difference Analysis", heading_style))
                img = Image(visualizations['difference'], width=5*inch, height=5*inch)
                elements.append(img)
                elements.append(Paragraph("Enhanced difference between original and stego images.", normal_style))
                elements.append(Spacer(1, 0.3*inch))
            
            if 'histogram_comparison' in visualizations:
                elements.append(Paragraph("Histogram Analysis", heading_style))
                img = Image(visualizations['histogram_comparison'], width=6*inch, height=4*inch)
                elements.append(img)
                elements.append(Paragraph("Comparison of color channel histograms between original and stego images.", normal_style))
                elements.append(Spacer(1, 0.3*inch))
            
            # Footer
            elements.append(Paragraph("Transform Domain Steganography Analysis Tool", normal_style))
            
            # Build the PDF
            doc.build(elements)
            
            return output_path
            
        except Exception as e:
            print(f"Error generating fallback PDF report: {e}")
            traceback.print_exc()
            return None