"""
EchoShield RF Simulator - Signal Generation Module
Generates synthetic IQ samples for Wi‑Fi, LoRa, and DJI protocols.
"""

import numpy as np
from scipy import signal as scipy_signal

SAMPLE_RATES = {
    'wifi': 20e6,
    'lora': 1e6,
    'dji': 10e6
}

DEFAULT_DURATION = 0.001  # 1 ms


def generate_wifi_iq(duration=DEFAULT_DURATION, sample_rate=None):
    """Generate OFDM‑like Wi‑Fi IQ samples with 64 subcarriers and cyclic prefix."""
    if sample_rate is None:
        sample_rate = SAMPLE_RATES['wifi']
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate
    
    iq = np.zeros(num_samples, dtype=complex)
    for subcarrier in range(-32, 32):
        if subcarrier == 0:
            continue
        symbol = (np.random.randn() + 1j * np.random.randn()) / np.sqrt(2)
        freq = subcarrier * 312.5e3
        iq += symbol * np.exp(2j * np.pi * freq * t)
    
    # Cyclic prefix
    cp_len = num_samples // 4
    iq = np.concatenate([iq[-cp_len:], iq])
    return iq[:num_samples]


def generate_lora_iq(duration=DEFAULT_DURATION, sample_rate=None):
    """Generate LoRa chirp spread spectrum IQ samples."""
    if sample_rate is None:
        sample_rate = SAMPLE_RATES['lora']
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate
    
    bw = 125e3
    k = bw / duration
    phase = 2 * np.pi * (-bw / 2 * t + (k / 2) * t ** 2)
    iq = np.exp(1j * phase)
    
    noise = (np.random.randn(num_samples) + 1j * np.random.randn(num_samples)) * 0.1
    return iq + noise


def generate_dji_iq(duration=DEFAULT_DURATION, sample_rate=None):
    """Generate frequency‑hopping DJI Ocusync‑like IQ samples."""
    if sample_rate is None:
        sample_rate = SAMPLE_RATES['dji']
    num_samples = int(duration * sample_rate)
    t = np.arange(num_samples) / sample_rate
    
    channels = np.array([2.400e9, 2.420e9, 2.440e9, 2.460e9, 2.480e9])
    hop_interval = 0.0002
    iq = np.zeros(num_samples, dtype=complex)
    
    for i in range(0, num_samples, int(hop_interval * sample_rate)):
        ch = np.random.choice(channels)
        freq = ch - 2.400e9
        end = min(i + int(hop_interval * sample_rate), num_samples)
        iq[i:end] = np.exp(2j * np.pi * freq * t[i:end])
    
    return iq


def generate_spectrogram(iq, sample_rate, nperseg=256):
    """Compute spectrogram (STFT) and return normalised 2D array."""
    f, t_spec, Sxx = scipy_signal.spectrogram(
        iq, fs=sample_rate, nperseg=nperseg,
        noverlap=nperseg // 2, return_onesided=False
    )
    Sxx_db = 10 * np.log10(np.abs(Sxx) + 1e-12)
    Sxx_norm = (Sxx_db - Sxx_db.min()) / (Sxx_db.max() - Sxx_db.min() + 1e-12) * 255
    Sxx_shifted = np.fft.fftshift(Sxx_norm, axes=0)
    return Sxx_shifted.astype(np.uint8)


def simulate_protocol(protocol, duration=DEFAULT_DURATION):
    """Run simulation for a protocol and return IQ, sample rate, and spectrogram."""
    sample_rate = SAMPLE_RATES.get(protocol)
    if sample_rate is None:
        raise ValueError(f"Unknown protocol: {protocol}")
    
    generators = {
        'wifi': generate_wifi_iq,
        'lora': generate_lora_iq,
        'dji': generate_dji_iq
    }
    iq = generators[protocol](duration=duration, sample_rate=sample_rate)
    spectrogram = generate_spectrogram(iq, sample_rate)
    return iq, sample_rate, spectrogram
