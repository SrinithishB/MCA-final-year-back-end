from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["drug_monitoring"]

drugs_collection = db["drugs"]
readers_collection = db["rfid_readers"]

drugs_collection.delete_many({})
readers_collection.delete_many({})

drugs_collection.insert_many([
    {
        "rfidTag": "096F776C",
        "drugName": "Insulin Vial",
        "batchNumber": "BATCH-INS-001",
        "category": "Hormone",
        "manufacturer": "Pharma Corp",
        "expiryDate": "2026-12-31",
        "requiresColdStorage": True,
        "temperatureMin": 2.0,
        "temperatureMax": 8.0,
        "humidityMin": 30.0,
        "humidityMax": 60.0,
        "isCompromised": False,
        "compromisedReason": None,
        "compromisedTimestamp": None,
        "currentLocation": "Pharmacy Storage",
        "addedDate": datetime.now(),
        "lastUpdated": datetime.now()
    },
    {
        "rfidTag": "A3B2C1D4",
        "drugName": "COVID-19 Vaccine",
        "batchNumber": "BATCH-VAC-002",
        "category": "Vaccine",
        "manufacturer": "VaxCo",
        "expiryDate": "2026-06-30",
        "requiresColdStorage": True,
        "temperatureMin": -80.0,
        "temperatureMax": -60.0,
        "humidityMin": 20.0,
        "humidityMax": 50.0,
        "isCompromised": False,
        "compromisedReason": None,
        "compromisedTimestamp": None,
        "currentLocation": "Ultra Cold Storage",
        "addedDate": datetime.now(),
        "lastUpdated": datetime.now()
    },
    {
        "rfidTag": "12345678",
        "drugName": "Paracetamol Tablets",
        "batchNumber": "BATCH-PAR-003",
        "category": "Pain Relief",
        "manufacturer": "Generic Pharma",
        "expiryDate": "2027-01-01",
        "requiresColdStorage": False,
        "temperatureMin": None,
        "temperatureMax": None,
        "humidityMin": None,
        "humidityMax": None,
        "isCompromised": False,
        "compromisedReason": None,
        "compromisedTimestamp": None,
        "currentLocation": "General Storage",
        "addedDate": datetime.now(),
        "lastUpdated": datetime.now()
    }
])

readers_collection.insert_many([
    {"readerId": "READER_001", "location": "Pharmacy Storage", "isActive": True},
    {"readerId": "READER_002", "location": "ICU Ward", "isActive": True},
    {"readerId": "READER_003", "location": "Emergency Room", "isActive": True}
])
