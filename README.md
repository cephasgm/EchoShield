# EchoShield – Anti‑Drone RF Simulator & Jamming AI

**CephasGM** | AI‑powered drone defence simulation.  
No hardware required – everything runs in your browser as a Progressive Web App.

## Project Overview

EchoShield simulates real‑world drone communication protocols (Wi‑Fi, LoRa, DJI) and uses an embedded neural network to detect, classify, and recommend optimal jamming signals. The entire electronic warfare scenario is software‑only, designed for rapid prototyping and later integration with software‑defined radios (SDRs).

### Key Features
- **Pure client‑side simulation** – Spectrograms and AI run entirely in your browser (TensorFlow.js).
- **Firebase Authentication** – Email/password & Google sign‑in.
- **Firestore Logging** – Every simulation run is stored securely.
- **Progressive Web App** – Installs on desktop & mobile, works offline.
- **Cloudflare Pages** – Fast, secure hosting on your custom domain `cephasgm.org`.

## Project Structure

EchoShield/
├── index.html # Landing page
├── signup.html # Sign‑up page
├── signin.html # Sign‑in page
├── dashboard.html # Simulation dashboard (protected)
├── manifest.json # PWA manifest
├── sw.js # Service Worker (offline caching)
├── _headers # Cloudflare security headers
├── _redirects # Cloudflare API proxy rules
├── icon-192.png # PWA icon (192x192)
├── icon-512.png # PWA icon (512x512)
├── backend/ # Optional Python backend (fully functional)
│ ├── app.py
│ ├── simulator.py
│ ├── ai_model.py
│ ├── train_model.py
│ ├── requirements.txt
│ ├── test_app.py
│ └── firebase-service-account.json 
└── README.md

## Quick Start (No Terminal Required)

EchoShield is a static website – just deploy the frontend files to **Cloudflare Pages** and it works.

### 1. Firebase Setup
You already completed this. For reference, your Firebase config is embedded in every HTML file. Make sure the following services are enabled:

- **Authentication** → Email/Password & Google providers.
- **Firestore Database** → Security rules:
rules_version = '2';
service cloud.firestore {
match /databases/{database}/documents {
match /simulations/{document=**} {
allow read, write: if request.auth != null;
}
}
}

- **Authorized domains** → `cephasgm.org` and `localhost` added.

### 2. Deploy to Cloudflare Pages
1. Push this repository to GitHub.
2. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/).
3. Go to **Workers & Pages** → **Pages** → **Connect to Git**.
4. Choose your repository and set:
 - **Build command**: _(leave blank)_
 - **Build output directory**: `/`
5. Under **Custom domains**, add `cephasgm.org` (and `www.cephasgm.org` if desired).
6. Cloudflare will automatically provision an SSL certificate and deploy your site.

The files `_headers` and `_redirects` will be picked up automatically and apply the correct security headers and API proxy rules.

### 3. Test the PWA
- Open `https://cephasgm.org` in Chrome/Edge.
- Sign up, then run a simulation from the Dashboard.
- You should see a **“Install”** prompt in the address bar – click to install the app.
- Turn off your internet; the app still loads (offline support via Service Worker).

## Client‑Side Simulation (Default)

The dashboard (`dashboard.html`) uses **TensorFlow.js** and custom signal‑processing code to generate spectrograms and classify them **directly in your browser**. No backend is required.

- **Spectrograms** are drawn on a canvas.
- **AI model** is a lightweight CNN built with TensorFlow.js and hard‑coded weights.
- **Firestore logging** happens directly from the browser (authenticated user).

## Optional: Running the Python Backend

If you need a more realistic simulation (NumPy‑based IQ generation, scipy spectrograms, Flask API), the `backend/` folder contains a fully functional Python server.

### Requirements
- Python 3.10+
- A `firebase-service-account.json` file (download from Firebase Console → Project Settings → Service accounts).

### Setup (Local or Cloud)
1. Navigate to the `backend/` folder.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
Place your firebase-service-account.json in the same folder.

Start the server:

bash
python app.py
The API runs on http://localhost:5000.

To use this backend with the frontend, update API_BASE_URL in dashboard.html to point to your backend URL (e.g., https://api.cephasgm.org if you deploy it).

Customisation
Branding: All pages contain CephasGM in the header and footer.

Icons: Replace icon-192.png and icon-512.png with your own logo if needed.

Firebase config: Already set to your project ID – no changes needed.

Domain: The _redirects file proxies /api/* to https://api.cephasgm.org. If you deploy the backend, update the target URL.

Testing (Backend)
bash
cd backend
pytest test_app.py -v
All tests pass with mocked Firebase services.

License & Ownership
Copyright © 2025 Cephas GM | Innovating for Tomorrow.
All rights reserved. The algorithm IP, including the jamming AI logic, belongs to the project owner.
