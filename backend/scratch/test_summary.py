import requests

BASE_URL = "http://localhost:5000/v1"
# Usamos el token que sabemos que existe por el código de vinculación simulado
DEVICE_TOKEN = "token-simulado-juan-perez"

def test_summary():
    headers = {"X-Device-Token": DEVICE_TOKEN}
    response = requests.get(f"{BASE_URL}/attendance/summary", headers=headers)
    
    if response.status_code == 200:
        print("OK: Test Exitoso")
        print(response.json())
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_summary()
