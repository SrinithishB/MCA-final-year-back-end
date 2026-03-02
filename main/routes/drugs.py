from flask import Blueprint, request, jsonify
from config.blockchain import w3, drug_contract, account

drugs_bp = Blueprint("drugs", __name__)

@drugs_bp.route("/api/drugs", methods=["POST"])
def add_drug():

    data = request.json

    tx = drug_contract.functions.addDrug(
        data["rfidTag"],
        data["drugName"],
        data["batchNumber"],
        data["manufacturerName"],
        data["manufactureDate"],
        data["expiryDate"],
        data.get("description",""),
        data.get("requiresColdStorage", False),
        data.get("isCompromised", False),
        int(data.get("temperatureMin", 0)),
        int(data.get("temperatureMax", 0)),
        int(data.get("humidityMax", 0))
    ).transact({"from": account})

    w3.eth.wait_for_transaction_receipt(tx)

    return jsonify({"success": True})


@drugs_bp.route("/api/drugs", methods=["GET"])
def get_drugs():

    tags = drug_contract.functions.getAllTags().call()

    drugs = []

    for tag in tags:
        d = drug_contract.functions.getDrug(tag).call()

        drugs.append({
            "rfidTag": d[0],
            "drugName": d[1],
            "batchNumber": d[2],
            "manufacturerName": d[3],
            "manufactureDate": d[4],
            "expiryDate": d[5],
            "description": d[6],
            "requiresColdStorage": d[7],
            "isCompromised": d[8],
            "temperatureMin": d[9],
            "temperatureMax": d[10],
            "humidityMax": d[11]
        })

    return jsonify({
        "success": True,
        "drugs": drugs
    })
