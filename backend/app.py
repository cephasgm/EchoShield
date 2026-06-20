import os
import io
import base64
import json
import traceback
import numpy as np
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from simulator import generate_iq_and_spectrogram
from ai_model import classify_spectrogram, generate_jamming_signal

app = Flask(__name__)
CORS(app)

# ---------- Firebase Admin Initialisation ----------
secret_path = '/etc/secrets/firebase-service-account.json'
try:
    if os.path.exists(secret_path):
        cred = credentials.Certificate(secret_path)
    else:
        cred = credentials.Certificate('firebase-service-account.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase init error: {e}")
    db = None  # will cause errors later if used, but app starts

SPECTRO_DIR = '/tmp/spectrograms'
os.makedirs(SPECTRO_DIR, exist_ok=True)

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

@app.route('/api/simulate', methods=['POST'])
def simulate():
    try:
        uid, error = verify_token(request)
        if error:
            return jsonify({'error': error}), 401

        data = request.get_json()
        if not data or 'protocol' not in data:
            return jsonify({'error': 'Missing protocol in request body'}), 400

        protocol = data['protocol'].lower()
        if protocol not in ['wifi', 'lora', 'dji']:
            return jsonify({'error': 'Invalid protocol. Choose wifi, lora, or dji.'}), 400

        # Generate IQ and spectrogram
        iq, spectrogram = generate_iq_and_spectrogram(protocol)

        # AI classification
        predicted_class, confidence = classify_spectrogram(spectrogram)

        # Jamming signal generation
        jamming_params = generate_jamming_signal(predicted_class)

        # Save spectrogram as PNG
        run_id = base64.urlsafe_b64encode(os.urandom(8)).decode('utf-8')
        img_path = os.path.join(SPECTRO_DIR, f'{run_id}.png')
        plt.figure(figsize=(6,4))
        plt.imshow(spectrogram, aspect='auto', origin='lower', cmap='inferno')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_path, bbox_inches='tight', pad_inches=0)
        plt.close()

        spectrogram_url = f'/api/spectrogram/{run_id}.png'

        # Log to Firestore (if available)
        if db:
            db.collection('simulations').add({
                'userId': uid,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'protocolRequested': protocol,
                'detectedProtocol': predicted_class,
                'confidence': float(confidence),
                'jammingParams': jamming_params
            })

        return jsonify({
            'detected_protocol': predicted_class,
            'confidence': float(confidence),
            'jamming': jamming_params,
            'spectrogram_url': spectrogram_url
        })
    except Exception as e:
        # Return full traceback in JSON for debugging
        err = traceback.format_exc()
        print(err)  # also logs to Render
        return jsonify({'error': str(e), 'trace': err.split('\n')[-2] if '\n' in err else str(e)}), 500

@app.route('/api/spectrogram/<filename>')
def get_spectrogram(filename):
    path = os.path.join(SPECTRO_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Spectrogram not found'}), 404
    return send_file(path, mimetype='image/png')

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)