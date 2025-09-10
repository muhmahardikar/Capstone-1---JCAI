import mysql.connector
from tabulate import tabulate
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
import getpass
import re
import datetime
import os

# ---------- Configuration ----------
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "dika",
    "password": "admin",
    "database": "rental_db"
}

# Global for undo (one-level)
LAST_ACTION = None  # dict storing reverse operation details

# ---------- Database helpers ----------
def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def fetch_all_to_df(query, params=None):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params or ())
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description] if cursor.description else []
    conn.close()
    if rows:
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame(columns=cols)

# ---------- Input validation helpers ----------
def input_float(prompt, min_value=None):
    while True:
        try:
            val = float(input(prompt))
            if min_value is not None and val < min_value:
                print(f"Nilai harus >= {min_value}. Coba lagi.")
                continue
            return val
        except ValueError:
            print("Input harus berupa angka desimal (float). Coba lagi.")

def input_int(prompt, min_value=None, max_value=None):
    while True:
        try:
            val = int(input(prompt))
            if min_value is not None and val < min_value:
                print(f"Nilai harus >= {min_value}. Coba lagi.")
                continue
            if max_value is not None and val > max_value:
                print(f"Nilai harus <= {max_value}. Coba lagi.")
                continue
            return val
        except ValueError:
            print("Input harus berupa angka bulat (integer). Coba lagi.")

def input_choice(prompt, options):
    opts = [o.lower() for o in options]
    while True:
        val = input(prompt).strip()
        if val.lower() in opts:
            return options[opts.index(val.lower())]
        else:
            print("Pilihan tidak valid. Pilihan yang tersedia:", ", ".join(options))

# ---------- ID generator ----------
def generate_car_id(cursor):
    cursor.execute("SELECT car_id FROM mobil_rental ORDER BY car_id DESC LIMIT 1")
    last = cursor.fetchone()
    if last:
        last_id = last[0]
        try:
            num = int(last_id[1:]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"M{num:03d}"

def generate_user_id(cursor):
    cursor.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
    last = cursor.fetchone()
    if last:
        last_id = last[0]
        try:
            num = int(last_id[1:]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"U{num:03d}"

# ---------- Manager functions ----------
def show_all_cars():
    df = fetch_all_to_df("SELECT * FROM mobil_rental ORDER BY car_id")
    if df.empty:
        print("Tidak ada data mobil.")
        return
    print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))

def filter_cars():
    print("\nFilter berdasarkan:")
    print("1. Jenis mobil (car_type)")
    print("2. Status (Tersedia / Dirental)")
    choice = input_choice("Pilih opsi (1/2): ", ["1", "2"])
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    if choice == "1":
        types_df = fetch_all_to_df("SELECT DISTINCT car_type FROM mobil_rental")
        types = types_df['car_type'].tolist() if not types_df.empty else []
        if not types:
            print("Tidak ada data jenis mobil.")
            conn.close()
            return
        print("Tipe yang tersedia:", ", ".join(types))
        car_type = input_choice("Masukkan jenis mobil: ", types)
        cursor.execute("SELECT * FROM mobil_rental WHERE car_type = %s", (car_type,))
    else:
        status = input_choice("Masukkan status (Tersedia/Dirental): ", ["Tersedia", "Dirental"])
        cursor.execute("SELECT * FROM mobil_rental WHERE status = %s", (status,))
    rows = cursor.fetchall()
    conn.close()
    if rows:
        print(tabulate(rows, headers="keys", tablefmt="grid"))
    else:
        print("Data tidak ditemukan.")

