from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["drug_monitoring"]

drugs_collection = db["drugs"]
temp_logs_collection = db["temperature_logs"]
trace_logs_collection = db["traceability_logs"]
readers_collection = db["rfid_readers"]
