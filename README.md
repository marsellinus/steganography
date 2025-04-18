# Aplikasi Steganografi Domain Transform

## Ringkasan

Aplikasi ini mengimplementasikan berbagai teknik steganografi domain transform untuk menyembunyikan pesan rahasia dalam gambar dan audio. Tidak seperti metode domain spasial seperti LSB (Least Significant Bit), steganografi domain transform menanamkan data dalam koefisien transformasi media, sehingga lebih tahan terhadap berbagai serangan dan pemrosesan.

## Teknik yang Diimplementasikan

### Steganografi Gambar

1. **DCT (Discrete Cosine Transform)**
   - Menyembunyikan data dalam koefisien frekuensi setelah transformasi DCT
   - Mirip dengan kompresi JPEG
   - Memberikan keseimbangan antara ketahanan dan kapasitas

2. **Wavelet Transform**
   - Menanamkan data dalam koefisien wavelet menggunakan DWT (Discrete Wavelet Transform)
   - Menyediakan lokalisasi yang baik dalam domain spasial dan frekuensi
   - Lebih tahan terhadap pemrosesan citra tertentu

3. **DFT (Discrete Fourier Transform)**
   - Menyembunyikan data dalam magnitudo komponen frekuensi
   - Memberikan ketahanan terhadap transformasi geometris seperti rotasi dan penskalaan

4. **SVD (Singular Value Decomposition)**
   - Menanamkan data dengan memodifikasi nilai singular dari blok gambar
   - Sangat tahan terhadap operasi pemrosesan gambar umum dan kompresi

5. **LBP (Local Binary Pattern)**
   - Menggunakan deskriptor tekstur untuk menyembunyikan informasi
   - Memanfaatkan pola tekstur gambar untuk steganografi

### Steganografi Audio

1. **DCT Audio (Discrete Cosine Transform)**
   - Menyembunyikan data dalam koefisien frekuensi dari sinyal audio
   - Memodifikasi komponen frekuensi menengah untuk meminimalkan perubahan yang terdengar

2. **Wavelet Audio**
   - Menanamkan data dalam koefisien wavelet sinyal audio
   - Menawarkan lokalisasi yang baik di domain waktu dan frekuensi

## Penjelasan Teknis Detail LBP Steganography

### 1. Konsep Dasar LBP (Local Binary Pattern)

LBP adalah operator tekstur yang digunakan untuk mengklasifikasikan pola tekstur pada citra. LBP mengkarakterisasi area lokal citra dengan membandingkan nilai piksel pusat dengan nilai piksel tetangganya dan mengubahnya menjadi nilai biner.

#### Algoritma LBP Dasar:

1. Untuk setiap piksel pusat (x,y) dalam sebuah gambar:
   - Bandingkan nilai keabuan (grayscale) piksel pusat dengan piksel tetangga di sekitarnya
   - Jika nilai piksel tetangga lebih besar atau sama dengan nilai piksel pusat, maka tandai sebagai 1, jika tidak 0
   - Susun bit hasil perbandingan (searah jarum jam atau sebaliknya) menjadi kode biner
   - Konversi kode biner ke nilai desimal, yang menjadi nilai LBP piksel pusat

```
Contoh untuk tetangga 3x3:
 Nilai piksel gambar:      Perbandingan dengan     Kode biner:
                          nilai tengah (100):
  65   70   95            0     0     0              00101011
  80  100   85   -->      0     -     0      -->  
  95  110  100            0     1     1             Nilai LBP = 43
```

### 2. LBP dalam Steganografi

LBP Steganography menggunakan sifat-sifat pola biner lokal dalam citra untuk menyembunyikan pesan. Pendekatan ini memiliki keunggulan karena:

1. **Menggunakan informasi tekstur**: Pesan tersembunyi dalam pola tekstur alami gambar
2. **Kesulitan deteksi visual**: Perubahan pada pola tekstur lebih sulit dideteksi mata manusia
3. **Ketahanan terhadap noise tertentu**: Karena berbasis pola relatif (bukan nilai absolut)

### 3. Implementasi Teknis LBP Steganography

#### Proses Encoding:

1. **Persiapan dan Transformasi**:
   ```python
   # Konversi gambar ke grayscale
   gray = cv2.cvtColor(cover_img, cv2.COLOR_BGR2GRAY)
   
   # Hitung representasi LBP
   # Radius=3 menentukan jari-jari tetangga, n_points=24 adalah jumlah titik tetangga
   lbp = local_binary_pattern(gray, n_points=24, radius=3, method='uniform')
   
   # Normalisasi nilai LBP ke rentang 0-255 untuk pemrosesan lebih lanjut
   lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
   ```

