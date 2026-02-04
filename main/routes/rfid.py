from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from config.db import drugs_collection, readers_collection, trace_logs_collection
from utils.serializer import serialize_doc

rfid_bp = Blueprint("rfid", __name__)

@rfid_bp.route("/api/rfid", methods=["POST"])
def receive_rfid():
    data = request.json or {}

    rfid_tag = data.get("tagID")
    reader_id = data.get("readerID", "READER_001")

    reader = readers_collection.find_one({"readerId": reader_id})
    location = reader["location"] if reader else "Unknown Location"

    drug = drugs_collection.find_one({"rfidTag": rfid_tag})

    # Counterfeit detection
    if not drug:
        trace_logs_collection.insert_one({
            "timestamp": datetime.now(),
            "rfidTag": rfid_tag,
            "drugName": "UNKNOWN",
            "batchNumber": "UNKNOWN",
            "location": location,
            "readerID": reader_id,
            "isCompromised": True,
            "event": "COUNTERFEIT_DETECTED"
        })

        return jsonify({
            "success": False,
            "message": "Counterfeit medicine found",
            "location": location,
            "blinkRed": True
        }), 404

    drugs_collection.update_one(
        {"rfidTag": rfid_tag},
        {"$set": {
            "currentLocation": location,
            "lastUpdated": datetime.now()
        }}
    )

    trace_logs_collection.insert_one({
        "timestamp": datetime.now(),
        "rfidTag": rfid_tag,
        "drugName": drug["drugName"],
        "batchNumber": drug["batchNumber"],
        "location": location,
        "readerID": reader_id,
        "isCompromised": drug.get("isCompromised", False)
    })

    compromised = drug.get("isCompromised", False)

    return jsonify({
        "success": True,
        "location": location,
        "blinkRed": compromised,
        "message": "Drug compromised" if compromised else "Scan logged"
    })


@rfid_bp.route("/api/rfid/latest", methods=["GET"])
def get_latest_rfid():
    since = datetime.now() - timedelta(minutes=5)

    log = list(
        trace_logs_collection
        .find({"timestamp": {"$gte": since}})
        .sort("timestamp", -1)
        .limit(1)
    )

    if not log:
        return jsonify({
            "success": False,
            "message": "No recent RFID scans (last 5 minutes)"
        }), 404

    return jsonify({
        "success": True,
        "scan": serialize_doc(log[0])
    })
