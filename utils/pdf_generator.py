"""
PDF report generation utility for steganography analysis
"""

import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class PDFReportGenerator:
    """
    Utility class to generate PDF reports with consistent formatting
    for steganography analysis results
    """
    
    def __init__(self, output_path):
        """
        Initialize the PDF generator
        
        Args:
            output_path: Path where the PDF will be saved
        """
        self.output_path = output_path
        self.doc = SimpleDocTemplate(output_path, pagesize=letter)
        self.elements = []
        
        # Initialize styles
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles["Title"]
        self.heading_style = self.styles["Heading2"]
        self.normal_style = self.styles["Normal"]
        
        # Create a centered style for subtitles
        self.subtitle_style = ParagraphStyle(
            'subtitle', 
            parent=self.styles['Heading2'], 
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Create a style for metrics
        self.metric_style = ParagraphStyle(
            'metric',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=6
        )
    
    def add_title(self, title):
        """Add a title to the report"""
        self.elements.append(Paragraph(title, self.title_style))
        self.elements.append(Spacer(1, 0.25*inch))
    
    def add_file_info(self, original_path, stego_path):
        """Add file information section"""
        self.elements.append(Paragraph(f"Original File: {os.path.basename(original_path)}", self.normal_style))
        self.elements.append(Paragraph(f"Stego File: {os.path.basename(stego_path)}", self.normal_style))
        self.elements.append(Paragraph(f"Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        self.elements.append(Spacer(1, 0.25*inch))
    
    def add_heading(self, text):
        """Add a section heading"""
        self.elements.append(Paragraph(text, self.heading_style))
    
    def add_subheading(self, text):
        """Add a subheading"""
        self.elements.append(Paragraph(text, self.subtitle_style))
    
    def add_paragraph(self, text):
        """Add a paragraph of text"""
        self.elements.append(Paragraph(text, self.normal_style))
        self.elements.append(Spacer(1, 0.1*inch))
    
    def add_spacer(self, height=0.2):
        """Add vertical space"""
        self.elements.append(Spacer(1, height*inch))
    
    def add_metrics_table(self, metrics_data):
        """Add a formatted metrics table"""
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.elements.append(metrics_table)
        self.elements.append(Spacer(1, 0.2*inch))
    
    def add_info_table(self, info_data):
        """Add a formatted information table"""
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.elements.append(info_table)
        self.elements.append(Spacer(1, 0.3*inch))
    
    def add_image(self, image_path, width=6, height=4, caption=None):
        """Add an image with optional caption"""
        try:
            img = Image(image_path, width=width*inch, height=height*inch)
            self.elements.append(img)
            if caption:
                self.elements.append(Paragraph(caption, self.normal_style))
            self.elements.append(Spacer(1, 0.2*inch))
        except Exception as e:
            self.elements.append(Paragraph(f"Error adding image: {str(e)}", self.normal_style))
    
    def add_footer(self, text="Transform Domain Steganography Analysis Tool"):
        """Add a footer to the report"""
        self.elements.append(Paragraph(text, self.normal_style))
    
    def generate(self):
        """Build the PDF document and return the path"""
        try:
            self.doc.build(self.elements)
            return self.output_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
