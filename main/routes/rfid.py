from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from config.db import trace_logs_collection
from config.blockchain import (
    trace_contract,
    drug_contract,
    reader_contract,
    w3,
    account
)
from utils.serializer import serialize_doc

rfid_bp = Blueprint("rfid", __name__)


# -----------------------------------------------------
# POST: Scan RFID
# -----------------------------------------------------
@rfid_bp.route("/api/rfid", methods=["POST"])
def receive_rfid():
    data = request.json or {}

    rfid_tag = data.get("tagID")
    reader_id = data.get("readerID", "READER_001")

    if not rfid_tag:
        return jsonify({
            "success": False,
            "message": "RFID tag required"
        }), 400

    current_timestamp = int(datetime.utcnow().timestamp())

    try:
        # Get Drug from Blockchain
        try:
            drug = drug_contract.functions.getDrug(rfid_tag).call()
        except Exception:
            drug = None

        # Get Reader from Blockchain
        try:
            reader = reader_contract.functions.getReader(reader_id).call()
            location = reader[1]
        except Exception:
            location = "Unknown Location"

        # ---------------- Counterfeit ----------------
        if not drug or drug[0] == "":

            trace_logs_collection.insert_one({
                "timestamp": current_timestamp,
                "rfidTag": rfid_tag,
                "drugName": None,
                "manufacturer": None,
                "readerID": reader_id,
                "location": location,
                "isCompromised": True,
                "event": "COUNTERFEIT_DETECTED"
            })

            tx = trace_contract.functions.addLog(
                rfid_tag,
                reader_id,
                0,
                0,
                True
            ).transact({"from": account})

            w3.eth.wait_for_transaction_receipt(tx)

            return jsonify({
                "success": False,
                "message": "Counterfeit medicine found",
                "blinkRed": True
            }), 404

        # ---------------- Valid Drug ----------------
        drug_name = drug[1]
        manufacturer = drug[3]
        compromised = drug[8]

        trace_logs_collection.insert_one({
            "timestamp": current_timestamp,
            "rfidTag": rfid_tag,
            "drugName": drug_name,
            "manufacturer": manufacturer,
            "readerID": reader_id,
            "location": location,
            "isCompromised": compromised
        })

        tx = trace_contract.functions.addLog(
            rfid_tag,
            reader_id,
            0,
            0,
            compromised
        ).transact({"from": account})

        w3.eth.wait_for_transaction_receipt(tx)

        return jsonify({
            "success": True,
            "rfidTag": rfid_tag,
            "drugName": drug_name,
            "manufacturer": manufacturer,
            "location": location,
            "blinkRed": compromised,
            "message": "Drug compromised" if compromised else "Scan logged"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# -----------------------------------------------------
# GET: Latest RFID Scan (Last 5 Minutes)
# -----------------------------------------------------
@rfid_bp.route("/api/rfid/latest", methods=["GET"])
def get_latest_rfid():

    five_minutes_ago = int(datetime.utcnow().timestamp()) - 300

    log = list(
        trace_logs_collection
        .find({"timestamp": {"$gte": five_minutes_ago}})
        .sort("timestamp", -1)
        .limit(1)
    )

    if not log:
        return jsonify({
            "success": False,
            "message": "No recent RFID scans"
        }), 404

    return jsonify({
        "success": True,
        "scan": serialize_doc(log[0])
    })