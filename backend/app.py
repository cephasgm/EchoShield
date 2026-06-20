import os
import io
import struct
import zlib
import traceback
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://echoshield.cephasgm.org"}})

# ---------- Firebase ----------
secret_path = '/etc/secrets/firebase-service-account.json'
if os.path.exists(secret_path):
    cred = credentials.Certificate(secret_path)
else:
    cred = credentials.Certificate('firebase-service-account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- Placeholder PNG ----------
def create_placeholder_png():
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
    raw = b'\x00' + b'\x00\x00\x00\x00'
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend
PLACEHOLDER_PNG = create_placeholder_png()

# ---------- Simulator & AI ----------
from simulator import generate_iq_and_spectrogram
from ai_model import classify_spectrogram, generate_jamming_signal

def verify_token(req):
    auth = req.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None, 'Missing or invalid Authorization header'
    try:
        decoded = auth.verify_id_token(auth.split('Bearer ')[1])
        return decoded['uid'], None
    except Exception as e:
        return None, str(e)

# ---------- Routes ----------
@app.route('/')
def home():
    return jsonify({'status': 'ok', 'message': 'EchoShield API'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    try:
        uid, err = verify_token(request)
        if err:
            return jsonify({'error': err}), 401

        data = request.get_json(silent=True)
        if not data or 'protocol' not in data:
            return jsonify({'error': 'Missing protocol'}), 400

        protocol = data['protocol'].lower()
        if protocol not in ('wifi', 'lora', 'dji'):
            return jsonify({'error': 'Invalid protocol'}), 400

        iq, spec = generate_iq_and_spectrogram(protocol)
        pred, conf = classify_spectrogram(spec)
        jam = generate_jamming_signal(pred)

        if db:
            try:
                db.collection('simulations').add({
                    'userId': uid,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'protocolRequested': protocol,
                    'detectedProtocol': pred,
                    'confidence': float(conf),
                    'jammingParams': jam
                })
            except Exception as e:
                print(f"Firestore error: {e}")

        return jsonify({
            'detected_protocol': pred,
            'confidence': float(conf),
            'jamming': jam,
            'spectrogram_url': '/api/spectrogram/placeholder.png'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/spectrogram/<filename>')
def spectrogram(filename):
    return send_file(io.BytesIO(PLACEHOLDER_PNG), mimetype='image/png')

# ---------- CORS fallback ----------
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://echoshield.cephasgm.org'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response