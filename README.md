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

### 1. DCT (Discrete Cosine Transform)

DCT mengubah gambar dari domain spasial ke domain frekuensi, menghasilkan koefisien yang mewakili frekuensi berbeda dalam gambar. Koefisien frekuensi rendah berisi informasi visual yang paling penting, sementara koefisien frekuensi tinggi mewakili detail yang kurang terlihat.

#### Algoritma Encoding:
1. Gambar dibagi menjadi blok 8x8 piksel (standar dalam JPEG)
2. Setiap blok dikonversi ke ruang warna YCrCb dan kanal Y (luminance) digunakan untuk penyisipan
3. DCT diterapkan pada setiap blok, menghasilkan matriks 8x8 koefisien frekuensi
4. Koefisien frekuensi menengah dimodifikasi untuk menyimpan bit pesan (koefisien (4,5) digunakan dalam implementasi ini)
5. Bit 0 → Koefisien dibulatkan ke kelipatan genap dari faktor kuantisasi
6. Bit 1 → Koefisien dibulatkan ke kelipatan ganjil dari faktor kuantisasi
7. DCT terbalik diterapkan untuk mengkonversi blok kembali ke domain spasial
8. Blok yang dimodifikasi disusun kembali untuk membentuk gambar stego

```python
# Proses encoding DCT
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

#### Algoritma Decoding:
1. Gambar stego dibagi menjadi blok 8x8 piksel
2. Kanal Y dari setiap blok diekstrak
3. DCT diterapkan pada setiap blok
4. Koefisien (4,5) diperiksa untuk menentukan apakah itu kelipatan genap atau ganjil
5. Jika koefisien mendekati kelipatan genap → bit 0, jika mendekati kelipatan ganjil → bit 1
6. Bit-bit dikumpulkan hingga menemukan urutan 8 bit nol (terminator)
7. Bit-bit dikonversi kembali ke teks

#### Parameter Utama:
- **Block Size**: Ukuran blok untuk transformasi DCT (biasanya 8x8)
- **Quantization Factor**: Mengontrol kekuatan penyembunyian dan ekstraksi (nilai lebih besar = lebih tahan, tapi kualitas gambar lebih rendah)
- **Koefisien Target**: Posisi koefisien yang dimodifikasi dalam blok DCT (posisi frekuensi menengah ideal)

### 2. Wavelet Transform

Transformasi Wavelet memecah gambar menjadi komponen frekuensi berbeda dengan lokalisasi spasial yang baik. Ini menghasilkan subband yang mewakili aproksimasi (cA) dan detail (cH = horizontal, cV = vertikal, cD = diagonal).

#### Algoritma Encoding:
1. Gambar dikonversi ke kanal R, G, B dan biasanya kanal biru dipilih untuk penyisipan (mata manusia kurang sensitif terhadap perubahan biru)
2. Transformasi wavelet diterapkan, menghasilkan koefisien aproksimasi (cA) dan detail (cH, cV, cD)
3. Koefisien detail horizontal (cH) dimodifikasi untuk menyisipkan bit pesan
4. Bit 0 → Koefisien dibuat menjadi kelipatan genap dari threshold
5. Bit 1 → Koefisien dibuat menjadi kelipatan ganjil dari threshold
6. Transformasi wavelet terbalik diterapkan untuk menghasilkan kanal biru yang dimodifikasi
7. Kanal yang dimodifikasi digabungkan kembali dengan kanal lain untuk menghasilkan gambar stego

```python
# Proses encoding Wavelet
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

#### Algoritma Decoding:
1. Kanal biru dari gambar stego diekstrak
2. Transformasi wavelet diterapkan
3. Koefisien detail horizontal (cH) diperiksa
4. Jika koefisien mendekati kelipatan genap → bit 0, jika mendekati kelipatan ganjil → bit 1
5. Bit-bit dikumpulkan hingga urutan 8 bit nol (terminator) ditemukan
6. Bit-bit dikonversi kembali ke teks

#### Parameter Utama:
- **Wavelet**: Jenis wavelet yang digunakan (haar, db1, db4, dll.)
- **Level**: Tingkat dekomposisi wavelet (biasanya level 1)
- **Threshold**: Mengontrol kekuatan modifikasi (nilai lebih besar = lebih tahan, tapi distorsi lebih terlihat)
- **Subband Target**: Komponen wavelet yang dimodifikasi (biasanya cH)

