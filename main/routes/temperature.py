from flask import Blueprint, request, jsonify
from datetime import datetime
from config.db import temp_logs_collection, drugs_collection

temperature_bp = Blueprint("temperature", __name__)

@temperature_bp.route("/api/temperature", methods=["POST"])
def receive_temperature():
    data = request.json or {}

    try:
        temperature = float(data.get("temperature", 0))
        humidity = float(data.get("humidity", 0))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid temperature or humidity"
        }), 400

    storage_id = data.get("storageID", "UNKNOWN")
    rfid_tag = data.get("rfidTag")

    temp_logs_collection.insert_one({
        "timestamp": datetime.now(),
        "storageID": storage_id,
        "temperature": temperature,
        "humidity": humidity,
        "rfidTag": rfid_tag
    })

    is_violation = False
    blink_red = False

    if rfid_tag:
        drug = drugs_collection.find_one({"rfidTag": rfid_tag})

        if drug and drug.get("requiresColdStorage"):
            temp_min = drug.get("temperatureMin", 0)
            temp_max = drug.get("temperatureMax", 100)
            hum_max = drug.get("humidityMax", 100)

            if temperature < temp_min or temperature > temp_max or humidity > hum_max:
                is_violation = True
                blink_red = True

                drugs_collection.update_one(
                    {"rfidTag": rfid_tag},
                    {"$set": {
                        "isCompromised": True,
                        "compromisedTimestamp": datetime.now(),
                        "lastUpdated": datetime.now()
                    }}
                )

    return jsonify({
        "success": True,
        "isViolation": is_violation,
        "blinkRed": blink_red,
        "message": "Temperature violation" if is_violation else "Temperature logged"
    })
