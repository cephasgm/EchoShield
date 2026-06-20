import numpy as np

def spectrogram_np(signal, fs, nperseg=256, noverlap=128):
    """Compute spectrogram using numpy FFT."""
    step = nperseg - noverlap
    num_segments = (len(signal) - noverlap) // step
    if num_segments <= 0:
        return np.array([]), np.array([]), np.array([])
    
    freqs = np.fft.rfftfreq(nperseg, 1/fs)
    times = np.arange(num_segments) * step / fs
    Sxx = np.zeros((len(freqs), num_segments))
    
    window = np.hanning(nperseg)
    for i in range(num_segments):
        start = i * step
        segment = signal[start:start+nperseg] * window
        fft_result = np.fft.rfft(segment)
        Sxx[:, i] = np.abs(fft_result)
    
    return freqs, times, Sxx

def generate_wifi(duration=0.5, fs=10e6):
    """Generate OFDM-like Wi‑Fi signal (simplified)."""
    t = np.arange(0, duration, 1/fs)
    num_carriers = 64
    symbol_len = int(fs * duration / num_carriers)
    symbols = (np.random.randn(num_carriers) + 1j*np.random.randn(num_carriers)) / np.sqrt(2)
    signal = np.tile(symbols, (symbol_len, 1)).flatten()[:len(t)]
    return signal

def generate_lora(duration=0.5, fs=1e6):
    """Generate LoRa chirp signal (SF7)."""
    t = np.arange(0, duration, 1/fs)
    BW = 125e3  # 125 kHz
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

    # Compute spectrogram using our own numpy function
    f, t_spec, Sxx = spectrogram_np(iq, fs, nperseg=256, noverlap=128)
    if Sxx.size == 0:
        # Fallback: create a dummy spectrogram of size 128x128
        Sxx_norm = np.zeros((128,128))
    else:
        Sxx_dB = 10 * np.log10(Sxx + 1e-12)
        Sxx_norm = (Sxx_dB - Sxx_dB.min()) / (Sxx_dB.max() - Sxx_dB.min() + 1e-12)
        # Resize to 128x128 for the AI model (if needed) – the classifier expects 128x128
        # We'll just use the raw size; the classifier currently uses the whole array.
    return iq, Sxx_norm