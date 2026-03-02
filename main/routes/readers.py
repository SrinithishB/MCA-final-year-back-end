from flask import Blueprint, request, jsonify
from config.blockchain import w3, reader_contract, account

readers_bp = Blueprint("readers", __name__)

@readers_bp.route("/api/readers", methods=["GET"])
def get_readers():

    ids = reader_contract.functions.getAllReaders().call()

    readers = []
    for rid in ids:
        r = reader_contract.functions.getReader(rid).call()

        readers.append({
            "readerId": r[0],
            "location": r[1],
            "isActive": r[2]
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

    return jsonify({"success": True})

@readers_bp.route("/api/readers/<reader_id>", methods=["GET"])
def get_reader(reader_id):

    r = reader_contract.functions.getReader(reader_id).call()

    return jsonify({
        "success": True,
        "reader": {
            "readerId": r[0],
            "location": r[1],
            "isActive": r[2]
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

    return jsonify({"success": True})


@readers_bp.route("/api/readers/<reader_id>", methods=["DELETE"])
def delete_reader(reader_id):

    tx = reader_contract.functions.deleteReader(reader_id)\
        .transact({"from": account})

    w3.eth.wait_for_transaction_receipt(tx)

    return jsonify({"success": True})
