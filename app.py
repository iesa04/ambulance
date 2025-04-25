from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from datetime import datetime, timedelta
import os

# Load MongoDB password from environment variable
db_password = os.environ.get("MONGO_DB_PASSWORD")
if not db_password:
    raise EnvironmentError("Missing MongoDB password in environment variables.")

# MongoDB connection URI
uri = f"mongodb+srv://root:{db_password}@cluster-1.8ddyu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster-1"

# Connect to MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Connected to MongoDB")
except Exception as e:
    print("MongoDB connection failed:", e)

# Flask setup
app = Flask(__name__)
db = client["traffic_db"]

@app.route("/api/override", methods=["POST"])
def override_signal():
    try:
        data = request.json
        ambulance_id = data["ambulance_id"]
        junction_id = data["junction_id"]
        signal_id = data["signal_id"]

        # Verify ambulance
        ambulance = db.ambulances.find_one({"_id": ambulance_id})
        if not ambulance:
            return jsonify({"error": "Ambulance not registered"}), 404

        # Find traffic signal
        signal = db.traffic_signals.find_one({
            "signal_id": signal_id,
            "junction_id": ObjectId(junction_id)
        })
        if not signal:
            return jsonify({"error": "Signal not found"}), 404

        # Update override
        db.traffic_signals.update_one(
            {"_id": signal["_id"]},
            {"$set": {
                "override": {
                    "is_active": True,
                    "ambulance_id": ambulance_id,
                    "expires_at": datetime.now() + timedelta(minutes=2)
                }
            }}
        )

        return jsonify({"message": "Override activated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0")
