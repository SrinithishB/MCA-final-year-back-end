from pymongo import MongoClient

try:
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )
    client.server_info()

    db = client["drug_monitoring"]
    for col in db.list_collection_names():
        db[col].count_documents({})

except Exception:
    pass
