import os
import io
import base64
import json
import struct
import zlib
import traceback
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth

app = Flask(__name__)

# ---------- CORS: Allow the frontend domain ----------
CORS(app, resources={r"/api/*": {"origins": "https://echoshield.cephasgm.org"}})

# ---------- Firebase Initialisation ----------
secret_path = '/etc/secrets/firebase-service-account.json'
if os.path.exists(secret_path):
    cred = credentials.Certificate(secret_path)
else:
    cred = credentials.Certificate('firebase-service-account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- Placeholder PNG generator (pure Python) ----------
def create_placeholder_png():
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)
    ihdr = chunk(b'IHDR', ihdr_data)
    raw = b'\x00' + b'\x00\x00\x00\x00'
    compressed = zlib.compress(raw)
    idat = chunk(b'IDAT', compressed)
    iend = chunk(b'IEND', b'')
    return signature + ihdr + idat + iend

PLACEHOLDER_PNG = create_placeholder_png()

# ---------- Signal simulation and AI modules ----------
from simulator import generate_iq_and_spectrogram
from ai_model import classify_spectrogram, generate_jamming_signal

# ---------- Helper: verify Firebase token ----------
def verify_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'Missing or invalid Authorization header'
    id_token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid'], None
    except Exception as e:
        return None, str(e)

# ---------- Global error handler: ensures CORS on all errors ----------
@app.errorhandler(Exception)
def handle_exception(e):
    err_trace = traceback.format_exc()
    print(err_trace)
    response = jsonify({
        'error': str(e),
        'trace': err_trace.split('\n')[-2] if '\n' in err_trace else str(e)
    })
    response.status_code = 500
    # Ensure CORS headers
    response.headers['Access-Control-Allow-Origin'] = 'https://echoshield.cephasgm.org'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# ---------- Routes ----------
@app.route('/api/test', methods=['GET', 'POST'])
def test():
    return jsonify({'message': 'Backend is reachable!'})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    try:
        # 1. Auth
        uid, error = verify_token(request)
        if error:
            return jsonify({'error': error}), 401

        # 2. Parse input
        data = request.get_json(silent=True)
        if not data or 'protocol' not in data:
            return jsonify({'error': 'Missing protocol in request body'}), 400

        protocol = data['protocol'].lower()
        if protocol not in ['wifi', 'lora', 'dji']:
            return jsonify({'error': 'Invalid protocol. Choose wifi, lora, or dji.'}), 400

        # 3. Simulate
        iq, spectrogram = generate_iq_and_spectrogram(protocol)

        # 4. AI classification
        predicted_class, confidence = classify_spectrogram(spectrogram)

        # 5. Jamming parameters
        jamming_params = generate_jamming_signal(predicted_class)

        # 6. Log to Firestore
        if db:
            try:
                db.collection('simulations').add({
                    'userId': uid,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'protocolRequested': protocol,
                    'detectedProtocol': predicted_class,
                    'confidence': float(confidence),
                    'jammingParams': jamming_params
                })
            except Exception as log_err:
                print(f"Firestore write failed: {log_err}")

        # 7. Return results
        return jsonify({
            'detected_protocol': predicted_class,
            'confidence': float(confidence),
            'jamming': jamming_params,
            'spectrogram_url': '/api/spectrogram/placeholder.png'
        })

    except Exception as e:
        err_trace = traceback.format_exc()
        print(err_trace)
        # Return 200 so the browser can read the error
        return jsonify({
            'error': str(e),
            'trace': err_trace.split('\n')[-2] if '\n' in err_trace else str(e)
        }), 200

@app.route('/api/spectrogram/<filename>')
def get_spectrogram(filename):
    return send_file(
        io.BytesIO(PLACEHOLDER_PNG),
        mimetype='image/png',
        as_attachment=False,
        download_name='spectrogram.png'
    )

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

# ---------- Safety net: add CORS headers to every response ----------
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://echoshield.cephasgm.org'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)