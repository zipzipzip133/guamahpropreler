import os
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta, timezone # <-- SUDAH DIPERBAIKI

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# --- Konfigurasi dan Variabel Global ---

# Kunci API rahasia Anda
SECRET_KEY = "akusayangvikaselamanya"

# Lokasi file data
DATA_FILE_PATH = '/tmp/premium_users.json'
INITIAL_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'premium_users.json')


# --- Fungsi Bantuan (Helper Functions) ---

def load_data():
    """Memuat data dari file JSON di /tmp. Jika tidak ada, salin dari data awal."""
    if not os.path.exists(DATA_FILE_PATH):
        if os.path.exists(INITIAL_DATA_PATH):
            with open(INITIAL_DATA_PATH, 'r') as f_initial:
                initial_data = json.load(f_initial)
            with open(DATA_FILE_PATH, 'w') as f_tmp:
                json.dump(initial_data, f_tmp, indent=2)
            return initial_data
        else:
            # Jika file data awal tidak ada, buat struktur default
            default_data = {"premium_users": []}
            with open(DATA_FILE_PATH, 'w') as f_tmp:
                json.dump(default_data, f_tmp, indent=2)
            return default_data

    try:
        with open(DATA_FILE_PATH, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {"premium_users": []}

def save_data(data):
    """Menyimpan data ke file JSON di /tmp."""
    with open(DATA_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def parse_duration(duration_str):
    """Mengubah string durasi (misal: '7day', '1mon') menjadi objek timedelta."""
    duration_str = duration_str.lower()
    if duration_str.endswith('day'):
        try:
            days = int(duration_str.replace('day', ''))
            return timedelta(days=days)
        except ValueError:
            return None
    elif duration_str.endswith('mon'):
        try:
            months = int(duration_str.replace('mon', ''))
            return timedelta(days=months * 30)
        except ValueError:
            return None
    return None

def cleanup_and_get_valid_users():
    """Membersihkan email yang sudah kedaluwarsa dan mengembalikan daftar yang valid."""
    data = load_data()
    # Gunakan waktu UTC saat ini untuk perbandingan yang akurat
    now = datetime.now(timezone.utc) # <-- SUDAH DIPERBAIKI
    
    valid_users = [
        user for user in data.get("premium_users", [])
        # Pastikan 'expires_at' ada sebelum membandingkan
        if 'expires_at' in user and datetime.fromisoformat(user['expires_at']) > now
    ]

    if len(valid_users) < len(data.get("premium_users", [])):
        data["premium_users"] = valid_users
        save_data(data)

    return valid_users


# --- Rute API (Endpoints) ---

@app.route('/')
def home():
    """Halaman utama untuk memastikan API berjalan."""
    return "BELI PREMIUM DONG TOLOL LU ANJING GAK MODAL KONTOL 🤭🗿"


@app.route('/add/premium', methods=['GET'])
def add_premium_user():
    """Endpoint untuk menambah atau memperbarui email premium."""
    key = request.args.get('key')
    email = request.args.get('addemail')
    duration_str = request.args.get('day')
    user_type = request.args.get('type')

    if key != SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid api, mau ngapain bang?"}), 401

    if not all([email, duration_str, user_type]):
        return jsonify({"status": "error", "message": "Missing parameters. Required: addemail, day, type, key"}), 400

    duration = parse_duration(duration_str)
    if not duration:
        return jsonify({"status": "error", "message": "Invalid duration format. Use 'Xday' or 'Xmon'."}), 400

    # Gunakan waktu UTC untuk semua perhitungan
    now_utc = datetime.now(timezone.utc) # <-- SUDAH DIPERBAIKI
    expires_at = now_utc + duration # <-- SUDAH DIPERBAIKI
    
    data = load_data()
    users = data.get("premium_users", [])

    user_found = False
    for user in users:
        if user['email'] == email:
            user['expires_at'] = expires_at.isoformat()
            user['type'] = user_type
            user['duration'] = duration_str
            user_found = True
            break
    
    if not user_found:
        users.append({
            "email": email,
            "type": user_type,
            "added_at": now_utc.isoformat(), # <-- SUDAH DIPERBAIKI
            "expires_at": expires_at.isoformat(),
            "duration": duration_str
        })

    data["premium_users"] = users
    save_data(data)

    return jsonify({
        "status": "success",
        "message": f"Email '{email}' has been added/updated.",
        "details": {
            "email": email,
            "type": user_type,
            "expires_at": expires_at.isoformat()
        }
    }), 200


@app.route('/delete/premium', methods=['GET'])
def delete_premium_user():
    """Endpoint untuk menghapus email premium."""
    key = request.args.get('key')
    email_to_delete = request.args.get('delemail')

    if key != SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid api , mau ngapain bang?"}), 401

    if not email_to_delete:
        return jsonify({"status": "error", "message": "Missing parameter: delemail"}), 400

    data = load_data()
    users = data.get("premium_users", [])
    
    users_after_deletion = [user for user in users if user.get('email') != email_to_delete]

    if len(users_after_deletion) < len(users):
        data["premium_users"] = users_after_deletion
        save_data(data)
        return jsonify({"status": "success", "message": f"Email '{email_to_delete}' has been deleted."}), 200
    else:
        return jsonify({"status": "error", "message": f"Email '{email_to_delete}' not found."}), 404


@app.route('/list/email/premium.json', methods=['GET'])
def list_premium_users():
    """Endpoint untuk menampilkan daftar email premium yang masih aktif."""
    valid_users = cleanup_and_get_valid_users()

    return jsonify({
        "retrieved_at": datetime.now(timezone.utc).isoformat(), # <-- SUDAH DIPERBAIKI
        "active_premium_users": valid_users
    }), 200
