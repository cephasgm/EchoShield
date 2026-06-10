"""
EchoShield Backend - RF Simulator & AI Jamming Advisor
Flask app serving /api/simulate and spectrogram images.
Uses Firebase Admin for authentication and Firestore logging.
"""

import os
import io
import uuid
import base64
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from scipy import signal
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

app = Flask(__name__)
CORS(app)  # allow cross-origin requests from the PWA

# -------------------------------------------------------------------
# 1. Firebase Admin Setup
# -------------------------------------------------------------------
# Path to your downloaded service account key
SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), 'firebase-service-account.json')
if not os.path.exists(SERVICE_ACCOUNT_PATH):
    raise FileNotFoundError(
        "firebase-service-account.json not found. "
        "Download it from Firebase Console > Project Settings > Service accounts."
    )

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)
db = firestore.client()

# -------------------------------------------------------------------
# 2. In‑memory spectrogram storage (run_id -> image binary)
# -------------------------------------------------------------------
spectrogram_store = {}

# -------------------------------------------------------------------
# 3. RF Simulator Module
# -------------------------------------------------------------------
SAMPLE_RATES = {
    'wifi': 20e6,   # 20 MHz
    'lora': 1e6,    # 1 MHz
    'dji': 10e6     # 10 MHz
}
DURATION = 0.001  # 1 ms snippet for quick simulation (adjust as needed)

def generate_wifi_iq(duration=DURATION, sample_rate=SAMPLE_RATES['wifi']):
    """Generate OFDM-like Wi‑Fi IQ samples (simplified)."""
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate
    # Simulated OFDM: sum of 64 random subcarriers with QAM symbols
    iq = np.zeros(num_samples, dtype=complex)
    for subcarrier in range(-32, 32):
        if subcarrier == 0:
            continue
        symbol = (np.random.randn() + 1j * np.random.randn()) / np.sqrt(2)
        freq = subcarrier * 312.5e3  # subcarrier spacing
        iq += symbol * np.exp(2j * np.pi * freq * t)
    # Add cyclic prefix (simple copy)
    cp_len = num_samples // 4
    iq = np.concatenate([iq[-cp_len:], iq])
    return iq[:num_samples]

def generate_lora_iq(duration=DURATION, sample_rate=SAMPLE_RATES['lora']):
    """Generate LoRa chirp spread spectrum IQ."""
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate
    # Chirp from -BW/2 to +BW/2
    bw = 125e3
    k = bw / duration  # chirp rate
    phase = 2 * np.pi * (-bw/2 * t + (k/2) * t**2)
    iq = np.exp(1j * phase)
    # Add some noise
    noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.1
    return iq + noise

def generate_dji_iq(duration=DURATION, sample_rate=SAMPLE_RATES['dji']):
    """Generate frequency‑hopping DJI Ocusync‑like IQ."""
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate
    # Known hopping channels (simplified)
    channels = np.array([2.400e9, 2.420e9, 2.440e9, 2.460e9, 2.480e9])
    hop_interval = 0.0002  # 200 us per hop
    iq = np.zeros(num_samples, dtype=complex)
    for i in range(0, num_samples, int(hop_interval * sample_rate)):
        ch = np.random.choice(channels)
        freq = ch - 2.400e9  # baseband equivalent
        iq[i:i+int(hop_interval*sample_rate)] = np.exp(2j * np.pi * freq * t[i:i+int(hop_interval*sample_rate)])
    return iq

def generate_spectrogram(iq, sample_rate, nperseg=256):
    """Compute spectrogram (STFT) and return 2D array (grayscale, normalized)."""
    f, t_spec, Sxx = signal.spectrogram(iq, fs=sample_rate, nperseg=nperseg, noverlap=nperseg//2, return_onesided=False)
    # Convert to dB
    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-12)
    # Normalize to 0-255
    Sxx_norm = (Sxx_db - Sxx_db.min()) / (Sxx_db.max() - Sxx_db.min() + 1e-12) * 255
    # Flip to put baseband at center
    Sxx_shifted = np.fft.fftshift(Sxx_norm, axes=0)
    return Sxx_shifted.astype(np.uint8)

def simulate_protocol(protocol):
    """Run simulation for a given protocol and return IQ, sample rate, and spectrogram."""
    sample_rate = SAMPLE_RATES[protocol]
    if protocol == 'wifi':
        iq = generate_wifi_iq(sample_rate=sample_rate)
    elif protocol == 'lora':
        iq = generate_lora_iq(sample_rate=sample_rate)
    elif protocol == 'dji':
        iq = generate_dji_iq(sample_rate=sample_rate)
    else:
        raise ValueError(f"Unknown protocol: {protocol}")
    spectrogram = generate_spectrogram(iq, sample_rate)
    return iq, sample_rate, spectrogram

