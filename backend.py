from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

SECRET_SALT = os.getenv("SECRET_SALT", "default_salt")  # Replace with your actual secret salt

# Function to generate hashed tokens
def generate_hashed_tokens(amount):
    num_tokens = amount // 200  # Assuming 200 NGN per token
    tokens = []
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')  # Current date in UTC
    for i in range(num_tokens):
        unique_data = f"{today}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook data:", data)  # Log incoming data for debugging
    
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        payment_amount = data['data'].get('amount', 0)  # Amount paid (in kobo)

        try:
            payment_amount = int(payment_amount) // 100  # Convert kobo to Naira
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Payment amount must be greater than zero"}), 400

        # Generate tokens
        tokens = generate_hashed_tokens(payment_amount)

        # Log tokens to the console
        print(f"Generated tokens for {email}: {tokens}")

        # Send tokens back to the frontend
        return jsonify({"status": "success", "tokens": tokens}), 200
    
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=10000, debug=True)
