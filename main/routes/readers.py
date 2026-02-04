from flask import Blueprint, request, jsonify
from datetime import datetime
from config.db import readers_collection
from utils.serializer import serialize_doc

readers_bp = Blueprint("readers", __name__)

@readers_bp.route("/api/readers", methods=["GET"])
def get_readers():
    readers = [serialize_doc(r) for r in readers_collection.find()]
    return jsonify({
        "success": True,
        "count": len(readers),
        "readers": readers
    })


@readers_bp.route("/api/readers", methods=["POST"])
def add_reader():
    data = request.json
    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided"
        }), 400

    reader_id = data.get("readerId")
    location = data.get("location")

    if not reader_id or not location:
        return jsonify({
            "success": False,
            "message": "readerId and location required"
        }), 400

    if readers_collection.find_one({"readerId": reader_id}):
        return jsonify({
            "success": False,
            "message": "Reader already exists"
        }), 409

    reader = {
        "readerId": reader_id,
        "location": location,
        "isActive": data.get("isActive", True),
        "addedDate": datetime.now()
    }

    result = readers_collection.insert_one(reader)
    reader["_id"] = str(result.inserted_id)

    return jsonify({
        "success": True,
        "message": "Reader added",
        "data": reader
    }), 201


@readers_bp.route("/api/readers/<reader_id>", methods=["GET"])
def get_reader(reader_id):
    reader = readers_collection.find_one({"readerId": reader_id})
    if not reader:
        return jsonify({
            "success": False,
            "message": "Reader not found"
        }), 404

    return jsonify({
        "success": True,
        "reader": serialize_doc(reader)
    })


@readers_bp.route("/api/readers/<reader_id>", methods=["PUT"])
def update_reader(reader_id):
    data = request.json or {}
    update = {
        k: v for k, v in data.items()
        if k in ["location", "isActive"]
    }

    if not update:
        return jsonify({
            "success": False,
            "message": "No valid fields"
        }), 400

    update["lastUpdated"] = datetime.now()

    result = readers_collection.update_one(
        {"readerId": reader_id},
        {"$set": update}
    )

    if result.matched_count == 0:
        return jsonify({
            "success": False,
            "message": "Reader not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Reader updated"
    })


@readers_bp.route("/api/readers/<reader_id>", methods=["DELETE"])
def delete_reader(reader_id):
    result = readers_collection.delete_one({"readerId": reader_id})

    if result.deleted_count == 0:
        return jsonify({
            "success": False,
            "message": "Reader not found"
        }), 404

    return jsonify({
        "success": True,
        "message": "Reader deleted"
    })
