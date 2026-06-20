import serial
import time

PORT = "COM8"

print(f"Connecting to {PORT}...")

ser = serial.Serial(PORT, 9600, timeout=1)

time.sleep(2)

print("Turning LED ON...")
ser.write(b"JAM:ON\n")

time.sleep(5)

print("Turning LED OFF...")
ser.write(b"JAM:OFF\n")

time.sleep(1)

ser.close()

print("Done.")