2. **Penyisipan Pesan**:
   ```python
   # Algoritma penyisipan bit (untuk setiap piksel yang dipilih)
   for y in range(h_start, h_end, 2):
       for x in range(w_start, w_end, 4):  # Menggunakan setiap piksel ke-4 secara horizontal
           bit = int(binary_message[message_index])
           pixel_val = int(lbp_normalized[y, x])
           
           # Jika bit pesan adalah 0, ubah nilai LBP menjadi kelipatan genap dari strength
           if bit == 0:
               stego_lbp[y, x] = int(strength * round(pixel_val / strength))
           # Jika bit pesan adalah 1, ubah nilai LBP menjadi kelipatan ganjil dari strength
           else:
               stego_lbp[y, x] = int(strength * round(pixel_val / strength - 0.5) + strength / 2)
   ```

3. **Penerapan Perubahan**:
   ```python
   # Menerapkan perubahan ke saluran warna (misalnya, saluran biru)
   for y in range(height):
       for x in range(width):
           if mask[y, x] == 255:  # Piksel yang berisi data pesan
               # Terapkan nilai yang dimodifikasi dengan atenuasi untuk meminimalkan distorsi visual
               diff = int(stego_lbp[y, x] - lbp_normalized[y, x])
               stego_img[y, x, 0] = np.clip(cover_img[y, x, 0] + diff // 4, 0, 255)
   ```

#### Proses Decoding:

1. **Transformasi dan Ekstraksi**:
   ```python
   # Ekstrak saluran yang digunakan untuk penyimpanan dan konversi ke grayscale
   gray = cv2.cvtColor(stego_img, cv2.COLOR_BGR2GRAY)
   
   # Hitung representasi LBP dengan parameter yang sama dengan encoding
   lbp = local_binary_pattern(gray, n_points=24, radius=3, method='uniform')
   lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
   ```

2. **Pengambilan Bit Pesan**:
   ```python
   # Untuk setiap piksel yang digunakan dalam encoding
   for y in range(h_start, h_end, 2):
       for x in range(w_start, w_end, 4):
           pixel_val = int(stego_img[y, x, 0])  # Menggunakan saluran biru
           
           # Memeriksa apakah nilai piksel adalah kelipatan genap atau ganjil dari strength
           remainder = (pixel_val % strength) / strength
           
           # Jika nilai mendekati setengah langkah, maka bit adalah 1
           if 0.35 < remainder < 0.65:
               extracted_bits.append(1)
           # Jika tidak, bit adalah 0
           else:
               extracted_bits.append(0)
   ```

### 4. Parameter Penting dalam LBP Steganography

1. **Radius (radius)**: 
   - Menentukan jarak tetangga dari piksel pusat
   - Nilai yang lebih besar mencakup area yang lebih luas tetapi kurang sensitif terhadap detail kecil
   - Implementasi menggunakan radius=3

2. **Jumlah Titik (n_points)**:
   - Jumlah titik sampel pada lingkaran dengan radius tertentu
   - Nilai yang lebih tinggi memberikan representasi yang lebih detail, tetapi meningkatkan kompleksitas
   - Implementasi menggunakan n_points=24

3. **Metode LBP (method)**:
   - 'uniform': Menggunakan pola seragam yang mengurangi dimensi dan lebih tahan terhadap noise
   - 'default': Menggunakan semua pola yang mungkin
   - 'ror': Menggunakan pola invarian rotasi
   - Implementasi menggunakan method='uniform'

4. **Kekuatan (strength)**:
   - Mengendalikan besarnya perubahan pada pola LBP
   - Nilai yang lebih tinggi memberikan ketahanan yang lebih baik tetapi mungkin menyebabkan distorsi visual
   - Implementasi menggunakan parameter yang dapat disesuaikan (default: 10.0)

### 5. Kelebihan dan Kekurangan

#### Kelebihan:
- **Berbasis tekstur**: Menggunakan karakteristik tekstur alami gambar
- **Ketahanan terhadap noise**: Lebih tahan terhadap beberapa jenis noise dan pemrosesan gambar
- **Distribusi modifikasi**: Perubahan tersebar pada area tekstur, mengurangi deteksi visual

#### Kekurangan:
- **Keterbatasan kapasitas**: Jumlah bit yang dapat disembunyikan lebih rendah daripada metode LSB konvensional
- **Area smooth**: Kurang efektif pada area gambar dengan tekstur minimal (area halus)
- **Kompleksitas komputasi**: Memerlukan perhitungan LBP yang lebih intensif komputasi

