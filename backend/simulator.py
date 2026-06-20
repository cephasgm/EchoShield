import numpy as np
from scipy.signal import spectrogram

def generate_wifi(duration=0.5, fs=10e6):
    """Generate OFDM-like Wi‑Fi signal (simplified)."""
    t = np.arange(0, duration, 1/fs)
    # 64 subcarriers, QAM symbols (random)
    num_carriers = 64
    symbol_len = int(fs * duration / num_carriers)
    symbols = (np.random.randn(num_carriers) + 1j*np.random.randn(num_carriers)) / np.sqrt(2)
    # Build signal by repeating symbols across time
    signal = np.tile(symbols, (symbol_len, 1)).flatten()[:len(t)]
    return signal

def generate_lora(duration=0.5, fs=1e6):
    """Generate LoRa chirp signal (SF7)."""
    t = np.arange(0, duration, 1/fs)
    BW = 125e3  # 125 kHz
    # Simple up-chirp
    f0 = -BW/2
    f1 = BW/2
    k = (f1 - f0) / duration
    phase = 2 * np.pi * (f0*t + 0.5*k*t**2)
    signal = np.exp(1j * phase)
    return signal

def generate_dji_hopping(duration=0.5, fs=10e6):
    """Simulate DJI‑style frequency hopping: short bursts at random channels."""
    channels = np.linspace(2.4e9, 2.483e9, 40)  # 40 channels
    t = np.arange(0, duration, 1/fs)
    signal = np.zeros(len(t), dtype=complex)
    hop_rate = 100  # hops per second
    hop_samples = int(fs / hop_rate)
    for i in range(0, len(t), hop_samples):
        end = min(i + hop_samples, len(t))
        ch = np.random.choice(channels)
        # Simple CW tone at channel frequency for this hop
        signal[i:end] = np.exp(2j * np.pi * ch * t[i:end])
    return signal

def generate_iq_and_spectrogram(protocol, duration=0.5):
    """Generate IQ signal and its spectrogram for given protocol."""
    if protocol == 'wifi':
        fs = 10e6
        iq = generate_wifi(duration, fs)
    elif protocol == 'lora':
        fs = 1e6
        iq = generate_lora(duration, fs)
    elif protocol == 'dji':
        fs = 10e6
        iq = generate_dji_hopping(duration, fs)
    else:
        raise ValueError('Unknown protocol')

    # Compute spectrogram
    f, t_spec, Sxx = spectrogram(iq, fs, nperseg=256, noverlap=128)
    # Convert to dB scale and normalise to 0-1
    Sxx_dB = 10 * np.log10(np.abs(Sxx) + 1e-12)
    Sxx_norm = (Sxx_dB - Sxx_dB.min()) / (Sxx_dB.max() - Sxx_dB.min() + 1e-12)
    return iq, Sxx_norm
