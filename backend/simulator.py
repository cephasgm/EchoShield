import numpy as np

def spectrogram_np(signal, fs, nperseg=128, noverlap=64):
    """Lightweight spectrogram implementation."""
    step = nperseg - noverlap

    if len(signal) < nperseg:
        return np.array([]), np.array([]), np.array([])

    num_segments = (len(signal) - noverlap) // step

    freqs = np.fft.rfftfreq(nperseg, 1 / fs)
    times = np.arange(num_segments) * step / fs

    Sxx = np.zeros((len(freqs), num_segments))

    window = np.hanning(nperseg)

    for i in range(num_segments):
        start = i * step
        segment = signal[start:start + nperseg]

        if len(segment) < nperseg:
            break

        segment = segment * window

        fft_result = np.fft.rfft(np.real(segment))
        Sxx[:, i] = np.abs(fft_result)

    return freqs, times, Sxx


def generate_wifi(duration=0.05, fs=100000):
    t = np.arange(0, duration, 1 / fs)

    signal = (
        np.random.randn(len(t))
        + 1j * np.random.randn(len(t))
    ) / np.sqrt(2)

    return signal


def generate_lora(duration=0.05, fs=100000):
    t = np.arange(0, duration, 1 / fs)

    bw = 10000
    f0 = -bw / 2
    f1 = bw / 2

    k = (f1 - f0) / duration

    phase = 2 * np.pi * (f0 * t + 0.5 * k * t**2)

    return np.exp(1j * phase)


def generate_dji_hopping(duration=0.05, fs=100000):
    t = np.arange(0, duration, 1 / fs)

    signal = np.zeros(len(t), dtype=complex)

    hop_rate = 20
    hop_samples = max(1, int(fs / hop_rate))

    frequencies = np.linspace(5000, 20000, 10)

    for i in range(0, len(t), hop_samples):
        end = min(i + hop_samples, len(t))

        freq = np.random.choice(frequencies)

        signal[i:end] = np.exp(
            2j * np.pi * freq * t[i:end]
        )

    return signal


def generate_iq_and_spectrogram(protocol, duration=0.05):
    """
    Render-friendly simulator.
    ~1000x lighter than the original version.
    """

    if protocol == "wifi":
        fs = 100000
        iq = generate_wifi(duration, fs)

    elif protocol == "lora":
        fs = 100000
        iq = generate_lora(duration, fs)

    elif protocol == "dji":
        fs = 100000
        iq = generate_dji_hopping(duration, fs)

    else:
        raise ValueError("Unknown protocol")

    _, _, Sxx = spectrogram_np(
        iq,
        fs,
        nperseg=128,
        noverlap=64
    )

    if Sxx.size == 0:
        return iq, np.zeros((128, 128))

    Sxx_db = 10 * np.log10(Sxx + 1e-12)

    Sxx_norm = (
        Sxx_db - Sxx_db.min()
    ) / (
        Sxx_db.max() - Sxx_db.min() + 1e-12
    )

    return iq, Sxx_norm
