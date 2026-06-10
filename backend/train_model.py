"""
train_model.py – EchoShield Synthetic Training
Generates 2000 spectrograms (500 per class) and trains the CNN.
Exports model.h5 and label_encoder.pkl.
"""

import os
import pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split

# ---------- 1. Spectrogram Generator ----------
def generate_wifi_spec():
    """Create a 128x128 spectrogram mimicking Wi‑Fi (wideband, random subcarriers)."""
    spec = np.random.rand(128, 128) * 0.4
    # Add some structured OFDM-like vertical lines
    for _ in range(20):
        col = np.random.randint(20, 108)
        spec[col:col+2, :] += 0.6
    return np.clip(spec, 0, 1)

def generate_lora_spec():
    """Create a 128x128 spectrogram with diagonal chirp pattern."""
    spec = np.zeros((128, 128))
    t = np.linspace(0, 1, 128)
    for i in range(128):
        freq_idx = int(64 + 48 * np.sin(2 * np.pi * t[i] + np.random.randn() * 0.05))
        freq_idx = max(0, min(127, freq_idx))
        spec[freq_idx, i] = 0.9
    return spec

def generate_dji_spec():
    """Create a 128x128 spectrogram with frequency‑hopping horizontal lines."""
    spec = np.zeros((128, 128))
    hop_duration = 16
    for start in range(0, 128, hop_duration):
        freq = np.random.randint(10, 118)
        spec[freq:freq+3, start:start+hop_duration] = 0.8
    return spec

def generate_noise_spec():
    """Random noise spectrogram."""
    return np.random.rand(128, 128) * 0.5

# ---------- 2. Dataset Creation ----------
def create_dataset(n_per_class=500):
    X, y = [], []
    generators = {
        'wifi': generate_wifi_spec,
        'lora': generate_lora_spec,
        'dji': generate_dji_spec,
        'noise': generate_noise_spec
    }
    for label, gen_func in generators.items():
        for _ in range(n_per_class):
            spec = gen_func()
            X.append(spec)
            y.append(label)
    # Encode labels
    label_to_idx = {l: i for i, l in enumerate(generators.keys())}
    y_enc = np.array([label_to_idx[lbl] for lbl in y])
    X = np.array(X).reshape(-1, 128, 128, 1)
    return X, y_enc, list(label_to_idx.keys())

# ---------- 3. Model Definition ----------
def build_model(input_shape=(128, 128, 1), num_classes=4):
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

# ---------- 4. Training ----------
if __name__ == '__main__':
    print("Generating synthetic dataset...")
    X, y, class_names = create_dataset(500)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
    model = build_model(num_classes=len(class_names))
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_val, y_val), verbose=1)
    
    # Save model and labels
    model.save('model.h5')
    with open('label_encoder.pkl', 'wb') as f:
        pickle.dump(class_names, f)
    
    print("Training complete. model.h5 and label_encoder.pkl saved.")
    print(f"Classes: {class_names}")
