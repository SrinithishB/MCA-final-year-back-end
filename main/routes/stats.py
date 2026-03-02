from flask import Blueprint, jsonify
from config.blockchain import drug_contract, trace_contract
from config.db import temp_logs_collection

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/api/stats", methods=["GET"])
def get_stats():

    try:
        # Drug Statistics (Blockchain)
        tags = drug_contract.functions.getAllTags().call()
        total = len(tags)

        compromised = 0
        cold_storage = 0

        for tag in tags:
            drug = drug_contract.functions.getDrug(tag).call()

            if drug[7]:
                cold_storage += 1

            if drug[8]:
                compromised += 1

        # Temperature Logs (MongoDB)
        temperature_logs = temp_logs_collection.count_documents({})

        # Trace Logs (Blockchain)
        trace_logs = trace_contract.functions.totalLogs().call()

        return jsonify({
            "success": True,
            "statistics": {
                "totalDrugs": total,
                "compromisedDrugs": compromised,
                "coldStorageDrugs": cold_storage,
                "temperatureLogs": temperature_logs,
                "traceabilityLogs": trace_logs,
                "compromiseRate": f"{(compromised / total * 100):.1f}%" if total else "0%"
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500