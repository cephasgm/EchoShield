import numpy as np

def _simple_stft(iq, fs, nperseg=256, noverlap=128):
    """
    Minimal short‑time Fourier transform using only NumPy.
    Returns frequencies, times, spectrogram (linear magnitude).
    """
    n = len(iq)
    step = nperseg - noverlap
    if step <= 0:
        raise ValueError('noverlap must be < nperseg')
    window = np.hanning(nperseg)
    freqs = np.fft.fftfreq(nperseg, 1/fs)
    times = []
    segments = []
    for start in range(0, n - nperseg + 1, step):
        segment = iq[start:start+nperseg] * window
        spectrum = np.fft.fft(segment)
        segments.append(np.abs(spectrum))
        times.append(start / fs)
    # Keep only positive frequencies
    pos_mask = freqs >= 0
    freqs = freqs[pos_mask]
    Sxx = np.array(segments)[:, pos_mask].T  # freq x time
    return freqs, np.array(times), Sxx

def generate_wifi(duration=0.5, fs=10e6):
    """Generate OFDM‑like Wi‑Fi signal (simplified)."""
    t = np.arange(0, duration, 1/fs)
    num_carriers = 64
    symbol_len = int(fs * duration / num_carriers)
    symbols = (np.random.randn(num_carriers) + 1j*np.random.randn(num_carriers)) / np.sqrt(2)
    signal = np.tile(symbols, (symbol_len, 1)).flatten()[:len(t)]
    return signal

def generate_lora(duration=0.5, fs=1e6):
    """Generate LoRa chirp signal (SF7)."""
    t = np.arange(0, duration, 1/fs)
    BW = 125e3
    f0 = -BW/2
    f1 = BW/2
    k = (f1 - f0) / duration
    phase = 2 * np.pi * (f0*t + 0.5*k*t**2)
    signal = np.exp(1j * phase)
    return signal

def generate_dji_hopping(duration=0.5, fs=10e6):
    """Simulate DJI‑style frequency hopping."""
    channels = np.linspace(2.4e9, 2.483e9, 40)
    t = np.arange(0, duration, 1/fs)
    signal = np.zeros(len(t), dtype=complex)
    hop_rate = 100
    hop_samples = int(fs / hop_rate)
    for i in range(0, len(t), hop_samples):
        end = min(i + hop_samples, len(t))
        ch = np.random.choice(channels)
        signal[i:end] = np.exp(2j * np.pi * ch * t[i:end])
    return signal

def generate_iq_and_spectrogram(protocol, duration=0.5):
    """Generate IQ signal and its spectrogram for the given protocol."""
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

    # Compute spectrogram with our NumPy STFT
    freqs, times, Sxx = _simple_stft(iq, fs, nperseg=256, noverlap=128)
    # Convert to dB and normalise 0‑1
    Sxx_dB = 10 * np.log10(Sxx + 1e-12)
    Sxx_norm = (Sxx_dB - Sxx_dB.min()) / (Sxx_dB.max() - Sxx_dB.min() + 1e-12)
    return iq, Sxx_norm