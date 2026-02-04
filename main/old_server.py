from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import json

app = Flask(__name__)
CORS(app)

# MongoDB Connection
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['drug_monitoring']
    
    # Collections
    drugs_collection = db['drugs']
    temp_logs_collection = db['temperature_logs']
    trace_logs_collection = db['traceability_logs']
    readers_collection = db['rfid_readers']
    
    print('✅ Connected to MongoDB')
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    exit(1)

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

# Initialize default RFID readers
def init_readers():
    if readers_collection.count_documents({}) == 0:
        default_readers = [
            {"readerId": "READER_001", "location": "Pharmacy Storage", "isActive": True},
            {"readerId": "READER_002", "location": "ICU Ward", "isActive": True},
            {"readerId": "READER_003", "location": "Emergency Room", "isActive": True}
        ]
        readers_collection.insert_many(default_readers)
        print('✅ Default RFID readers initialized')

# Root endpoint
@app.route('/')
def home():
    return jsonify({
        'message': 'Drug Monitoring Server Running with MongoDB',
        'database': 'MongoDB',
        'collections': {
            'drugs': drugs_collection.count_documents({}),
            'temperature_logs': temp_logs_collection.count_documents({}),
            'traceability_logs': trace_logs_collection.count_documents({}),
            'rfid_readers': readers_collection.count_documents({})
        },
        'endpoints': {
            'dashboard': '/dashboard',
            'drugs': '/api/drugs',
            'temperature': '/api/temperature',
            'rfid': '/api/rfid',
            'stats': '/api/stats'
        }
    })

