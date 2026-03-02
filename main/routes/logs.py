from flask import Blueprint, jsonify, request
from config.blockchain import trace_contract, drug_contract, reader_contract
from config.db import temp_logs_collection
from utils.serializer import serialize_doc

logs_bp = Blueprint("logs", __name__)


# Temperature Logs (MongoDB)
@logs_bp.route("/api/temperature/logs", methods=["GET"])
def get_temp_logs():
    limit = min(int(request.args.get("limit", 100)), 500)

    logs = list(
        temp_logs_collection
        .find()
        .sort("timestamp", -1)
        .limit(limit)
    )

    return jsonify({
        "success": True,
        "count": len(logs),
        "logs": [serialize_doc(log) for log in logs]
    })


# All Trace Logs (Blockchain + Enriched)
@logs_bp.route("/api/traceability/logs", methods=["GET"])
def get_trace_logs():

    try:
        total = trace_contract.functions.totalLogs().call()
        formatted_logs = []

        for i in range(total):
            log = trace_contract.functions.getLog(i).call()

            rfid_tag = log[0]
            reader_id = log[1]

            # Fetch Drug Details
            try:
                drug = drug_contract.functions.getDrug(rfid_tag).call()
                drug_name = drug[1]
                batch_number = drug[2]
                manufacturer = drug[3]
            except:
                drug_name = None
                batch_number = None
                manufacturer = None

            # Fetch Reader Location
            try:
                reader = reader_contract.functions.getReader(reader_id).call()
                location = reader[1]
            except:
                location = "Unknown Location"

            formatted_logs.append({
                "rfidTag": rfid_tag,
                "drugName": drug_name,
                "batchNumber": batch_number,
                "manufacturer": manufacturer,
                "readerID": reader_id,
                "location": location,
                "temperature": log[2],
                "humidity": log[3],
                "violated": log[4],
                "timestamp": log[5]
            })

        return jsonify({
            "success": True,
            "count": total,
            "logs": formatted_logs
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# Trace Logs By RFID (Blockchain + Enriched)
@logs_bp.route("/api/traceability/logs/<rfid_tag>", methods=["GET"])
def get_trace_logs_by_rfid(rfid_tag):

    try:
        total = trace_contract.functions.totalLogs().call()
        filtered_logs = []

        for i in range(total):
            log = trace_contract.functions.getLog(i).call()

            if log[0] == rfid_tag:

                reader_id = log[1]

                # Drug Details
                try:
                    drug = drug_contract.functions.getDrug(rfid_tag).call()
                    drug_name = drug[1]
                    batch_number = drug[2]
                    manufacturer = drug[3]
                except:
                    drug_name = None
                    batch_number = None
                    manufacturer = None

                # Reader Location
                try:
                    reader = reader_contract.functions.getReader(reader_id).call()
                    location = reader[1]
                except:
                    location = "Unknown Location"

                filtered_logs.append({
                    "rfidTag": rfid_tag,
                    "drugName": drug_name,
                    "batchNumber": batch_number,
                    "manufacturer": manufacturer,
                    "readerID": reader_id,
                    "location": location,
                    "temperature": log[2],
                    "humidity": log[3],
                    "violated": log[4],
                    "timestamp": log[5]
                })

        return jsonify({
            "success": True,
            "rfidTag": rfid_tag,
            "count": len(filtered_logs),
            "logs": filtered_logs
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500