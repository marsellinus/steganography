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

## Fitur

- Berbagai teknik domain transform yang dapat dipilih
- Kekuatan penyembunyian yang dapat disesuaikan
- Antarmuka GUI dengan pratinjau gambar
- Antarmuka web dengan Flask
- Alat analisis gambar (histogram, perhitungan PSNR)
- Dukungan untuk berbagai format gambar dan audio

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
     - LBP: Pola biner lokal dimodifikasi

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
