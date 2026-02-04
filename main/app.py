from flask import Flask, jsonify
from flask_cors import CORS

from routes.readers import readers_bp
from routes.drugs import drugs_bp
from routes.temperature import temperature_bp
from routes.rfid import rfid_bp
from routes.logs import logs_bp
from routes.stats import stats_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(readers_bp)
app.register_blueprint(drugs_bp)
app.register_blueprint(temperature_bp)
app.register_blueprint(rfid_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(stats_bp)

@app.route("/")
def home():
    endpoints = []

    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            endpoints.append({
                "endpoint": rule.endpoint,
                "methods": sorted(rule.methods - {"HEAD", "OPTIONS"}),
                "path": rule.rule
            })

    return jsonify({
        "success": True,
        "service": "Drug Monitoring Server",
        "endpoints": endpoints
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
