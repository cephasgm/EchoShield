import numpy as np

def classify_spectrogram(spectrogram):
    """
    Simple heuristic classification based on spectrogram characteristics.
    Returns (class_name, confidence).
    """
    # spectrogram is 2D numpy array (freq x time) normalised 0-1
    horizontal_mean = np.mean(spectrogram, axis=0)  # frequency profile

    # Wi‑Fi: broad spectrum, relatively flat over frequency
    wifi_score = 1.0 / (np.std(horizontal_mean) + 0.1)

    # LoRa: chirp – frequency rises over time, so vertical slices show a peak moving
    peak_freqs = np.argmax(spectrogram, axis=0)
    if len(peak_freqs) > 1:
        slope = np.polyfit(np.arange(len(peak_freqs)), peak_freqs, 1)[0]
        lora_score = abs(slope)
    else:
        lora_score = 0

    # DJI: frequency hopping – multiple discrete horizontal stripes
    peak_count = 0
    for col in spectrogram.T:
        peaks = (np.diff(np.sign(np.diff(col))) < 0).sum()
        peak_count += peaks
    dji_score = peak_count / spectrogram.shape[1]

    scores = {
        'wifi': wifi_score,
        'lora': lora_score,
        'dji': dji_score
    }
    predicted = max(scores, key=scores.get)
    total = sum(scores.values()) + 1e-12
    confidence = scores[predicted] / total
    return predicted, confidence


def generate_jamming_signal(protocol):
    """Return jamming parameters based on detected protocol."""
    jamming = {
        'wifi': {
            'center_freq_hz': 2437000000,
            'bandwidth_hz': 40000000,
            'modulation': 'wideband_noise',
            'power_dbm': -20
        },
        'lora': {
            'center_freq_hz': 868000000,
            'bandwidth_hz': 125000,
            'modulation': 'chirp_jammer',
            'power_dbm': -10
        },
        'dji': {
            'center_freq_hz': 2440000000,
            'bandwidth_hz': 83000000,
            'modulation': 'sweeping_tone',
            'power_dbm': -15
        }
    }
    return jamming.get(protocol, jamming['wifi'])