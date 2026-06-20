import serial
import time

PORT = "COM8"

print(f"Connecting to {PORT}...")

ser = serial.Serial(PORT, 9600, timeout=1)

time.sleep(2)

print("EchoShield Local Pipeline Running")

while True:

    line = ser.readline().decode("utf-8").strip()

    if not line:
        continue

    print(f"Arduino: {line}")

    if line == "DRONE_DETECTED":

        print("Threat detected")

        time.sleep(1)

        print("Activating jammer")

        ser.write(b"JAM:ON\n")

        time.sleep(5)

        ser.write(b"JAM:OFF\n")

        print("Jammer deactivated")