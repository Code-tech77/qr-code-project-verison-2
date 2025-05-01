from flask import Flask, request, jsonify, render_template, send_file, redirect
from uuid import uuid4
import os
import qrcode

app = Flask(__name__)
DB_FILE = "qr_codes.txt"

def load_data():
    data = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            for line in f:
                uid, url, scanned = line.strip().split(',')
                data[uid] = {'data': url, 'scanned': scanned == 'True'}
    return data

def save_data(data):
    with open(DB_FILE, 'w') as f:
        for uid, values in data.items():
            f.write(f"{uid},{values['data']},{str(values['scanned'])}\n")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    user_link = request.form.get('text')
    if not user_link:
        return jsonify({'error': 'No link provided'}), 400

    uid = str(uuid4())
    db = load_data()
    db[uid] = {'data': user_link, 'scanned': False}
    save_data(db)

    qr_url = request.host_url + 'scan_qr/' + uid
    qr = qrcode.make(qr_url)
    qr_path = f"static/qrcodes/{uid}.png"
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr.save(qr_path)

    return jsonify({'qr_path': '/' + qr_path}), 200

@app.route('/scan_qr/<uid>')
def scan_qr(uid):
    db = load_data()
    if uid in db:
        if not db[uid]['scanned']:
            db[uid]['scanned'] = True
            save_data(db)
            return redirect(db[uid]['data'])  # Redirect to user's original link
        else:
            return "<h1>QR Code Expired ❌</h1><p>This QR code has already been scanned once and is no longer valid.</p>", 400
    else:
        return "<h1>Invalid QR Code ❌</h1><p>This QR code does not exist.</p>", 404

if __name__ == '__main__':
    app.run(debug=True)
