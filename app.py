from flask import Flask, request, jsonify, render_template
from uuid import uuid4
import os
import qrcode
import sqlite3

app = Flask(__name__)
DB_FILE = "qr_codes.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS qr_codes (
            uid TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            scanned INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Generate a new QR code and store in DB
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    user_link = request.form.get('text')
    if not user_link:
        return jsonify({'error': 'No link provided'}), 400

    uid = str(uuid4())
    qr_url = request.host_url + 'scan_qr/' + uid

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO qr_codes (uid, data, scanned) VALUES (?, ?, ?)', (uid, user_link, 0))
    conn.commit()
    conn.close()

    qr = qrcode.make(qr_url)
    qr_path = f"static/qrcodes/{uid}.png"
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr.save(qr_path)

    return jsonify({'qr_path': '/' + qr_path}), 200

# QR scan endpoint
@app.route('/scan_qr/<uid>', methods=['GET'])
def scan_qr(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT data, scanned FROM qr_codes WHERE uid = ?', (uid,))
    row = c.fetchone()

    if row:
        url, scanned = row
        if not scanned:
            c.execute('UPDATE qr_codes SET scanned = 1 WHERE uid = ?', (uid,))
            conn.commit()
            conn.close()
            return render_template('scan_result.html', url=url, scanned=False, invalid=False)
        else:
            conn.close()
            return render_template('scan_result.html', url='', scanned=True, invalid=False)
    else:
        conn.close()
        return render_template('scan_result.html', url='', scanned=False, invalid=True)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()  # Ensure DB is ready
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)