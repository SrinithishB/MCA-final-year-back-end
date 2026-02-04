from flask import Blueprint, jsonify, request
from config.db import temp_logs_collection, trace_logs_collection
from utils.serializer import serialize_doc

logs_bp = Blueprint("logs", __name__)

@logs_bp.route("/api/temperature/logs", methods=["GET"])
def get_temp_logs():
    limit = int(request.args.get("limit", 100))
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


@logs_bp.route("/api/traceability/logs/<rfid_tag>", methods=["GET"])
def get_trace_logs_by_rfid(rfid_tag):
    logs = list(
        trace_logs_collection
        .find({"rfidTag": rfid_tag})
        .sort("timestamp", -1)
    )

    return jsonify({
        "success": True,
        "rfidTag": rfid_tag,
        "count": len(logs),
        "logs": [serialize_doc(log) for log in logs]
    })


@logs_bp.route("/api/traceability/logs", methods=["GET"])
def get_trace_logs():
    limit = int(request.args.get("limit", 100))
    logs = list(
        trace_logs_collection
        .find()
        .sort("timestamp", -1)
        .limit(limit)
    )

    return jsonify({
        "success": True,
        "count": len(logs),
        "logs": [serialize_doc(log) for log in logs]
    })
