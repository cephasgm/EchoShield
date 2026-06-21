import os
import io
import traceback

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, firestore, auth

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulator import generate_iq_and_spectrogram
from ai_model import classify_spectrogram, generate_jamming_signal

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "https://echoshield.cephasgm.org"
        }
    }
)

# ==================================================
# Firebase
# ==================================================

secret_path = "/etc/secrets/firebase-service-account.json"

if not firebase_admin._apps:

    if os.path.exists(secret_path):
        cred = credentials.Certificate(secret_path)
    else:
        cred = credentials.Certificate(
            "firebase-service-account.json"
        )

    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==================================================
# Helpers
# ==================================================

def log_detection(document):

    try:

        doc_ref = db.collection(
            "simulations"
        ).add(document)

        print(
            "FIRESTORE WRITE SUCCESS:",
            doc_ref
        )

        return True

    except Exception as e:

        print(
            "FIRESTORE WRITE FAILED:",
            str(e)
        )

        return False

def verify_token(req):

    auth_header = req.headers.get(
        "Authorization"
    )

    if (
        not auth_header
        or
        not auth_header.startswith(
            "Bearer "
        )
    ):
        return (
            None,
            "Missing or invalid Authorization header"
        )

    try:

        token = auth_header.split(
            "Bearer "
        )[1]

        decoded_token = (
            auth.verify_id_token(
                token
            )
        )

        return (
            decoded_token["uid"],
            None
        )

    except Exception as e:

        return (
            None,
            str(e)
        )


# ==================================================
# Routes
# ==================================================

@app.route("/")
def home():

    return jsonify({
        "status": "ok",
        "message": "EchoShield API"
    })


@app.route("/api/health")
def health():

    return jsonify({
        "status": "ok"
    })


# ==================================================
# Dashboard Simulation Route
# ==================================================

@app.route(
    "/api/simulate",
    methods=["POST"]
)
def simulate():

    try:

        uid, err = verify_token(
            request
        )

        if err:
            return jsonify({
                "error": err
            }), 401

        data = request.get_json(
            silent=True
        )

        if (
            not data
            or
            "protocol" not in data
        ):
            return jsonify({
                "error": "Missing protocol"
            }), 400

        protocol = (
            data["protocol"]
            .lower()
        )

        iq, spec = (
            generate_iq_and_spectrogram(
                protocol
            )
        )

        pred, conf = (
            classify_spectrogram(
                spec
            )
        )

        jam = (
            generate_jamming_signal(
                pred
            )
        )

        return jsonify({

            "detected_protocol":
                pred,

            "confidence":
                float(conf),

            "jamming":
                jam,

            "spectrogram_url":
                "/api/spectrogram/current.png"
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ==================================================
# Arduino Detection Route
# ==================================================

@app.route(
    "/api/arduino/detect",
    methods=["POST"]
)
def arduino_detect():

    try:

        data = (
            request.get_json(
                silent=True
            ) or {}
        )

        protocol = (
            data.get(
                "protocol",
                "wifi"
            ).lower()
        )

        distance_cm = int(
            data.get(
                "distance_cm",
                0
            )
        )

        zone = data.get(
            "zone",
            "UNKNOWN"
        )

        iq, spec = (
            generate_iq_and_spectrogram(
                protocol
            )
        )

        pred, conf = (
            classify_spectrogram(
                spec
            )
        )

        jam = (
            generate_jamming_signal(
                pred
            )
        )

        threat = (
            float(conf)
            > 0.60
        )

        document = {

            "userId":
                "arduino_hardware",

            "userEmail":
                "hardware@echoshield.local",

            "timestamp":
                firestore.SERVER_TIMESTAMP,

            "source":
                "arduino",

            "protocolRequested":
                protocol,

            "detectedProtocol":
                pred,

            "confidence":
                float(conf),

            "distance_cm":
                distance_cm,

            "zone":
                zone,

            "threat":
                threat,

            "jammingParams":
                jam
        }

        log_detection(
            document
        )

        print(
            f"Arduino Detection | "
            f"Distance={distance_cm}cm "
            f"Zone={zone} "
            f"Threat={threat}"
        )

        return jsonify({

            "detected_protocol":
                pred,

            "confidence":
                float(conf),

            "distance_cm":
                distance_cm,

            "zone":
                zone,

            "jamming":
                jam,

            "threat":
                threat
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ==================================================
# Spectrogram Image Route
# ==================================================

@app.route(
    "/api/spectrogram/<filename>"
)
def spectrogram(filename):

    try:

        protocol = "wifi"

        _, spec = (
            generate_iq_and_spectrogram(
                protocol
            )
        )

        img = io.BytesIO()

        plt.figure(
            figsize=(6, 4)
        )

        plt.imshow(
            spec,
            aspect="auto",
            origin="lower",
            cmap="inferno"
        )

        plt.axis("off")

        plt.tight_layout(
            pad=0
        )

        plt.savefig(
            img,
            format="png",
            bbox_inches="tight",
            pad_inches=0
        )

        plt.close()

        img.seek(0)

        return send_file(
            img,
            mimetype="image/png"
        )

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ==================================================
# CORS
# ==================================================

@app.after_request
def add_cors(response):

    response.headers[
        "Access-Control-Allow-Origin"
    ] = (
        "https://echoshield.cephasgm.org"
    )

    response.headers[
        "Access-Control-Allow-Headers"
    ] = (
        "Authorization, Content-Type"
    )

    response.headers[
        "Access-Control-Allow-Methods"
    ] = (
        "GET, POST, OPTIONS"
    )

    response.headers[
        "Access-Control-Allow-Credentials"
    ] = "true"

    return response


# ==================================================
# Main
# ==================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )