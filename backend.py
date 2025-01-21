from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

SECRET_SALT = os.getenv("SECRET_SALT", "QBIJSIH5NXWLNUJASMWI4RVU4XQH4E4E")  # Replace with your actual secret salt
generated_tokens = []  # Store generated tokens temporarily

# Function to generate hashed tokens
def generate_hashed_tokens():
    num_tokens = 10  # Number of tokens
    tokens = []
    for _ in range(num_tokens):
        unique_data = f"testword-{SECRET_SALT}"  # Use "testword" for hashing
        token = hashlib.md5(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

# Webhook to receive payment success events
@app.route('/webhook', methods=['POST'])
def webhook():
    global generated_tokens
    data = request.json
    print("Received webhook data:", data)

    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']

        # Generate tokens
        generated_tokens = generate_hashed_tokens()

        # Log tokens
        print(f"Generated tokens for {email}: {generated_tokens}")

        # Send tokens back to the frontend
        return jsonify({"status": "success", "tokens": generated_tokens}), 200

    return jsonify({"status": "ignored"}), 200

# API endpoint for ESP8266 to fetch tokens
@app.route('/get_tokens', methods=['GET'])
def get_tokens():
    if generated_tokens:
        return jsonify({"status": "success", "tokens": generated_tokens}), 200
    return jsonify({"status": "error", "message": "No tokens available"}), 404

if __name__ == '__main__':
    app.run(port=10000, debug=True)
