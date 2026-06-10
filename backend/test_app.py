"""
test_app.py – Unit tests for EchoShield backend.
Uses pytest, Flask test client, and mocks for Firebase.
"""

import json
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app import app, LABELS, model

@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- Mock Firebase Auth ---
def mock_verify_id_token(token):
    if token == 'valid_token':
        return {'uid': 'test_user_123'}
    raise ValueError('Invalid token')

# --- Tests ---
def test_simulate_wifi(client):
    """POST /api/simulate with wifi protocol returns correct structure."""
    with patch('app.firebase_auth.verify_id_token', side_effect=mock_verify_id_token):
        response = client.post(
            '/api/simulate',
            json={'protocol': 'wifi'},
            headers={'Authorization': 'Bearer valid_token'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'detected_protocol' in data
        assert data['detected_protocol'] in LABELS
        assert 'confidence' in data
        assert 0 <= data['confidence'] <= 1
        assert 'jamming' in data
        assert 'center_freq_hz' in data['jamming']
        assert 'bandwidth_hz' in data['jamming']
        assert 'modulation' in data['jamming']
        assert 'power_dbm' in data['jamming']
        assert 'spectrogram_url' in data

def test_simulate_lora(client):
    with patch('app.firebase_auth.verify_id_token', side_effect=mock_verify_id_token):
        response = client.post(
            '/api/simulate',
            json={'protocol': 'lora'},
            headers={'Authorization': 'Bearer valid_token'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['detected_protocol'] in LABELS

def test_simulate_dji(client):
    with patch('app.firebase_auth.verify_id_token', side_effect=mock_verify_id_token):
        response = client.post(
            '/api/simulate',
            json={'protocol': 'dji'},
            headers={'Authorization': 'Bearer valid_token'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['detected_protocol'] in LABELS

def test_simulate_invalid_protocol(client):
    with patch('app.firebase_auth.verify_id_token', side_effect=mock_verify_id_token):
        response = client.post(
            '/api/simulate',
            json={'protocol': 'bluetooth'},
            headers={'Authorization': 'Bearer valid_token'}
        )
        assert response.status_code == 400

def test_simulate_no_token(client):
    response = client.post('/api/simulate', json={'protocol': 'wifi'})
    assert response.status_code == 401

def test_simulate_bad_token(client):
    with patch('app.firebase_auth.verify_id_token', side_effect=mock_verify_id_token):
        response = client.post(
            '/api/simulate',
            json={'protocol': 'wifi'},
            headers={'Authorization': 'Bearer bad_token'}
        )
        assert response.status_code == 401

def test_model_classification():
    """Ensure model returns a valid class for a dummy spectrogram."""
    dummy_spec = np.random.rand(128, 128).astype(np.uint8)
    # Import ai_model functions directly
    from ai_model import classify_spectrogram
    label, conf = classify_spectrogram(dummy_spec, model)
    assert label in LABELS
    assert 0 <= conf <= 1

def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'

# --- Firestore mock (optional) ---
def test_firestore_logging_mocked(client):
    """Mock Firestore add() and verify it is called."""
    with patch('app.firebase_auth.verify_id_token', side_effect=mock_verify_id_token), \
         patch('app.db.collection') as mock_collection:
        mock_doc = MagicMock()
        mock_collection.return_value.add = mock_doc
        response = client.post(
            '/api/simulate',
            json={'protocol': 'wifi'},
            headers={'Authorization': 'Bearer valid_token'}
        )
        assert response.status_code == 200
        # Check that add was called once
        mock_doc.assert_called_once()