### 3. DFT (Discrete Fourier Transform)

DFT mengubah gambar ke domain frekuensi menghasilkan koefisien kompleks yang mewakili magnitudo dan fase dari komponen frekuensi. DFT unggul dalam menghadapi transformasi geometris seperti rotasi dan penskalaan.

#### Algoritma Encoding:
1. Gambar dikonversi ke kanal R, G, B dan biasanya kanal hijau dipilih untuk penyisipan
2. DFT diterapkan pada kanal tersebut
3. Hasil shift diterapkan untuk memindahkan frekuensi nol ke tengah
4. Magnitudo dari koefisien frekuensi menengah dimodifikasi untuk menyisipkan bit pesan
5. Bit 0 → Magnitudo dibuat menjadi kelipatan genap dari strength parameter
6. Bit 1 → Magnitudo dibuat menjadi kelipatan ganjil dari strength parameter
7. Komponen real dan imajiner diskalakan untuk mencapai magnitudo yang diinginkan
8. DFT terbalik dan shift terbalik diterapkan
9. Kanal yang dimodifikasi dikembalikan ke gambar untuk menghasilkan gambar stego

```python
# Proses encoding DFT
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

#### Algoritma Decoding:
1. Kanal hijau dari gambar stego diekstrak
2. DFT diterapkan
3. Hasil shift diterapkan
4. Magnitudo dari koefisien target diperiksa
5. Jika magnitudo mendekati kelipatan genap → bit 0, jika mendekati kelipatan ganjil → bit 1
6. Bit-bit dikumpulkan hingga urutan 8 bit nol (terminator) ditemukan
7. Bit-bit dikonversi kembali ke teks

#### Parameter Utama:
- **Strength**: Mengontrol kekuatan modifikasi magnitudo
- **Region Target**: Area frekuensi yang dimodifikasi (mid-frequency ideal)
- **Kanal Warna**: Kanal yang digunakan untuk penyisipan (biasanya hijau)

### 4. SVD (Singular Value Decomposition)

SVD adalah faktoriasi matriks yang memecah gambar menjadi tiga matriks komponen: U, S, dan V^T. Nilai singular (diagonal matrix S) merepresentasikan energi gambar dan sangat stabil terhadap serangan.

#### Algoritma Encoding:
1. Gambar dibagi menjadi blok (biasanya 8x8 piksel)
2. Kanal merah biasanya dipilih untuk penyisipan
3. SVD diterapkan pada setiap blok, menghasilkan matriks U, S, dan V^T
4. Nilai singular pertama (S[0]) dimodifikasi untuk menyisipkan bit pesan
5. Bit 0 → Nilai singular dibuat menjadi kelipatan genap dari strength
6. Bit 1 → Nilai singular dibuat menjadi kelipatan ganjil dari strength
7. Blok direkonstruksi menggunakan U, S yang dimodifikasi, dan V^T
8. Blok yang dimodifikasi disusun kembali untuk membentuk gambar stego

```python
# Proses encoding SVD
U, S, Vt = np.linalg.svd(block, full_matrices=False)  # Dekomposisi nilai singular

# Modifikasi nilai singular terbesar berdasarkan bit pesan
if bit == 0:
    S[0] = strength * np.floor(S[0] / strength)
else:
    S[0] = strength * np.floor(S[0] / strength) + strength / 2

