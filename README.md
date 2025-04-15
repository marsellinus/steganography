# Transform Domain Steganography Application

## Overview

This application implements various transform domain steganography techniques to hide secret messages in images. Unlike spatial domain methods like LSB (Least Significant Bit), transform domain steganography embeds data in the transform coefficients of the image, making it more robust against various attacks and processing.

## Implemented Techniques

1. **DCT (Discrete Cosine Transform)** - Hides data in the frequency coefficients after DCT transform, similar to JPEG compression.

2. **Wavelet Transform** - Embeds data in wavelet coefficients using DWT (Discrete Wavelet Transform).

3. **DFT (Discrete Fourier Transform)** - Hides data in the magnitude of frequency components.

4. **SVD (Singular Value Decomposition)** - Embeds data by modifying the singular values of image blocks.

5. **LBP (Local Binary Pattern) Transform** - Uses texture descriptors to hide information.

## Features

- Multiple transform domain techniques to choose from
- Adjustable embedding strength
- GUI interface with image previews
- Web interface with Flask
- Image analysis tools (histograms, PSNR calculation)
- Support for various image formats

## Requirements

- Python 3.7+
- Required packages listed in `requirements.txt`

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/transform-steganography.git
cd transform-steganography
```

2. Install requirements:
```
pip install -r requirements.txt
```

3. Run the desktop application:
```
python main.py
```

4. Alternatively, run the web application:
```
python app.py
```

## Usage

### Desktop Application

1. Select a transform method (DCT, Wavelet, DFT, SVD, LBP)
2. Adjust the embedding strength as needed
3. For encoding:
   - Select a cover image
   - Enter your secret message
   - Click "Encode" and choose where to save the stego image
4. For decoding:
   - Select the stego image
   - Choose the same transform method used for encoding
   - Click "Decode" to extract the hidden message

### Web Application

1. Open your browser and navigate to `http://127.0.0.1:5000/`
2. Follow the on-screen instructions to encode or decode images

## Analysis Tools

- **Compare Images**: Visualize differences between original and stego images
- **Show Histogram**: Analyze color distribution
- **Calculate PSNR**: Measure image quality and steganographic imperceptibility

## Authors

- Student 1
- Student 2
- Student 3
- Student 4
- Student 5

## License

This project is licensed under the MIT License - see the LICENSE file for details.