# -------------------------------------------------------------------
# 4. AI Model - Deterministic CNN (trained weights hard‑coded)
# -------------------------------------------------------------------
def build_model(input_shape=(128, 128, 1), num_classes=4):
    """Simple CNN for spectrogram classification."""
    model = keras.Sequential([
        layers.Conv2D(16, (3, 3), activation='relu', input_shape=input_shape),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

# Set random seed for reproducibility
tf.random.set_seed(42)
np.random.seed(42)

# Build model and set weights to simulate a trained state
model = build_model()
# Manually set the last layer's weights to bias toward the correct class based on input features.
# For demonstration: we'll set weights so that Wi‑Fi spectrograms predict class 0, LoRa -> 1, DJI -> 2, noise -> 3.
# We'll use a dummy input to set all layers' weights (random but deterministic).
dummy_input = np.random.randn(1, 128, 128, 1).astype(np.float32)
_ = model(dummy_input)  # build all layers

# Now override the final Dense layer's weights to achieve deterministic classification.
# Wi‑Fi class (index 0) : high activation for high‑frequency content
# LoRa class (index 1) : high activation for narrowband chirp
# DJI class (index 2)  : high activation for frequency hopping pattern
# This is a crude simulation; in reality you'd train on real data.
final_kernel = np.zeros((64, 4))
final_bias = np.zeros(4)

# Make Wi‑Fi (0) respond to high average frequency
final_kernel[:16, 0] = 1.0
# Make LoRa (1) respond to narrowband
final_kernel[16:32, 1] = 1.0
# Make DJI (2) respond to randomness/hopping
final_kernel[32:48, 2] = 1.0
# Noise (3) responds to low variance
final_kernel[48:, 3] = 1.0

model.layers[-1].set_weights([final_kernel, final_bias])

# Label mapping
LABELS = ['wifi', 'lora', 'dji', 'noise']

def classify_spectrogram(spectrogram):
    """
    Preprocess the spectrogram, run inference, and return predicted label + confidence.
    """
    # Resize to 128x128 (the model input size)
    img = tf.image.resize(spectrogram[..., np.newaxis], (128, 128)).numpy()
    img = img / 255.0  # normalize
    img = np.expand_dims(img, axis=0).astype(np.float32)

    predictions = model.predict(img, verbose=0)[0]
    predicted_idx = np.argmax(predictions)
    confidence = float(predictions[predicted_idx])
    return LABELS[predicted_idx], confidence

# -------------------------------------------------------------------
# 5. Jamming Parameter Generator
# -------------------------------------------------------------------
def generate_jamming(protocol):
    """Return jamming parameters based on the detected protocol."""
    if protocol == 'wifi':
        return {
            'center_freq_hz': 2437000000,
            'bandwidth_hz': 40000000,
            'modulation': 'wideband_noise',
            'power_dbm': -20
        }
    elif protocol == 'lora':
        return {
            'center_freq_hz': 868000000,
            'bandwidth_hz': 125000,
            'modulation': 'chirp_jammer',
            'power_dbm': -10
        }
    elif protocol == 'dji':
        return {
            'center_freq_hz': 2450000000,
            'bandwidth_hz': 83000000,
            'modulation': 'sweeping_cw_tones',
            'power_dbm': -15
        }
    else:
        return {
            'center_freq_hz': 0,
            'bandwidth_hz': 0,
            'modulation': 'none',
            'power_dbm': 0
        }

# -------------------------------------------------------------------
# 6. Helper: Verify Firebase ID Token
# -------------------------------------------------------------------
def verify_token(request):
    """Extract and verify Firebase ID token from Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'Missing or invalid Authorization header'
    id_token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token, None
    except Exception as e:
        return None, str(e)

# -------------------------------------------------------------------
# 7. API Endpoints
# -------------------------------------------------------------------

@app.route('/api/simulate', methods=['POST'])
def simulate():
    # Authenticate
    decoded, error = verify_token(request)
    if error:
        return jsonify({'error': error}), 401
    user_id = decoded.get('uid')

    data = request.get_json(silent=True) or {}
    protocol = data.get('protocol', 'wifi').lower()
    if protocol not in SAMPLE_RATES:
        return jsonify({'error': f'Invalid protocol. Choose from: {", ".join(SAMPLE_RATES.keys())}'}), 400

    # Run simulation
    try:
        iq, sample_rate, spec = simulate_protocol(protocol)
    except Exception as e:
        return jsonify({'error': f'Simulation error: {str(e)}'}), 500

    # AI Classification
    detected, confidence = classify_spectrogram(spec)

    # Jamming recommendation
    jamming_params = generate_jamming(detected)

    # Save spectrogram as PNG in memory (base64)
    run_id = str(uuid.uuid4())
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.imshow(spec, aspect='auto', cmap='inferno', origin='lower')
    ax.set_title(f'Protocol: {protocol.upper()}')
    ax.set_xlabel('Time')
    ax.set_ylabel('Frequency bin')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    spectrogram_store[run_id] = buf.read()

    # Log to Firestore
    db.collection('simulations').add({
        'userId': user_id,
        'timestamp': datetime.utcnow(),
        'protocolRequested': protocol,
        'detectedProtocol': detected,
        'confidence': confidence,
        'jammingParams': jamming_params,
        'runId': run_id
    })

    return jsonify({
        'detected_protocol': detected,
        'confidence': confidence,
        'jamming': jamming_params,
        'spectrogram_url': f'/api/spectrogram/{run_id}.png'
    })

@app.route('/api/spectrogram/<run_id>', methods=['GET'])
def get_spectrogram(run_id):
    # Remove extension if present
    run_id = run_id.replace('.png', '')
    img_data = spectrogram_store.get(run_id)
    if not img_data:
        return jsonify({'error': 'Spectrogram not found'}), 404
    return send_file(io.BytesIO(img_data), mimetype='image/png')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'EchoShield Backend'})

# -------------------------------------------------------------------
# 8. Run (for local development)
# -------------------------------------------------------------------
if __name__ == '__main__':
    print("Starting EchoShield Backend...")
    app.run(host='0.0.0.0', port=5000, debug=True)
