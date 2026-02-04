import serial
import serial.tools.list_ports
import requests
import json
import time

SERVER_URL = "http://localhost:5000/api/rfid"

def find_arduino():
    for port in serial.tools.list_ports.comports():
        if any(k in port.description.upper() for k in ["ARDUINO", "CH340", "USB"]):
            print(f"[INFO] Arduino detected on {port.device}")
            return port.device
    return None

def main():
    port = find_arduino()
    if not port:
        port = input("Enter COM port: ")

    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"[CONNECTED] Serial port opened: {port}")
        time.sleep(2)

        while True:
            if ser.in_waiting:
                line = ser.readline().decode(errors="ignore").strip()
                print(f"[SERIAL] Received: {line}")

                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        print(f"[JSON] Parsed data: {data}")

                        response = requests.post(
                            SERVER_URL, json=data, timeout=5
                        )

                        print(f"[HTTP] Status Code: {response.status_code}")

                        if response.status_code == 200:
                            result = response.json()
                            print(f"[SERVER RESPONSE] {result}")

                            if result.get("blinkRed"):
                                ser.write(b"BLINK_RED\n")
                                print("[ACTION] Sent BLINK_RED to Arduino")

                        else:
                            print("[ERROR] Server returned non-200 response")

                    except json.JSONDecodeError:
                        print("[ERROR] Invalid JSON received")
                    except requests.RequestException as e:
                        print(f"[ERROR] HTTP request failed: {e}")

    except KeyboardInterrupt:
        print("\n[EXIT] Program stopped by user")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()
            print("[CLOSED] Serial port closed")

if __name__ == "__main__":
    main()
