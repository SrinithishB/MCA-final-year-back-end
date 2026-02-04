from flask import Blueprint, request, jsonify
from datetime import datetime
from config.db import drugs_collection
from utils.serializer import serialize_doc

drugs_bp = Blueprint("drugs", __name__)

@drugs_bp.route("/api/drugs", methods=["POST"])
def add_drug():
    data = request.json

    required_fields = [
        "rfidTag",
        "drugName",
        "batchNumber",
        "manufacturerName",
        "manufactureDate",
        "expiryDate"
    ]

    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400

    if drugs_collection.find_one({"rfidTag": data["rfidTag"]}):
        return jsonify({
            "success": False,
            "message": "RFID already exists"
        }), 409

    try:
        data["manufactureDate"] = datetime.strptime(
            data["manufactureDate"], "%Y-%m-%d"
        )
        data["expiryDate"] = datetime.strptime(
            data["expiryDate"], "%Y-%m-%d"
        )
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid date format (YYYY-MM-DD required)"
        }), 400

    data.setdefault("description", "")
    data.setdefault("requiresColdStorage", False)
    data.setdefault("isCompromised", False)

    if data["requiresColdStorage"]:
        cold_fields = ["temperatureMin", "temperatureMax", "humidityMax"]

        if not all(field in data for field in cold_fields):
            return jsonify({
                "success": False,
                "message": "Cold storage drugs require temperatureMin, temperatureMax and humidityMax"
            }), 400

        try:
            data["temperatureMin"] = float(data["temperatureMin"])
            data["temperatureMax"] = float(data["temperatureMax"])
            data["humidityMax"] = float(data["humidityMax"])
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Temperature and humidity must be numeric values"
            }), 400

        if data["temperatureMin"] >= data["temperatureMax"]:
            return jsonify({
                "success": False,
                "message": "temperatureMin must be less than temperatureMax"
            }), 400

        if not (0 <= data["humidityMax"] <= 100):
            return jsonify({
                "success": False,
                "message": "humidityMax must be between 0 and 100"
            }), 400
    else:
        data.pop("temperatureMin", None)
        data.pop("temperatureMax", None)
        data.pop("humidityMax", None)

    data["addedDate"] = datetime.now()
    data["lastUpdated"] = datetime.now()

    result = drugs_collection.insert_one(data)
    data["_id"] = str(result.inserted_id)

    return jsonify({
        "success": True,
        "data": serialize_doc(data)
    }), 201


@drugs_bp.route("/api/drugs", methods=["GET"])
def get_drugs():
    drugs = [serialize_doc(d) for d in drugs_collection.find()]
    return jsonify({
        "success": True,
        "count": len(drugs),
        "drugs": drugs
    })
