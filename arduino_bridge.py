import serial
import requests
import time

# ==========================================
# EchoShield Arduino Bridge
# CephasGM
# ==========================================

SERIAL_PORT = "COM8"
BAUD_RATE = 9600

API_URL = (
    "https://echoshield-api-4x6z.onrender.com"
    "/api/arduino/detect"
)

print("===================================")
print("EchoShield Arduino Bridge Starting")
print("===================================")

print("Connecting to Arduino...")

ser = serial.Serial(
    SERIAL_PORT,
    BAUD_RATE,
    timeout=1
)

time.sleep(2)

print("Connected.")
print("Waiting for detections...")
print()

# ==========================================
# Zone Calculator
# ==========================================

def get_zone(distance_cm):

    if distance_cm < 50:
        return "THREAT"

    elif distance_cm < 100:
        return "WARNING"

    elif distance_cm < 150:
        return "MONITOR"

    return "CLEAR"


# ==========================================
# Main Loop
# ==========================================

while True:

    try:

        line = (
            ser.readline()
            .decode("utf-8", errors="ignore")
            .strip()
        )

        if not line:
            continue

        print("Arduino:", line)

        # ----------------------------------
        # Detection Event
        # ----------------------------------

        if line.startswith("DETECTED:"):

            try:

                distance_cm = int(
                    line.split(":")[1]
                )

            except:

                print(
                    "Invalid distance format"
                )

                continue

            zone = get_zone(distance_cm)

            print()
            print("===================================")
            print("TARGET DETECTED")
            print("Distance:", distance_cm, "cm")
            print("Zone:", zone)
            print("===================================")

            payload = {
                "protocol": "wifi",
                "distance_cm": distance_cm,
                "zone": zone
            }

            try:

                print(
                    "Sending detection "
                    "to EchoShield AI..."
                )

                response = requests.post(
                    API_URL,
                    json=payload,
                    timeout=30
                )

                print(
                    "HTTP:",
                    response.status_code
                )

                if response.status_code == 200:

                    data = response.json()

                    print()
                    print("AI Response")
                    print("--------------------------------")

                    print(
                        "Protocol:",
                        data.get(
                            "detected_protocol"
                        )
                    )

                    print(
                        "Confidence:",
                        round(
                            data.get(
                                "confidence",
                                0
                            ) * 100,
                            2
                        ),
                        "%"
                    )

                    print(
                        "Threat:",
                        data.get("threat")
                    )

                    print(
                        "Zone:",
                        data.get(
                            "zone",
                            zone
                        )
                    )

                    print(
                        "Distance:",
                        data.get(
                            "distance_cm",
                            distance_cm
                        ),
                        "cm"
                    )

                    if data.get("threat"):

                        print()
                        print(
                            "THREAT DETECTED"
                        )

                        print(
                            "Activating "
                            "Countermeasure..."
                        )

                        ser.write(
                            b"JAM:ON\n"
                        )

                        time.sleep(5)

                        ser.write(
                            b"JAM:OFF\n"
                        )

                        print(
                            "Countermeasure "
                            "Deactivated"
                        )

                    else:

                        print()
                        print(
                            "No Threat"
                        )

                else:

                    print(
                        "API Error:",
                        response.text
                    )

            except Exception as e:

                print()
                print(
                    "Network Error:"
                )

                print(str(e))

            print()

        # ----------------------------------
        # Status Messages
        # ----------------------------------

        elif line == "JAM_ACTIVE":

            print(
                "[ARDUINO] "
                "Countermeasure Active"
            )

        elif line == "JAM_OFF":

            print(
                "[ARDUINO] "
                "Countermeasure Off"
            )

    except KeyboardInterrupt:

        print()
        print(
            "Bridge stopped by user."
        )

        break

    except Exception as e:

        print(
            "Bridge Error:",
            str(e)
        )

        time.sleep(1)

# ==========================================
# Cleanup
# ==========================================

try:
    ser.close()
except:
    pass