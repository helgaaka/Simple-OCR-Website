from dotenv import load_dotenv
load_dotenv() 

from flask import send_from_directory
import os
import io
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'} 

try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if not GEMINI_API_KEY:
        raise ValueError("Error: Environment variable GEMINI_API_KEY tidak ditemukan. Pastikan file .env sudah benar.")
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(e)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image_with_gemini(file_content):
    try:
        img = Image.open(io.BytesIO(file_content))

        model = genai.GenerativeModel('gemini-1.5-flash-latest')

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

        response = model.generate_content([prompt, img])

        if not response.text:
             raise Exception("Gemini tidak mengembalikan teks. Gambar mungkin kosong atau tidak dapat dibaca.")

        return response.text

    except Exception as e:
        raise e


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/ocr-process', methods=['POST'])
def ocr_process():
    if 'image_file' not in request.files:
        return jsonify({"error": "Request harus menyertakan bagian 'image_file'"}), 400

    file = request.files['image_file']

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "File tidak valid. Gunakan: png, jpg, jpeg"}), 400

    try:
        file_content = file.read()
        extracted_text = process_image_with_gemini(file_content)
        return jsonify({"structured_text": extracted_text}), 200
    except Exception as e:
        app.logger.error(f"Terjadi kesalahan saat pemrosesan OCR dengan Gemini: {e}")
        return jsonify({"error": f"Gagal memproses file: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)

