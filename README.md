# Simulasi Deforestasi 2D (Pygame)

Sebuah aplikasi simulasi interaktif berbasis Python dan Pygame yang dirancang untuk memvisualisasikan dampak deforestasi terhadap keseimbangan ekosistem, peningkatan risiko erosi, serta pemicu terjadinya bencana alam.

Sistem ini menggunakan pendekatan berbasis grid (cellular automata) yang dikombinasikan dengan sistem partikel 2D, rendering berbasis kedalaman (Z-ordering), dan antarmuka pengguna dinamis untuk memberikan representasi visual yang akurat secara algoritmik.

---

## Deskripsi Fungsionalitas Utama

### 1. Sistem Terrain dan Vegetasi Dinamis

- **Pewarnaan Interpolasi:** Menggunakan algoritma Linear Interpolation (Lerp) untuk menghasilkan transisi warna yang halus antara tanah gersang dan rumput sehat, merepresentasikan tingkat tutupan vegetasi di setiap sel grid.
- **Rendering Pohon Berlapis:** Menggunakan pengurutan render berdasarkan sumbu Y (Y-sorting) untuk memberikan ilusi kedalaman. Kanopi pohon digambar dalam beberapa lapisan warna untuk mensimulasikan efek pencahayaan tiga dimensi.

### 2. Generasi Prosedural Lingkungan

- **Sistem Sungai Bersyarat:** Jalur sungai dibentuk menggunakan algoritma interpolasi smooth noise untuk menghasilkan pola aliran yang meliuk secara alami dari kiri atas ke kanan bawah area simulasi.
- **Pertumbuhan Hutan Awal:** Pada saat inisialisasi, pohon ditempatkan secara acak di luar area sungai untuk menciptakan ekosistem awal yang sehat.

### 3. Mesin Probabilitas Bencana Alam

Sistem memantau rasio hilangnya vegetasi untuk menghitung persentase Risiko Erosi. Risiko ini menjadi parameter penentu probabilitas dan jenis bencana yang akan terjadi:

- **Hujan & Badai:** Cuaca dinamis yang bertindak sebagai pre-cursor atau peringatan sebelum terjadinya bencana berbasis hidrologi.
- **Tanah Longsor (Landslide):** Dapat dipicu jika erosi > 50%. Menghancurkan pohon dalam radius tertentu, menyisakan tunggul, dan memunculkan efek partikel puing.
- **Banjir Besar (Flood):** Dapat dipicu jika erosi > 50%. Memperluas area sungai secara drastis berdasarkan faktor erosi, merendam pohon, dan mengurangi persentase kesehatan pohon secara bertahap hingga mati.
- **Gempa Bumi (Earthquake):** Dapat dipicu jika erosi > 70%. Mengaplikasikan efek guncangan kamera dan memiliki probabilitas tinggi untuk meruntuhkan pohon secara acak di seluruh peta.
- **Kekeringan (Drought):** Dapat dipicu jika erosi > 70%. Menyusutkan volume sungai menjadi sangat sempit, mengubah warna terrain menjadi kering, dan menurunkan kesehatan pohon akibat kurangnya suplai air.

---

## Arsitektur Kelas

- **Particle & RainDrop:** Menangani fisika dasar (gravitasi, kecepatan, umur) untuk efek visual seperti puing tanah saat pohon ditebang atau rintik hujan.
- **Cloud:** Menangani pergerakan awan secara horizontal, ukuran, dan perubahan warna (dari transparan menjadi abu-abu gelap saat mode hujan badai).
- **Button:** Menangani deteksi hover, status klik, dan render antarmuka pengguna interaktif pada panel sisi.
- **DeforestationSimulation:** Kelas inti pengelola status (State Manager). Menangani game loop, pembaruan fisika (dt), matriks deforestasi, kalkulasi risiko, dan pengurutan render layar.

---

## Antarmuka Pengguna (UI Panel)

Panel informasi di sebelah kanan simulasi terdiri dari beberapa kontainer terstruktur:

1. **Status Kewaspadaan:** Menampilkan indikator teks dinamis (Aman, Waspada, Bahaya, Kritis) yang bereaksi sesuai tingkat persentase risiko erosi saat ini.
2. **Statistik Real-time:** Menampilkan grafik batang (bar) dari persentase erosi, jumlah pohon aktif, jumlah tunggul, total bencana yang telah terjadi, dan total pohon yang mati akibat bencana.
3. **Panel Kontrol Interaktif:** Panel untuk memodifikasi mode aktif kursor atau memicu kejadian tertentu.
4. **Indikator Mode Aktif:** Teks di bagian bawah panel yang mengonfirmasi jenis aksi kursor saat ini (Tanam vs Tebang).

---

## Persyaratan Sistem

Pastikan lingkungan lokal Anda memenuhi spesifikasi berikut:

- **Bahasa Pemrograman:** Python 3.6 atau lebih baru.
- **Pustaka Eksternal:**
  - `pygame`: Untuk rendering grafis 2D dan penanganan interaksi pengguna.
  - `numpy`: Untuk kalkulasi matriks grid dan vektor secara efisien.

*Instalasi dependensi:*

```bash
pip install pygame numpy
```

---

## Cara Menjalankan

Eksekusi skrip utama melalui terminal atau command prompt:

```bash
python main.py
```

*(Catatan: Sesuaikan `main.py` dengan nama file sumber Anda)*

---

## Panduan Kontrol Pengguna

Interaksi utama pada area peta dilakukan melalui mouse. Aksi klik kiri sangat bergantung pada **Mode Aktif** yang sedang dipilih di Panel Kontrol.

### Aksi Mouse

- **Klik Kiri pada Peta:** Mengeksekusi tindakan berdasarkan mode yang sedang aktif.
- **Klik Kanan pada Peta:** Pintasan konstan untuk menebang pohon (menghapus objek pohon terdekat dari titik klik) tanpa perlu mengganti mode aktif.

### Tombol Aksi Panel Kontrol

- **🌱 Tanam Pohon (Mode Klik)**  
  *Fungsi:* Mengubah mode klik kiri untuk menanam bibit pohon baru di sel grid yang dituju.

- **🔪 Tebang Pohon (Mode Klik)**  
  *Fungsi:* Mengubah mode klik kiri untuk menebang pohon secara manual satu per satu.

- **🔥 Tebang 20% Pohon (Massal)**  
  *Fungsi:* Aksi instan yang langsung menghilangkan 20% dari total populasi pohon saat ini secara acak untuk mensimulasikan deforestasi berskala besar.

- **🔄 RESET SIMULASI**  
  *Fungsi:* Mengembalikan semua parameter ekologi ke titik mula (mereset generasi sungai, hutan, cuaca, dan statistik bencana).
