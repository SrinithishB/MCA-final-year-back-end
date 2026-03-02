from flask import Blueprint, request, jsonify
from datetime import datetime
from config.db import temp_logs_collection
from config.blockchain import drug_contract, trace_contract, w3, account

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

    # Always store log in MongoDB
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

        # Get drug limits from blockchain
        drug = drug_contract.functions.getDrug(rfid_tag).call()

        requires_cold = drug[7]
        temp_min = drug[9]
        temp_max = drug[10]
        hum_max = drug[11]

        if requires_cold and (
            temperature < temp_min or
            temperature > temp_max or
            humidity > hum_max
        ):
            is_violation = True
            blink_red = True

            # 1. Store violation on blockchain trace log
            tx = trace_contract.functions.addLog(
                rfid_tag,
                storage_id,
                int(temperature),
                int(humidity),
                True
            ).transact({"from": account})

            w3.eth.wait_for_transaction_receipt(tx)

            # 2. Mark drug compromised in blockchain
            tx2 = drug_contract.functions.setCompromised(
                rfid_tag,
                True
            ).transact({"from": account})

            w3.eth.wait_for_transaction_receipt(tx2)

    return jsonify({
        "success": True,
        "isViolation": is_violation,
        "blinkRed": blink_red,
        "message": "Temperature violation" if is_violation else "Temperature logged"
    })