# Rekonstruksi blok
modified_block = U @ np.diag(S) @ Vt
```

#### Algoritma Decoding:
1. Kanal merah dari gambar stego diekstrak dan dibagi menjadi blok
2. SVD diterapkan pada setiap blok
3. Nilai singular pertama (S[0]) diperiksa
4. Jika nilai singular mendekati kelipatan genap → bit 0, jika mendekati kelipatan ganjil → bit 1
5. Bit-bit dikumpulkan hingga urutan 8 bit nol (terminator) ditemukan
6. Bit-bit dikonversi kembali ke teks

#### Parameter Utama:
- **Block Size**: Ukuran blok untuk SVD (biasanya 8x8)
- **Strength**: Mengontrol kekuatan modifikasi nilai singular
- **Kanal Warna**: Kanal yang digunakan untuk penyisipan (biasanya merah)

### 5. LBP (Local Binary Pattern)

LBP adalah operator tekstur yang mengkarakterisasi pola lokal gambar dengan membandingkan piksel pusat dengan piksel tetangganya, menghasilkan kode biner yang mewakili pola tekstur.

#### Algoritma Encoding:
1. Gambar dikonversi ke grayscale untuk perhitungan LBP
2. Representasi LBP dihitung dengan parameter radius dan jumlah titik tetangga
3. Nilai LBP dinormalisasi ke rentang 0-255
4. Nilai-nilai LBP yang dipilih dimodifikasi untuk menyisipkan bit pesan:
5. Bit 0 → Nilai LBP dibuat menjadi kelipatan genap dari strength
6. Bit 1 → Nilai LBP dibuat menjadi kelipatan ganjil dari strength 
7. Perubahan diterapkan ke saluran warna (biasanya biru) dengan atenuasi untuk meminimalkan distorsi visual

```python
# Proses encoding LBP
gray = cv2.cvtColor(cover_img, cv2.COLOR_BGR2GRAY)
lbp = local_binary_pattern(gray, n_points=24, radius=3, method='uniform')
lbp_normalized = cv2.normalize(lbp, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Algoritma penyisipan bit 
for y in range(h_start, h_end, 2):
    for x in range(w_start, w_end, 4):  # Menggunakan setiap piksel ke-4 secara horizontal
        bit = int(binary_message[message_index])
        pixel_val = int(lbp_normalized[y, x])
        
        # Jika bit pesan adalah 0, ubah nilai LBP menjadi kelipatan genap dari strength
        if bit == 0:
            stego_lbp[y, x] = int(strength * np.floor(pixel_val / strength))
        # Jika bit pesan adalah 1, ubah nilai LBP menjadi kelipatan ganjil dari strength
        else:
            stego_lbp[y, x] = int(strength * np.floor(pixel_val / strength) + strength / 2)

# Menerapkan perubahan ke saluran biru
for y in range(height):
    for x in range(width):
        if mask[y, x] == 255:  # Piksel yang berisi data pesan
            # Terapkan nilai yang dimodifikasi dengan atenuasi untuk meminimalkan distorsi visual
            diff = int(stego_lbp[y, x] - lbp_normalized[y, x])
            stego_img[y, x, 0] = np.clip(cover_img[y, x, 0] + diff // 4, 0, 255)
```

#### Algoritma Decoding:
1. Gambar stego dikonversi ke grayscale
2. Representasi LBP dihitung dengan parameter yang sama seperti encoding
3. Nilai piksel dari saluran biru pada lokasi yang digunakan untuk penyisipan diperiksa
4. Jika nilai mendekati kelipatan genap → bit 0, jika mendekati kelipatan ganjil → bit 1
5. Bit-bit dikumpulkan hingga urutan 8 bit nol (terminator) ditemukan
6. Bit-bit dikonversi kembali ke teks

```python
# Proses decoding LBP
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

#### Parameter Utama:
- **Radius**: Jarak tetangga dari piksel pusat (biasanya 1-3)
- **N_Points**: Jumlah titik sampel pada lingkaran (biasanya 8-24)
- **Method**: Mode LBP ('uniform', 'default', 'ror')
- **Strength**: Mengontrol kekuatan modifikasi nilai LBP
- **Kanal Warna**: Kanal yang dimodifikasi berdasarkan LBP (biasanya biru)

## Analisis Gambar

Aplikasi ini menyediakan alat analisis komprehensif untuk mengevaluasi kualitas steganografi dan keamanannya terhadap deteksi. Fitur analisis gambar membantu menilai seberapa baik pesan tersembunyi dalam gambar.

### 1. Perbandingan Gambar (Image Comparison)

Alat perbandingan gambar memungkinkan pengguna untuk membandingkan gambar asli (cover) dengan gambar stego secara visual.

#### Cara Kerja:
1. Aplikasi menghitung perbedaan absolut antara piksel gambar asli dan stego
2. Perbedaan divisualisasikan dengan amplifikasi (umumnya 10x) untuk membuat perubahan kecil terlihat
3. Peta panas warna (colormap) diterapkan untuk membuat area dengan perubahan lebih mudah dikenali

#### Interpretasi:
- **Area biru gelap**: Sedikit atau tidak ada perubahan
- **Area hijau/kuning**: Perubahan sedang
- **Area merah/ungu**: Perubahan signifikan

#### Contoh Implementasi:
```python
# Menghitung perbedaan gambar dan mengamplifikasinya untuk visualisasi
diff = cv2.absdiff(original, stego)
diff_amplified = cv2.convertScaleAbs(diff, alpha=10)  # Amplifikasi 10x
diff_color = cv2.applyColorMap(diff_amplified, cv2.COLORMAP_JET)  # Terapkan colormap
```

### 2. Histogram

Analisis histogram membandingkan distribusi nilai piksel antara gambar asli dan stego untuk mendeteksi perubahan statistik yang mungkin mengungkapkan keberadaan pesan tersembunyi.

#### Cara Kerja:
1. Histogram dihitung untuk setiap saluran warna (R, G, B) pada gambar asli dan stego
2. Hasil ditampilkan dalam grafik berdampingan untuk memudahkan perbandingan visual
3. Korelasi histogram dihitung sebagai metrik untuk mengukur kesamaan statistik

#### Interpretasi:
- **Korelasi mendekati 1.0**: Histogram sangat mirip, menunjukkan steganografi berkualitas tinggi
- **Korelasi < 0.95**: Mungkin menunjukkan perubahan yang terdeteksi pada distribusi nilai piksel

#### Contoh Implementasi:
```python
# Menghitung histogram untuk gambar asli dan stego
hist_original = cv2.calcHist([original], [0], None, [256], [0, 256])
hist_stego = cv2.calcHist([stego], [0], None, [256], [0, 256])

# Menghitung korelasi Pearson antara dua histogram
correlation, _ = pearsonr(hist_original.flatten(), hist_stego.flatten())
```

### 3. Metrik Kualitas Gambar

Metrik ini mengukur perbedaan matematis antara gambar asli dan stego untuk mengevaluasi kualitas steganografi.

#### 3.1. PSNR (Peak Signal-to-Noise Ratio)

PSNR adalah metrik yang mengukur kualitas gambar setelah dimodifikasi (dalam desibel).

**Cara Kerja:**
- Menghitung MSE (Mean Squared Error) antara gambar asli dan stego
- Mengkonversi MSE ke PSNR menggunakan rumus: PSNR = 20 * log10(255 / √MSE)

**Interpretasi:**
- **> 40 dB**: Kualitas sangat baik, perbedaan tidak terlihat oleh mata manusia
- **30-40 dB**: Kualitas baik, perbedaan hampir tidak terlihat
- **20-30 dB**: Kualitas cukup, beberapa perbedaan mungkin terlihat
- **< 20 dB**: Kualitas rendah, perbedaan terlihat jelas

```python
# Menghitung PSNR antara gambar asli dan stego
mse = np.mean((original - stego) ** 2)
if mse == 0:
    psnr = float('inf')
else:
    psnr = 20 * math.log10(255.0 / math.sqrt(mse))
```

#### 3.2. MSE (Mean Squared Error)

MSE mengukur rata-rata dari kuadrat perbedaan antara piksel-piksel gambar asli dan stego.

**Cara Kerja:**
- Menghitung selisih nilai piksel antara gambar asli dan stego
- Mengkuadratkan selisih tersebut dan menghitung rata-ratanya

**Interpretasi:**
- **Mendekati 0**: Gambar sangat mirip
- **Nilai lebih tinggi**: Menunjukkan lebih banyak perbedaan

```python
# Menghitung MSE antara gambar asli dan stego
mse = np.mean((original - stego) ** 2)
```

#### 3.3. SSIM (Structural Similarity Index)

SSIM adalah metrik yang lebih sesuai dengan persepsi manusia, berfokus pada perubahan dalam struktur gambar.

**Cara Kerja:**
- Mengukur perubahan dalam luminance, kontras, dan struktur antara gambar asli dan stego
- Menggabungkan metrik-metrik tersebut menjadi nilai SSIM antara -1 dan 1

**Interpretasi:**
- **Mendekati 1.0**: Gambar struktural sangat mirip
- **< 0.95**: Menandakan perubahan struktural yang mungkin terlihat

```python
# Menghitung SSIM antara gambar asli dan stego
from skimage.metrics import structural_similarity as ssim
ssim_value = ssim(original, stego, multichannel=True)
```

### 4. Deteksi Statistik

Analisis statistik mendeteksi anomali yang mungkin menunjukkan keberadaan pesan tersembunyi.

#### 4.1. Chi-Square Test

Chi-Square test dapat digunakan untuk mendeteksi perubahan tidak wajar dalam frekuensi nilai piksel yang bisa mengindikasikan steganografi LSB.

**Interpretasi:**
- **p-value rendah**: Kemungkinan gambar berisi pesan tersembunyi

#### 4.2. RS Analysis (Regular-Singular)

RS Analysis adalah metode statistik untuk mendeteksi steganografi berbasis LSB dengan menganalisis kelompok piksel.

### 5. Pengaruh Lapisan Transformasi pada Analisis

Untuk metode steganografi domain transform, analisis tambahan perlu dilakukan pada koefisien domain yang relevan:

#### 5.1. Analisis Koefisien DCT:
```python
# Menghitung perubahan koefisien DCT
block_size = 8
dct_diff = []

for y in range(0, height, block_size):
    for x in range(0, width, block_size):
        original_block = original_y[y:y+block_size, x:x+block_size]
        stego_block = stego_y[y:y+block_size, x:x+block_size]
        
        dct_original = cv2.dct(original_block.astype(np.float32))
        dct_stego = cv2.dct(stego_block.astype(np.float32))
        
        # Hitung perubahan pada koefisien DCT tengah
        diff = np.abs(dct_original - dct_stego)
        dct_diff.append(np.mean(diff))
```

#### 5.2. Analisis Koefisien Wavelet:
```python
# Menghitung perubahan koefisien Wavelet
coeffs_original = pywt.dwt2(original_blue, 'haar')
coeffs_stego = pywt.dwt2(stego_blue, 'haar')

# Bandingkan koefisien detail horizontal
cA_orig, (cH_orig, cV_orig, cD_orig) = coeffs_original
cA_stego, (cH_stego, cV_stego, cD_stego) = coeffs_stego

wavelet_diff = np.mean(np.abs(cH_orig - cH_stego))
```

## Fitur Analisis dalam Aplikasi

### Antarmuka Web:
Melalui panel Analyze, Anda dapat:
1. Mengupload gambar asli dan stego
2. Melihat gambar perbedaan yang dihasilkan (dengan amplifikasi untuk visibilitas)
3. Melihat metrik PSNR, MSE, dan korelasi histogram
4. Membandingkan histogram kedua gambar secara visual

### Aplikasi Desktop:
Melalui tab Analysis, Anda dapat:
1. Melakukan perbandingan gambar dengan visualisasi perbedaan
2. Melihat histogram komparatif
3. Menghitung metrik PSNR dan MSE
4. Melakukan analisis statistik tambahan

### Penggunaan Tools Analisis

1. **Persiapan**: Siapkan gambar asli (cover) dan gambar stego
2. **Perbandingan Visual**:
   - Upload kedua gambar
   - Lihat gambar perbedaan yang dihasilkan untuk mendeteksi area modifikasi
3. **Analisis Kuantitatif**:
   - Periksa nilai PSNR (>30dB menunjukkan steganografi berkualitas baik)
   - Periksa MSE (nilai lebih rendah menunjukkan perubahan lebih sedikit)
   - Periksa korelasi histogram (nilai mendekati 1.0 ideal)
4. **Analisis Histogram**:
   - Bandingkan kedua histogram secara visual untuk mendeteksi perbedaan distribusi
   - Perhatikan perbedaan signifikan yang mungkin mengungkap keberadaan pesan

### Batasan dan Catatan

- Analisis gambar ini dirancang terutama untuk pendidikan dan riset
- Tidak semua metode deteksi steganografi diimplementasikan
- Hasil analisis harus diinterpretasikan dengan mempertimbangkan konteks penggunaan
- Untuk hasil lebih akurat, gunakan metrik tambahan dan alat steganalisis khusus

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