### 6. Contoh Kode Penuh LBP Steganography

```python
def encode_lbp(cover_image_path, message, output_path, strength=10.0, radius=3, n_points=24):
    """
    Menyembunyikan pesan dalam gambar menggunakan LBP steganography
    
    Langkah-langkah:
    1. Konversi pesan ke representasi biner
    2. Hitung pola biner lokal (LBP) dari gambar cover
    3. Modifikasi nilai LBP berdasarkan bit pesan
    4. Terapkan perubahan ke saluran warna gambar
    5. Simpan gambar stego
    """
    # Langkah 1: Konversi pesan ke biner dengan terminator
    binary_message = ''.join(format(ord(c), '08b') for c in message) + '00000000'
    
    # Langkah 2: Load gambar dan hitung LBP
    cover_img = cv2.imread(cover_image_path, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(cover_img, cv2.COLOR_BGR2GRAY)
    lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
    lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # Langkah 3: Modifikasi nilai LBP berdasarkan bit pesan
    height, width = gray.shape
    stego_lbp = lbp_normalized.copy()
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Tentukan area untuk penyembunyian (menghindari tepi)
    h_start, h_end = height // 8, height - height // 8
    w_start, w_end = width // 8, width - width // 8
    
    # Periksa kapasitas
    max_bits = (h_end - h_start) * (w_end - w_start) // 8
    if len(binary_message) > max_bits:
        raise ValueError(f"Pesan terlalu panjang! Max {max_bits} bits, got {len(binary_message)}")
    
    # Sisipkan pesan
    message_index = 0
    for y in range(h_start, h_end, 2):
        if message_index >= len(binary_message): break
        for x in range(w_start, w_end, 4):
            if message_index >= len(binary_message): break
            
            bit = int(binary_message[message_index])
            pixel_val = int(lbp_normalized[y, x])
            
            # Modifikasi nilai LBP berdasarkan bit pesan
            if bit == 0:
                stego_lbp[y, x] = int(strength * np.floor(pixel_val / strength))
            else:
                stego_lbp[y, x] = int(strength * np.floor(pixel_val / strength) + strength / 2)
            
            message_index += 1
            mask[y, x] = 255  # Tandai piksel ini di mask
    
    # Langkah 4: Terapkan perubahan ke saluran biru
    stego_img = cover_img.copy()
    for y in range(height):
        for x in range(width):
            if mask[y, x] == 255:
                diff = int(stego_lbp[y, x] - lbp_normalized[y, x])
                stego_img[y, x, 0] = np.clip(cover_img[y, x, 0] + diff // 4, 0, 255)
    
    # Langkah 5: Simpan gambar stego
    cv2.imwrite(output_path, stego_img)
    return output_path
```

## Proses Steganografi

### Proses Encoding (Penyembunyian Pesan)

1. **Persiapan Data**:
   - Teks pesan dikonversi menjadi representasi biner (0 dan 1)
   - Terminator ditambahkan di akhir pesan untuk menandai akhir pesan

2. **Transformasi Media**:
   - Gambar/audio diubah ke domain transform yang sesuai (DCT, Wavelet, DFT, SVD, atau LBP)
   - Media diproses dalam blok-blok (untuk DCT dan SVD) atau seluruh komponen (untuk Wavelet dan DFT)

3. **Penyisipan Pesan**:
   - Bit-bit pesan disisipkan dengan memodifikasi koefisien transform
   - Setiap bit pesan (0 atau 1) memengaruhi satu koefisien:
     - DCT: Koefisien frekuensi menengah dimodifikasi menjadi genap (untuk bit 0) atau ganjil (untuk bit 1)
     - Wavelet: Koefisien detail horizontal dimodifikasi
     - DFT: Magnitudo komponen frekuensi dimodifikasi
     - SVD: Nilai singular terbesar dari blok gambar dimodifikasi
     - LBP: Pola biner lokal dimodifikasi sesuai algoritma di atas

4. **Transformasi Balik**:
   - Domain transform diubah kembali ke domain asli (spasial/temporal)
   - Media yang telah disisipi pesan (stego media) disimpan dalam format yang sesuai

### Proses Decoding (Ekstraksi Pesan)

1. **Transformasi Media**:
   - Stego media dibaca dan dikonversi ke domain transform yang sesuai

2. **Ekstraksi Bit Pesan**:
   - Koefisien yang berisi pesan diperiksa (genap/ganjil, dll.)
   - Bit-bit pesan (0 atau 1) dikumpulkan berdasarkan karakteristik koefisien

3. **Konversi ke Pesan**:
   - Rangkaian bit dikonversi kembali menjadi karakter ASCII
   - Proses berhenti saat terminator ditemukan

