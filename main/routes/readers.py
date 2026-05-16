from flask import Blueprint, request, jsonify
from config.blockchain import w3, reader_contract, account
from config.db import readers_collection

readers_bp = Blueprint("readers", __name__)

@readers_bp.route("/api/readers", methods=["GET"])
def get_readers():

    ids = reader_contract.functions.getAllReaders().call()

    readers = []
    for rid in ids:
        r = reader_contract.functions.getReader(rid).call()
        mongo_doc = readers_collection.find_one({"readerId": r[0]}) or {}

        readers.append({
            "readerId": r[0],
            "location": r[1],
            "isActive": r[2],
            "city": mongo_doc.get("city", "")
        })

    return jsonify({
        "success": True,
        "count": len(readers),
        "readers": readers
    })


@readers_bp.route("/api/readers", methods=["POST"])
def add_reader():

    data = request.json

    tx = reader_contract.functions.addReader(
        data["readerId"],
        data["location"],
        data.get("isActive", True)
    ).transact({"from": account})

    w3.eth.wait_for_transaction_receipt(tx)

    readers_collection.update_one(
        {"readerId": data["readerId"]},
        {"$set": {"readerId": data["readerId"], "city": data.get("city", "")}},
        upsert=True
    )

    return jsonify({"success": True})

@readers_bp.route("/api/readers/<reader_id>", methods=["GET"])
def get_reader(reader_id):

    r = reader_contract.functions.getReader(reader_id).call()
    mongo_doc = readers_collection.find_one({"readerId": r[0]}) or {}

    return jsonify({
        "success": True,
        "reader": {
            "readerId": r[0],
            "location": r[1],
            "isActive": r[2],
            "city": mongo_doc.get("city", "")
        }
    })


@readers_bp.route("/api/readers/<reader_id>", methods=["PUT"])
def update_reader(reader_id):

    data = request.json

    tx = reader_contract.functions.updateReader(
        reader_id,
        data["location"],
        data.get("isActive", True)
    ).transact({"from": account})

    w3.eth.wait_for_transaction_receipt(tx)

    if "city" in data:
        readers_collection.update_one(
            {"readerId": reader_id},
            {"$set": {"city": data["city"]}},
            upsert=True
        )

    return jsonify({"success": True})


@readers_bp.route("/api/readers/<reader_id>", methods=["DELETE"])
def delete_reader(reader_id):

    tx = reader_contract.functions.deleteReader(reader_id)\
        .transact({"from": account})

    w3.eth.wait_for_transaction_receipt(tx)

    return jsonify({"success": True})
