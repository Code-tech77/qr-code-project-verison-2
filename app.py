from flask import Flask, request, jsonify, render_template
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

@app.route('/scan_qr/<uid>', methods=['GET'])
def scan_qr(uid):
    db = load_data()
    if uid in db:
        if not db[uid]['scanned']:
            db[uid]['scanned'] = True
            save_data(db)
            return f"<h2>Redirecting to: {db[uid]['data']}</h2><script>window.location.replace('{db[uid]['data']}');</script>"
        else:
            return "<h2>QR code has already been scanned.</h2>"
    else:
        return "<h2>Invalid QR code.</h2>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
