import pytest
from app import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    assert rv.json['status'] == 'ok'

@patch('app.verify_token')
def test_simulate_no_auth(mock_verify, client):
    mock_verify.return_value = (None, 'Invalid token')
    rv = client.post('/api/simulate', json={'protocol': 'wifi'})
    assert rv.status_code == 401

@patch('app.verify_token')
@patch('app.db.collection')
def test_simulate_wifi(mock_db, mock_verify, client):
    mock_verify.return_value = ('test_uid', None)
    mock_add = MagicMock()
    mock_db.return_value.add = mock_add

    rv = client.post('/api/simulate', json={'protocol': 'wifi'})
    assert rv.status_code == 200
    data = rv.json
    assert 'detected_protocol' in data
    assert 'confidence' in data
    assert 'jamming' in data
    assert 'spectrogram_url' in data
    # Check that jamming matches wifi
    assert data['jamming']['modulation'] == 'wideband_noise'
    mock_add.assert_called_once()
