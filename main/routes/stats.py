from flask import Blueprint, jsonify
from config.db import drugs_collection, temp_logs_collection, trace_logs_collection

stats_bp = Blueprint("stats", __name__)

@stats_bp.route("/api/stats", methods=["GET"])
def get_stats():
    total = drugs_collection.count_documents({})
    compromised = drugs_collection.count_documents({"isCompromised": True})

    return jsonify({
        "success": True,
        "statistics": {
            "totalDrugs": total,
            "compromisedDrugs": compromised,
            "coldStorageDrugs": drugs_collection.count_documents({"requiresColdStorage": True}),
            "temperatureLogs": temp_logs_collection.count_documents({}),
            "traceabilityLogs": trace_logs_collection.count_documents({}),
            "compromiseRate": f"{(compromised / total * 100):.1f}%" if total else "0%"
        }
    })
