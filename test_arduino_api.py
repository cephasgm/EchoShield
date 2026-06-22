import requests

url = "https://echoshield-api-4x6z.onrender.com/api/arduino/detect"

response = requests.post(
    url,
    json={"protocol": "wifi"},
    timeout=30
)

print("Status:", response.status_code)
print("Response:")
print(response.json())