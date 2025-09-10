# Capstone-1---JCAI
Capstone Module 1 - JCAI

# 🚗 Rental Mobil Management System

Sistem ini adalah aplikasi **console-based** untuk mengelola bisnis rental mobil.  
Program menyediakan 2 peran utama:
- **Pengelola (Manager)** → mengelola data mobil, statistik, visualisasi, dan user.  
- **Pelanggan (Customer)** → mencari, merental, dan mengembalikan mobil.  

## ⚙️ Fitur Utama
### 🔑 Login & Registrasi
- Login dengan **email & password** (default: `admin@rental.com` / `admin`, `customer@rental.com` / `admin`).  
- Batas login: 3 kali, program otomatis keluar jika gagal.  
- Registrasi user baru dengan validasi format email.  
- Role: `manager` atau `customer`.

### 👨‍💼 Menu Manager
- Lihat semua mobil dalam tabel.
- Filter mobil berdasarkan jenis atau status.
- Tambah mobil baru (ID otomatis, model/jenis dipilih dari daftar, validasi harga).
- Lihat **statistik detail**: total mobil, distribusi status, rata-rata harga, top 5 mobil paling sering dirental, dll.
- Ekspor statistik ke **Excel** (multi-sheet).
- Lihat **visualisasi** (pie, bar, histogram, scatter).
- Tambah user baru.
- Undo aksi terakhir (penambahan mobil atau perubahan status).

### 👨‍👩‍👦 Menu Customer
- Lihat mobil yang tersedia.
- Cari mobil berdasarkan model/jenis.
- Simulasi rental mobil (dengan konfirmasi & estimasi biaya).
- Simulasi pengembalian mobil (dengan konfirmasi).
- Undo aksi terakhir (rental/return).
- Logout.

### 📊 Visualisasi
- Pie chart: Tersedia vs Dirental.
- Bar chart: Jumlah mobil per jenis.
- Histogram: Distribusi harga sewa.
- Bar chart: Top 5 mobil paling sering dirental (ID + model).
- Scatter: Harga vs total rental count.

---

## 🛠️ Setup
1. Import database:
   ```sql
   SOURCE rental_db.sql;
   ```
   Ini akan membuat database `rental_db`, tabel `mobil_rental` (140 data dummy), dan tabel `users`.

2. Pastikan Python memiliki library:
   ```bash
   pip install mysql-connector-python pandas matplotlib tabulate openpyxl
   ```

3. Jalankan program:
   ```bash
   python rental_system.py
   ```

---

## 🔐 Catatan Keamanan
Saat ini password disimpan **plain-text** untuk kemudahan demo.  
🔒 **Disarankan** untuk meng-hash password (misalnya dengan `bcrypt`) agar lebih aman pada implementasi produksi.  