def add_car():
    global LAST_ACTION
    conn = connect_db()
    cursor = conn.cursor()
    car_id = generate_car_id(cursor)
    print(f"ID mobil baru: {car_id}")

    car_options = [
        ("Toyota Avanza", "MPV"),
        ("Daihatsu Xenia", "MPV"),
        ("Honda Brio", "Hatchback"),
        ("Suzuki Ertiga", "MPV"),
        ("Mitsubishi Pajero", "SUV"),
        ("Toyota Fortuner", "SUV"),
        ("Honda Jazz", "Hatchback"),
        ("Toyota Yaris", "Hatchback"),
        ("Honda HRV", "SUV"),
        ("Toyota Innova", "MPV"),
        ("Honda Civic", "Sedan"),
        ("Toyota Camry", "Sedan"),
        ("Mazda CX-5", "SUV"),
        ("Nissan X-Trail", "SUV"),
        ("Mitsubishi Xpander", "MPV"),
    ]

    print("\nPilih mobil dari daftar berikut:")
    for i, (model, tipe) in enumerate(car_options, 1):
        print(f"{i}. {model} ({tipe})")

    idx = input_int("Pilih nomor mobil: ", 1, len(car_options))
    car_model, car_type = car_options[idx-1]

    price_per_day = input_float("Masukkan harga sewa per hari: Rp ", min_value=0)

    status = "Tersedia"
    current_rental_days = 0
    total_rental_count = 0

    # confirm
    print("\nRingkasan data mobil yang akan ditambahkan:")
    print(f"ID: {car_id}, Model: {car_model}, Type: {car_type}, Price/day: Rp {price_per_day:,}, Status: {status}")
    confirm = input_choice("Konfirmasi tambah mobil? (y/n): ", ["y","n"])
    if confirm == "n":
        print("Penambahan mobil dibatalkan.")
        conn.close()
        return

    cursor.execute("""
        INSERT INTO mobil_rental (car_id, car_model, car_type, price_per_day, status, current_rental_days, total_rental_count)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (car_id, car_model, car_type, price_per_day, status, current_rental_days, total_rental_count))
    conn.commit()

    # store undo info
    LAST_ACTION = {"action":"insert_car", "car_id":car_id}
    conn.close()
    print(f"Mobil {car_model} ({car_type}) berhasil ditambahkan dengan ID {car_id}! (Anda bisa undo terakhir jika perlu)")

# ---------- Statistics & export ----------
def show_statistics():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    print("\n=== Statistik Mobil Rental (Detail) ===")

    cursor.execute("SELECT COUNT(*) as cnt FROM mobil_rental")
    total = cursor.fetchone()['cnt'] or 0
    print(f"Total mobil di fleet: {total}")

    cursor.execute("SELECT status, COUNT(*) as jumlah FROM mobil_rental GROUP BY status")
    rows = cursor.fetchall()
    available = 0
    rented = 0
    for row in rows:
        print(f"{row['status']}: {row['jumlah']} mobil")
        if row['status'] == 'Tersedia':
            available = row['jumlah']
        elif row['status'] == 'Dirental':
            rented = row['jumlah']

    if total > 0:
        print(f"Persentase Tersedia: {available/total*100:.1f}% | Persentase Dirental: {rented/total*100:.1f}%")

    cursor.execute("SELECT AVG(price_per_day) as avg_price FROM mobil_rental")
    avg_price = cursor.fetchone()['avg_price']
    if avg_price is not None:
        print(f"Rata-rata harga sewa per hari (seluruh fleet): Rp {avg_price:,.0f}")

    cursor.execute("SELECT car_type, AVG(price_per_day) as avg_type_price, COUNT(*) as cnt FROM mobil_rental GROUP BY car_type")
    for row in cursor.fetchall():
        print(f"- {row['car_type']}: rata-rata Rp {row['avg_type_price']:,.0f} ({row['cnt']} unit)")

    cursor.execute("SELECT AVG(total_rental_count) as avg_rent_count, MAX(total_rental_count) as max_rent_count, MIN(total_rental_count) as min_rent_count FROM mobil_rental")
    rc = cursor.fetchone()
    print(f"Rata-rata total rental per mobil: {rc['avg_rent_count']:.2f}, Max: {rc['max_rent_count']}, Min: {rc['min_rent_count']}")

    cursor.execute("SELECT car_id, car_model, total_rental_count FROM mobil_rental ORDER BY total_rental_count DESC LIMIT 5")
    top5 = cursor.fetchall()
    if top5:
        print("\nTop 5 mobil berdasarkan total_rental_count:")
        df_top5 = pd.DataFrame(top5)
        print(tabulate(df_top5, headers="keys", tablefmt="grid", showindex=False))

    cursor.execute("SELECT car_id, car_model, current_rental_days FROM mobil_rental WHERE status='Dirental' ORDER BY current_rental_days DESC LIMIT 5")
    long_rentals = cursor.fetchall()
    if long_rentals:
        print("\nMobil dengan rental berjalan terlama:")
        df_lr = pd.DataFrame(long_rentals)
        print(tabulate(df_lr, headers="keys", tablefmt="grid", showindex=False))

    df = fetch_all_to_df("SELECT price_per_day, car_type, status, total_rental_count, car_id, car_model FROM mobil_rental")
    if not df.empty:
        print("\nRingkasan distribusi harga sewa:")
        print(df['price_per_day'].describe().to_string())

    # Offer export to Excel
    export = input_choice("\nApakah ingin mengekspor ringkasan statistik ke file Excel? (y/n): ", ["y","n"])
    if export == "y":
        default_name = f"rental_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = input(f"Masukkan nama file Excel atau tekan Enter untuk default [{default_name}]: ").strip()
        if filepath == "":
            filepath = default_name
        # build a few sheets
        with pd.ExcelWriter(filepath) as writer:
            # overall summary
            overall = {
                "total_mobil":[total],
                "tersedia":[available],
                "dirental":[rented],
                "avg_price":[avg_price if avg_price is not None else 0]
            }
            pd.DataFrame(overall).to_excel(writer, sheet_name="summary", index=False)
            # top5
            if top5:
                pd.DataFrame(top5, columns=["car_id","car_model","total_rental_count"]).to_excel(writer, sheet_name="top5", index=False)
            # long rentals
            if long_rentals:
                pd.DataFrame(long_rentals, columns=["car_id","car_model","current_rental_days"]).to_excel(writer, sheet_name="long_rentals", index=False)
            # full dump for further analysis
            pd.DataFrame(df).to_excel(writer, sheet_name="full_data", index=False)
        print(f"Statistik berhasil diekspor ke {filepath}")

    conn.close()

# ---------- Visualizations ----------
def show_visualizations():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mobil_rental")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("Tidak ada data untuk divisualisasikan.")
        return
    df = pd.DataFrame(rows)

    while True:
        print("\n=== Menu Visualisasi ===")
        print("1. Pie Chart - Tersedia vs Dirental")
        print("2. Bar Chart - Jumlah mobil per jenis")
        print("3. Histogram - Distribusi harga sewa")
        print("4. Bar Chart - Top 5 mobil paling sering dirental")
        print("5. Scatter - Harga vs Total Rental Count")
        print("6. Kembali ke menu utama")
        choice = input("Pilih opsi: ")

        if choice == "1":
            counts = df['status'].value_counts()
            counts.plot.pie(autopct='%1.1f%%', ylabel='')
            plt.title("Perbandingan Mobil Tersedia vs Dirental")
            plt.show()

        elif choice == "2":
            vc = df['car_type'].value_counts().sort_index()
            ax = vc.plot.bar()
            plt.title("Jumlah Mobil per Jenis")
            plt.xlabel("Jenis Mobil")
            plt.ylabel("Jumlah")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.show()

        elif choice == "3":
            ax = df['price_per_day'].plot.hist(bins=12)
            plt.title("Distribusi Harga Sewa Mobil")
            plt.xlabel("Harga Sewa per Hari")
            plt.ylabel("Frekuensi")
            plt.show()

        elif choice == "4":
            top5 = df.sort_values(by="total_rental_count", ascending=False).head(5).copy()
            top5['label'] = top5['car_id'] + " - " + top5['car_model']
            ax = top5.plot.bar(x='label', y='total_rental_count', legend=False)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.title("Top 5 Mobil Paling Sering Dirental (CarID - Model)")
            plt.xlabel("Mobil (ID - Model)")
            plt.ylabel("Jumlah Rental")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()

        elif choice == "5":
            ax = df.plot.scatter(x='price_per_day', y='total_rental_count')
            plt.title("Harga vs Total Rental Count")
            plt.xlabel("Harga per Hari")
            plt.ylabel("Total Rental Count")
            plt.show()

        elif choice == "6":
            break
        else:
            print("Pilihan tidak valid.")

# ---------- Undo support ----------
def undo_last_action():
    global LAST_ACTION
    if not LAST_ACTION:
        print("Tidak ada aksi yang dapat di-undo.")
        return
    print("Aksi terakhir:", LAST_ACTION.get('action'))
    confirm = input_choice("Apakah Anda ingin meng-undo aksi terakhir? (y/n): ", ["y","n"])
    if confirm == "n":
        print("Undo dibatalkan.")
        return
    conn = connect_db()
    cursor = conn.cursor()
    try:
        if LAST_ACTION['action'] == 'insert_car':
            cursor.execute("DELETE FROM mobil_rental WHERE car_id=%s", (LAST_ACTION['car_id'],))
            conn.commit()
            print(f"Penambahan mobil {LAST_ACTION['car_id']} berhasil di-undo (dihapus).")
        elif LAST_ACTION['action'] == 'update_status':
            # reverse to previous status and days and adjust total_rental_count if needed
            cursor.execute("UPDATE mobil_rental SET status=%s, current_rental_days=%s, total_rental_count=%s WHERE car_id=%s",
                           (LAST_ACTION['prev_status'], LAST_ACTION['prev_days'], LAST_ACTION['prev_total'], LAST_ACTION['car_id']))
            conn.commit()
            print(f"Perubahan status untuk {LAST_ACTION['car_id']} berhasil di-undo.")
        else:
            print("Tipe aksi undo tidak dikenali.")
    except Exception as e:
        print("Gagal melakukan undo:", e)
    finally:
        conn.close()
        LAST_ACTION = None

# ---------- User management (authentication, email validation) ----------
def init_user_tables():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(6) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            role ENUM('manager','customer') NOT NULL
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM users WHERE email='admin@rental.com'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (user_id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
                       ('U001','Admin Manager','admin@rental.com','admin','manager'))
    cursor.execute("SELECT COUNT(*) FROM users WHERE email='customer@rental.com'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (user_id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
                       ('U002','Admin Customer','customer@rental.com','admin','customer'))
    conn.commit()
    conn.close()

def is_valid_email(email):
    # basic but practical regex for emails
    pattern = r'^[A-Za-z0-9]+[A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None

def register_user():
    conn = connect_db()
    cursor = conn.cursor()
    print("\n=== Registrasi User Baru ===")
    name = input("Nama lengkap: ").strip()
    while True:
        email = input("Email: ").strip().lower()
        if not is_valid_email(email):
            print("Format email tidak valid. Contoh: nama@domain.com")
            continue
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s", (email,))
        if cursor.fetchone()[0] > 0:
            print("Email sudah terdaftar. Gunakan email lain atau login.")
        else:
            break
    password = getpass.getpass("Password (tidak akan ditampilkan): ").strip()
    role = input_choice("Role (manager/customer): ", ["manager","customer"])
    user_id = generate_user_id(cursor)
    cursor.execute("INSERT INTO users (user_id, name, email, password, role) VALUES (%s,%s,%s,%s,%s)",
                   (user_id, name, email, password, role))
    conn.commit()
    conn.close()
    print("Registrasi sukses. Anda dapat login menggunakan email dan password yang didaftarkan.")

def login_user():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    attempts = 3
    while attempts > 0:
        email = input("Email: ").strip().lower()
        password = getpass.getpass("Password: ").strip()
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            print(f"Login berhasil. Selamat datang, {user['name']} ({user['role']})")
            conn.close()
            return user
        else:
            attempts -= 1
            print(f"Login gagal. Kesempatan tersisa: {attempts}")
    conn.close()
    print("Anda telah gagal login 3 kali. Program akan keluar.")
    return None

# ---------- Customer functions ----------
def customer_menu(user):
    global LAST_ACTION
    while True:
        print(f"\n=== MENU PELANGGAN ({user['name']}) ===")
        print("1. Lihat mobil tersedia")
        print("2. Cari mobil (jenis/model)")
        print("3. Pinjam / rental mobil (simulasi)")
        print("4. Kembalikan mobil (simulasi)")
        print("5. Undo last action (jika ada)")
        print("6. Logout")
        choice = input("Pilih menu: ")
        if choice == '1':
            df = fetch_all_to_df("SELECT * FROM mobil_rental WHERE status='Tersedia' ORDER BY car_id")
            if df.empty:
                print("Tidak ada mobil tersedia saat ini.")
            else:
                print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        elif choice == '2':
            keyword = input('Masukkan kata kunci (model atau jenis): ').strip().lower()
            df = fetch_all_to_df("SELECT * FROM mobil_rental WHERE LOWER(car_model) LIKE %s OR LOWER(car_type) LIKE %s", params=(f"%{keyword}%", f"%{keyword}%"))
            if df.empty:
                print('Tidak ditemukan.')
            else:
                print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        elif choice == '3':
            car_id = input('Masukkan Car ID yang ingin dirental (contoh M001): ').strip().upper()
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM mobil_rental WHERE car_id=%s', (car_id,))
            car = cursor.fetchone()
            if not car:
                print('Car ID tidak ditemukan.')
            elif car['status'] == 'Dirental':
                print('Maaf, mobil sedang dirental.')
            else:
                days = input_int('Berapa hari ingin dirental? (integer): ', min_value=1)
                print(f"Anda akan merental {car_id} selama {days} hari, total harga estimasi: Rp {int(car['price_per_day']*days):,}")                
                confirm = input_choice("Konfirmasi rental? (y/n): ", ["y","n"])                
                if confirm == 'y':
                    # store previous state for undo
                    prev_status = car['status']
                    prev_days = car['current_rental_days']
                    prev_total = car['total_rental_count']
                    cursor.execute("UPDATE mobil_rental SET status='Dirental', current_rental_days=%s, total_rental_count=total_rental_count+1 WHERE car_id=%s", (days, car_id))
                    conn.commit()
                    LAST_ACTION = {'action':'update_status','car_id':car_id,'prev_status':prev_status,'prev_days':prev_days,'prev_total':prev_total}
                    print(f'Mobil {car_id} berhasil dirental selama {days} hari. (Anda bisa undo terakhir jika perlu)')
                else:
                    print('Rental dibatalkan.')
            conn.close()
        elif choice == '4':
            car_id = input('Masukkan Car ID yang ingin dikembalikan: ').strip().upper()
            conn = connect_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM mobil_rental WHERE car_id=%s', (car_id,))
            car = cursor.fetchone()
            if not car:
                print('Car ID tidak ditemukan.')
            elif car['status'] == 'Tersedia':
                print('Mobil sudah tersedia. Tidak perlu dikembalikan.')
            else:
                print(f"Anda akan mengembalikan {car_id}. Pastikan selesai pembayaran. ")                
                confirm = input_choice("Konfirmasi pengembalian? (y/n): ", ["y","n"])                
                if confirm == 'y':
                    prev_status = car['status']
                    prev_days = car['current_rental_days']
                    prev_total = car['total_rental_count']
                    cursor.execute("UPDATE mobil_rental SET status='Tersedia', current_rental_days=0 WHERE car_id=%s", (car_id,))
                    conn.commit()
                    LAST_ACTION = {'action':'update_status','car_id':car_id,'prev_status':prev_status,'prev_days':prev_days,'prev_total':prev_total}
                    print(f'Mobil {car_id} berhasil dikembalikan dan kini tersedia. (Anda bisa undo terakhir jika perlu)')
                else:
                    print('Pengembalian dibatalkan.')
            conn.close()
        elif choice == '5':
            undo_last_action()
        elif choice == '6':
            print('Logout.')
            break
        else:
            print('Pilihan tidak valid.')

# ---------- Manager menu ----------
def manager_menu(user):
    while True:
        print(f"\n=== MENU PENGELOLA ({user['name']}) ===")
        print("1. Lihat semua mobil")
        print("2. Filter mobil")
        print("3. Tambah mobil baru")
        print("4. Lihat statistik (detail)")
        print("5. Lihat visualisasi")
        print("6. Tambah user (registrasi admin/customer)")
        print("7. Undo last action (jika ada)")
        print("8. Logout")
        choice = input("Pilih menu: ")
        if choice == '1':
            show_all_cars()
        elif choice == '2':
            filter_cars()
        elif choice == '3':
            add_car()
        elif choice == '4':
            show_statistics()
        elif choice == '5':
            show_visualizations()
        elif choice == '6':
            register_user()
        elif choice == '7':
            undo_last_action()
        elif choice == '8':
            print('Logout.')
            break
        else:
            print('Pilihan tidak valid.')

# ---------- Entry point (choose role) ----------
def main():
    init_user_tables()
    print("Selamat datang di Sistem Rental Mobil (Manager & Pelanggan)")
    while True:
        print("\nMasuk sebagai:")
        print("1. Pengelola (manager)")
        print("2. Pelanggan (customer)")
        print("3. Registrasi akun baru")
        print("4. Keluar")
        choice = input("Pilih opsi: ")
        if choice == '1':
            print("-- Login Manager --")
            user = login_user()
            if user and user['role'] == 'manager':
                manager_menu(user)
            elif user:
                print('Akun Anda bukan manager.')
        elif choice == '2':
            print("-- Login Pelanggan --")
            user = login_user()
            if user and user['role'] == 'customer':
                customer_menu(user)
            elif user:
                print('Akun Anda bukan customer.')
        elif choice == '3':
            register_user()
        elif choice == '4':
            print('Terima kasih. Program selesai.')
            break
        else:
            print('Pilihan tidak valid.')

if __name__ == '__main__':
    main()