# API: Add new drug
@app.route('/api/drugs', methods=['POST'])
def add_drug():
    try:
        drug_data = request.json
        
        # Validate required fields
        required = ['rfidTag', 'drugName', 'batchNumber']
        if not all(field in drug_data for field in required):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Check if RFID tag already exists
        existing = drugs_collection.find_one({'rfidTag': drug_data['rfidTag']})
        if existing:
            return jsonify({'success': False, 'message': 'RFID tag already exists'}), 400
        
        # Add default values
        drug_data.setdefault('requiresColdStorage', False)
        drug_data.setdefault('isCompromised', False)
        drug_data.setdefault('compromisedReason', None)
        drug_data.setdefault('compromisedTimestamp', None)
        drug_data.setdefault('currentLocation', 'Pharmacy Storage')
        drug_data.setdefault('category', 'General')
        drug_data.setdefault('manufacturer', 'Unknown')
        drug_data['addedDate'] = datetime.now()
        drug_data['lastUpdated'] = datetime.now()
        
        # Insert into MongoDB
        result = drugs_collection.insert_one(drug_data)
        drug_data['_id'] = str(result.inserted_id)
        
        print(f'✅ New drug added: {drug_data["drugName"]} ({drug_data["rfidTag"]})')
        
        return jsonify({'success': True, 'message': 'Drug added', 'data': serialize_doc(drug_data)}), 201
        
    except Exception as e:
        print(f'❌ Error adding drug: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get all drugs
@app.route('/api/drugs', methods=['GET'])
def get_drugs():
    try:
        drugs = list(drugs_collection.find())
        for drug in drugs:
            serialize_doc(drug)
        
        return jsonify({'success': True, 'count': len(drugs), 'drugs': drugs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get single drug by RFID
@app.route('/api/drugs/<rfid_tag>', methods=['GET'])
def get_drug(rfid_tag):
    try:
        drug = drugs_collection.find_one({'rfidTag': rfid_tag})
        if drug:
            return jsonify({'success': True, 'drug': serialize_doc(drug)})
        return jsonify({'success': False, 'message': 'Drug not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Update drug
@app.route('/api/drugs/<rfid_tag>', methods=['PUT'])
def update_drug(rfid_tag):
    try:
        update_data = request.json
        update_data['lastUpdated'] = datetime.now()
        
        result = drugs_collection.update_one(
            {'rfidTag': rfid_tag},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Drug updated'})
        return jsonify({'success': False, 'message': 'Drug not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Temperature monitoring
@app.route('/api/temperature', methods=['POST'])
def receive_temperature():
    try:
        data = request.json
        
        temperature = float(data.get('temperature', 0))
        humidity = float(data.get('humidity', 0))
        storage_id = data.get('storageID', 'UNKNOWN')
        rfid_tag = data.get('rfidTag', None)
        
        # Create temperature log
        temp_log = {
            'timestamp': datetime.now(),
            'storageID': storage_id,
            'temperature': temperature,
            'humidity': humidity,
            'rfidTag': rfid_tag
        }
        
        # Insert log
        temp_logs_collection.insert_one(temp_log)
        
        # Check if drug requires monitoring
        is_violation = False
        blink_red = False
        compromised_reason = None
        
        if rfid_tag:
            drug = drugs_collection.find_one({'rfidTag': rfid_tag})
            
            if drug and drug.get('requiresColdStorage'):
                temp_min = drug.get('temperatureMin', 0)
                temp_max = drug.get('temperatureMax', 100)
                hum_min = drug.get('humidityMin', 0)
                hum_max = drug.get('humidityMax', 100)
                
                # Check violation
                temp_violation = temperature < temp_min or temperature > temp_max
                hum_violation = humidity < hum_min or humidity > hum_max
                
                if temp_violation or hum_violation:
                    is_violation = True
                    blink_red = True
                    
                    compromised_reason = f"Temperature: {temperature}°C (Required: {temp_min}-{temp_max}°C)"
                    if hum_violation:
                        compromised_reason += f", Humidity: {humidity}% (Required: {hum_min}-{hum_max}%)"
                    
                    # Update drug status
                    drugs_collection.update_one(
                        {'rfidTag': rfid_tag},
                        {
                            '$set': {
                                'isCompromised': True,
                                'compromisedReason': compromised_reason,
                                'compromisedTimestamp': datetime.now(),
                                'lastUpdated': datetime.now()
                            }
                        }
                    )
                    
                    print(f'⚠️  VIOLATION: {drug["drugName"]} compromised!')
                    print(f'   Reason: {compromised_reason}')
        
        print(f'📊 Temperature logged: {temperature}°C, {humidity}% - Storage: {storage_id}')
        
        return jsonify({
            'success': True,
            'isViolation': is_violation,
            'blinkRed': blink_red,
            'message': 'Temperature violation - drug compromised!' if is_violation else 'Temperature logged'
        }), 200
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# API: RFID scan (traceability)
@app.route('/api/rfid', methods=['POST'])
def receive_rfid():
    try:
        data = request.json
        
        rfid_tag = data.get('tagID', 'UNKNOWN')
        reader_id = data.get('readerID', 'READER_001')
        
        # Get reader location
        reader = readers_collection.find_one({'readerId': reader_id})
        location = reader['location'] if reader else 'Unknown Location'
        
        # Find drug
        drug = drugs_collection.find_one({'rfidTag': rfid_tag})
        
        if not drug:
            print(f'⚠️  Unknown RFID tag scanned: {rfid_tag}')
            return jsonify({
                'success': False, 
                'message': 'Drug not found - Please add this drug to database first',
                'rfidTag': rfid_tag,
                'blinkRed': False
            }), 404
        
        # Update location
        drugs_collection.update_one(
            {'rfidTag': rfid_tag},
            {
                '$set': {
                    'currentLocation': location,
                    'lastUpdated': datetime.now()
                }
            }
        )
        
        # Log traceability
        trace_log = {
            'timestamp': datetime.now(),
            'rfidTag': rfid_tag,
            'drugName': drug['drugName'],
            'batchNumber': drug['batchNumber'],
            'location': location,
            'readerID': reader_id,
            'isCompromised': drug.get('isCompromised', False)
        }
        
        trace_logs_collection.insert_one(trace_log)
        
        blink_red = drug.get('isCompromised', False)
        
        print(f'🏷️  RFID Scan: {drug["drugName"]} at {location}')
        if blink_red:
            print(f'   ⚠️  WARNING: Drug is COMPROMISED!')
        
        return jsonify({
            'success': True,
            'drug': serialize_doc(drug),
            'location': location,
            'blinkRed': blink_red,
            'message': 'Drug is compromised!' if blink_red else 'Scan logged'
        }), 200
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get temperature logs
@app.route('/api/temperature/logs', methods=['GET'])
def get_temp_logs():
    try:
        limit = int(request.args.get('limit', 100))
        logs = list(temp_logs_collection.find().sort('timestamp', -1).limit(limit))
        
        for log in logs:
            serialize_doc(log)
            if 'timestamp' in log and isinstance(log['timestamp'], datetime):
                log['timestamp'] = log['timestamp'].isoformat()
        
        return jsonify({'success': True, 'count': len(logs), 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get traceability logs
@app.route('/api/traceability/logs', methods=['GET'])
def get_trace_logs():
    try:
        limit = int(request.args.get('limit', 100))
        logs = list(trace_logs_collection.find().sort('timestamp', -1).limit(limit))
        
        for log in logs:
            serialize_doc(log)
            if 'timestamp' in log and isinstance(log['timestamp'], datetime):
                log['timestamp'] = log['timestamp'].isoformat()
        
        return jsonify({'success': True, 'count': len(logs), 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get all readers
@app.route('/api/readers', methods=['GET'])
def get_readers():
    try:
        readers = list(readers_collection.find())
        for reader in readers:
            serialize_doc(reader)
        
        return jsonify({'success': True, 'count': len(readers), 'readers': readers})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Add new reader
@app.route('/api/readers', methods=['POST'])
def add_reader():
    try:
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        reader_id = data.get('readerId')
        location = data.get('location')

        if not reader_id or not location:
            return jsonify({'success': False, 'message': 'readerId and location are required'}), 400

        if readers_collection.find_one({'readerId': reader_id}):
            return jsonify({'success': False, 'message': 'Reader already exists'}), 409

        reader_data = {
            'readerId': reader_id,
            'location': location,
            'isActive': data.get('isActive', True),
            'addedDate': datetime.now()
        }

        result = readers_collection.insert_one(reader_data)
        reader_data['_id'] = str(result.inserted_id)
        
        print(f'✅ New reader added: {reader_id} at {location}')

        return jsonify({
            'success': True,
            'message': 'Reader added successfully',
            'data': reader_data
        }), 201

    except Exception as e:
        print(f'❌ Error adding reader: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get single reader
@app.route('/api/readers/<reader_id>', methods=['GET'])
def get_reader(reader_id):
    try:
        reader = readers_collection.find_one({'readerId': reader_id})
        if reader:
            return jsonify({'success': True, 'reader': serialize_doc(reader)})
        return jsonify({'success': False, 'message': 'Reader not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Update reader
@app.route('/api/readers/<reader_id>', methods=['PUT'])
def update_reader(reader_id):
    try:
        update_data = request.json
        
        if not update_data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Only allow updating certain fields
        allowed_fields = ['location', 'isActive']
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
            return jsonify({'success': False, 'message': 'No valid fields to update'}), 400
        
        filtered_data['lastUpdated'] = datetime.now()
        
        result = readers_collection.update_one(
            {'readerId': reader_id},
            {'$set': filtered_data}
        )
        
        if result.modified_count > 0:
            print(f'📍 Reader {reader_id} updated: {filtered_data}')
            return jsonify({'success': True, 'message': 'Reader updated'})
        
        if result.matched_count > 0:
            return jsonify({'success': True, 'message': 'Reader unchanged (same data)'})
        
        return jsonify({'success': False, 'message': 'Reader not found'}), 404
        
    except Exception as e:
        print(f'❌ Error updating reader: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Delete reader
@app.route('/api/readers/<reader_id>', methods=['DELETE'])
def delete_reader(reader_id):
    try:
        result = readers_collection.delete_one({'readerId': reader_id})
        
        if result.deleted_count > 0:
            print(f'🗑️  Reader {reader_id} deleted')
            return jsonify({'success': True, 'message': 'Reader deleted'})
        
        return jsonify({'success': False, 'message': 'Reader not found'}), 404
        
    except Exception as e:
        print(f'❌ Error deleting reader: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Get statistics
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_drugs = drugs_collection.count_documents({})
        compromised_drugs = drugs_collection.count_documents({'isCompromised': True})
        cold_storage_drugs = drugs_collection.count_documents({'requiresColdStorage': True})
        temp_logs_count = temp_logs_collection.count_documents({})
        trace_logs_count = trace_logs_collection.count_documents({})
        
        return jsonify({
            'success': True,
            'statistics': {
                'totalDrugs': total_drugs,
                'compromisedDrugs': compromised_drugs,
                'coldStorageDrugs': cold_storage_drugs,
                'temperatureLogs': temp_logs_count,
                'traceabilityLogs': trace_logs_count,
                'compromiseRate': f'{(compromised_drugs/total_drugs*100):.1f}%' if total_drugs > 0 else '0%'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Clear all data (for testing)
@app.route('/api/clear', methods=['POST'])
def clear_data():
    try:
        temp_logs_collection.delete_many({})
        trace_logs_collection.delete_many({})
        print('\n🗑️  Temperature and traceability logs cleared!\n')
        return jsonify({'success': True, 'message': 'Logs cleared'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Serve dashboard HTML
@app.route('/dashboard')
def dashboard():
    return send_file('dashboard.html')

if __name__ == '__main__':
    init_readers()
    
    print('\n')
    print('╔════════════════════════════════════════╗')
    print('║  Drug Monitoring Server Started ✅      ║')
    print('║  Database: MongoDB                     ║')
    print('║                                        ║')
    print('║  Server: http://localhost:5000         ║')
    print('║  Dashboard: http://localhost:5000/dashboard ║')
    print('║                                        ║')
    print('║  MongoDB Collections:                  ║')
    print(f'║    - Drugs: {drugs_collection.count_documents({}):>6}                      ║')
    print(f'║    - Temp Logs: {temp_logs_collection.count_documents({}):>6}                ║')
    print(f'║    - Trace Logs: {trace_logs_collection.count_documents({}):>6}               ║')
    print('║                                        ║')
    print('║  Press CTRL+C to quit                  ║')
    print('╚════════════════════════════════════════╝')
    print('\n')
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)