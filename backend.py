from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["*"])

# Secret salt for token hashing 1st feb 2025 part 2
SECRET_SALT = os.getenv("SECRET_SALT", "default_salt")

# Function to generate hashed tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # Assuming 200 NGN per token
    tokens = []
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

# Webhook to receive payment and generate token
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    txn_id = data.get('data', {}).get('id')
    
    if not txn_id:
        return jsonify({"error": "Transaction ID not found"}), 400

    # Generate token using txn_id and SECRET_SALT
    unique_data = f"{txn_id}-{SECRET_SALT}"
    token = hashlib.md5(unique_data.encode()).hexdigest()[:8]
    
    # Store the token in the database
    TOKENS_DB.append({
        "token": token,
        "status": "valid",
        "created_at": datetime.utcnow(),
    })

    print(f"Generated token: {token}")
    return jsonify({"status": "success", "token": token}), 200

# API for ESP8266 to fetch valid tokens
@app.route('/fetch-tokens', methods=['GET'])
def fetch_tokens():
    # Filter valid tokens
    valid_tokens = [t["token"] for t in TOKENS_DB if t["status"] == "valid"]
    return jsonify({"tokens": valid_tokens}), 200

# API for ESP8266 to mark token as used
@app.route('/mark-token-used', methods=['POST'])
def mark_token_used():
    data = request.json
    token = data.get('token')
    
    for t in TOKENS_DB:
        if t["token"] == token and t["status"] == "valid":
            t["status"] = "used"
            return jsonify({"status": "success", "message": "Token marked as used"}), 200
    
    return jsonify({"status": "error", "message": "Invalid or already used token"}), 400

if __name__ == '__main__':
    app.run(port=10000, debug=True)
