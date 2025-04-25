from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, request, jsonify
from bson import ObjectId
from datetime import datetime, timedelta

uri = "mongodb+srv://root:iTZuc8WtBKQa6m3m@cluster-1.8ddyu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster-1"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


app = Flask(__name__)

db = client["traffic_db"]

@app.route("/api/override", methods=["POST"])
def override_signal():
    try:
        data = request.json
        ambulance_id = data["ambulance_id"]
        junction_id = data["junction_id"]
        signal_id = data["signal_id"]
        timestamp = int(data["timestamp"])

        # # Basic timestamp freshness check (5 mins tolerance)
        # if abs(datetime.now().timestamp() - timestamp) > 300:
        #     return jsonify({"error": "Stale or invalid timestamp"}), 400

        # Verify ambulance exists
        ambulance = db.ambulances.find_one({"_id": ambulance_id})
        if not ambulance:
            return jsonify({"error": "Ambulance not registered"}), 404

        # Find the traffic signal
        signal = db.traffic_signals.find_one({
            "signal_id": signal_id,
            "junction_id": ObjectId(junction_id)
        })

        if not signal:
            return jsonify({"error": "Signal not found"}), 404

        # Update traffic signal override
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

        return jsonify({"message": "✅ Override activated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0')  # Add host='0.0.0.0'