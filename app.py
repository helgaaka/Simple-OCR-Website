from dotenv import load_dotenv
load_dotenv() # Memuat variabel dari file .env secara otomatis

import os
import io
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from PIL import Image # Library untuk memproses gambar

# --- Konfigurasi ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Batas ukuran file 10MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'} # Gemini Vision mendukung format gambar ini

# --- Inisialisasi Klien Gemini ---
# Ambil API Key dari environment variable yang sudah dimuat oleh load_dotenv()
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("Error: Environment variable GEMINI_API_KEY tidak ditemukan. Pastikan file .env sudah benar.")
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(e)

# --- Fungsi Bantuan ---
def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_with_gemini(file_content):
    """
    Memanggil Gemini API untuk melakukan OCR dengan mempertahankan tata letak.
    """
    try:
        # Muat konten file gambar mentah menjadi objek gambar yang bisa diproses
        img = Image.open(io.BytesIO(file_content))

        # Inisialisasi model Gemini
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # ---- PROMPT BARU YANG LEBIH DINAMIS ----
        prompt = """Anda adalah mesin OCR dengan presisi tinggi. Tugas utama Anda adalah mentranskripsikan teks dari gambar ini sambil mempertahankan tata letak visual aslinya secara akurat.

Instruksi:
1.  Analisis struktur dokumen pada gambar, identifikasi semua kolom, paragraf, daftar, dan indentasi.
2.  Gunakan spasi dan baris baru (`\n`) untuk mereplikasi tata letak tersebut dalam format teks murni. Jika ada dua kolom, teks di kolom kanan harus sejajar dengan benar relatif terhadap kolom kiri.
3.  Transkripsikan teks persis seperti yang terlihat.

Aturan Ketat:
- **JANGAN** tambahkan format Markdown (seperti `**` atau `*`).
- **JANGAN** interpretasikan ikon atau simbol menjadi emoji.
- **JANGAN** tambahkan komentar, judul, atau teks tambahan apa pun yang tidak ada di gambar.
- Hasilnya harus berupa teks mentah (raw text) saja."""

        # Kirim prompt dan gambar ke model Gemini
        response = model.generate_content([prompt, img])

        if not response.text:
             raise Exception("Gemini tidak mengembalikan teks. Gambar mungkin kosong atau tidak dapat dibaca.")

        return response.text

    except Exception as e:
        # Melempar kembali exception untuk ditangani oleh endpoint API
        raise e


# --- Rute untuk Halaman Utama (Frontend) ---
@app.route('/')
def index():
    """Menyajikan halaman web utama."""
    return render_template('index.html')


# --- Rute untuk API OCR ---
@app.route('/api/ocr-process', methods=['POST'])
def ocr_process():
    """Endpoint untuk menerima file, menjalankan OCR dengan Gemini, dan mengembalikan teks."""
    if 'image_file' not in request.files:
        return jsonify({"error": "Request harus menyertakan bagian 'image_file'"}), 400

    file = request.files['image_file']

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "File tidak valid. Gunakan: png, jpg, jpeg"}), 400

    try:
        file_content = file.read()
        # Panggil fungsi yang baru untuk memproses dengan Gemini
        extracted_text = process_image_with_gemini(file_content)
        return jsonify({"structured_text": extracted_text}), 200
    except Exception as e:
        app.logger.error(f"Terjadi kesalahan saat pemrosesan OCR dengan Gemini: {e}")
        return jsonify({"error": f"Gagal memproses file: {str(e)}"}), 500


# --- Menjalankan Server ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