## Detail Teknis Implementasi

### DCT (Discrete Cosine Transform):
```python
# Proses encoding
dct_block = cv2.dct(block)  # Menerapkan DCT pada blok 8x8
bit = int(binary_message[message_index])
if bit == 0:
    # Membuat koefisien genap
    dct_block[4, 5] = quantization_factor * math.floor(dct_block[4, 5] / quantization_factor)
else:
    # Membuat koefisien ganjil
    dct_block[4, 5] = quantization_factor * math.floor(dct_block[4, 5] / quantization_factor) + quantization_factor / 2
block = cv2.idct(dct_block)  # Menerapkan inverse DCT
```

### Wavelet Transform:
```python
# Proses encoding
coeffs = pywt.dwt2(blue_channel, wavelet)  # Menerapkan transformasi wavelet
cA, (cH, cV, cD) = coeffs  # Mendapatkan koefisien aproksimasi dan detail

for y in range(height):
    for x in range(width):
        bit = int(binary_message[message_index])
        if bit == 0:
            # Membuat koefisien kelipatan genap dari threshold
            cH[y, x] = round(cH[y, x] / threshold) * threshold
        else:
            # Membuat koefisien kelipatan ganjil dari threshold
            cH[y, x] = round(cH[y, x] / threshold) * threshold + threshold / 2

# Menerapkan transformasi wavelet terbalik
modified_coeffs = cA, (cH, cV, cD)
blue_channel_modified = pywt.idwt2(modified_coeffs, wavelet)
```

### DFT (Discrete Fourier Transform):
```python
# Proses encoding
dft = cv2.dft(green_channel, flags=cv2.DFT_COMPLEX_OUTPUT)
dft_shift = np.fft.fftshift(dft)  # Menggeser frekuensi nol ke tengah

# Menyembunyikan bit di magnitudo komponen frekuensi
magnitude = np.sqrt(dft_shift[i, j, 0]**2 + dft_shift[i, j, 1]**2)
if bit == 0:
    new_magnitude = strength * np.floor(magnitude / strength)
else:
    new_magnitude = strength * np.floor(magnitude / strength) + strength / 2

# Skala komponen nyata dan imajiner
scale = new_magnitude / magnitude
dft_shift[i, j, 0] *= scale
dft_shift[i, j, 1] *= scale
```

### SVD (Singular Value Decomposition):
```python
# Proses encoding
U, S, Vt = np.linalg.svd(block, full_matrices=False)  # Dekomposisi nilai singular

# Modifikasi nilai singular terbesar berdasarkan bit pesan
if bit == 0:
    S[0] = strength * np.floor(S[0] / strength)
else:
    S[0] = strength * np.floor(S[0] / strength) + strength / 2

# Rekonstruksi blok
modified_block = U @ np.diag(S) @ Vt
```

## Persyaratan

- Python 3.7+
- Paket yang diperlukan tercantum dalam `requirements.txt`

## Instalasi

1. Clone repositori:
```
git clone https://github.com/yourusername/transform-steganography.git
cd transform-steganography
```

2. Instal dependensi:
```
pip install -r requirements.txt
```

3. Jalankan aplikasi desktop:
```
python main.py
```

4. Atau jalankan aplikasi web:
```
python app.py
```

## Penggunaan

### Aplikasi Desktop

1. Pilih metode transform (DCT, Wavelet, DFT, SVD, LBP)
2. Sesuaikan kekuatan penyembunyian sesuai kebutuhan
3. Untuk encoding:
   - Pilih gambar cover
   - Masukkan pesan rahasia Anda
   - Klik "Encode" dan pilih di mana untuk menyimpan gambar stego
4. Untuk decoding:
   - Pilih gambar stego
   - Pilih metode transform yang sama yang digunakan untuk encoding
   - Klik "Decode" untuk mengekstrak pesan tersembunyi

### Aplikasi Web

1. Buka browser dan navigasi ke `http://127.0.0.1:5000/`
2. Ikuti petunjuk di layar untuk encode atau decode gambar

## Alat Analisis

- **Bandingkan Gambar**: Visualisasikan perbedaan antara gambar asli dan stego
- **Tampilkan Histogram**: Analisa distribusi warna
- **Hitung PSNR**: Ukur kualitas gambar dan imperceptibility steganografi

## Penulis

- Mahasiswa 1
- Mahasiswa 2
- Mahasiswa 3
- Mahasiswa 4
- Mahasiswa 5

## Lisensi

Proyek ini dilisensikan di bawah Lisensi MIT - lihat file LICENSE untuk detail.
