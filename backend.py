from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])  # Allow frontend access

# Secret salt for hashing tokens
SECRET_SALT = "your_secret_salt_here"  # Change this to a secure, random string

# Function to generate hashed tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # 1 token per 200 NGN
    tokens = []
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if data.get('event') == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = data['data']['id']  # Unique transaction ID
        payment_amount = data['data'].get('amount', 0)  # Amount paid (in kobo)

        try:
            payment_amount = int(payment_amount) // 100  # Convert kobo to NGN
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Payment amount must be greater than zero"}), 400

        # Generate tokens
        tokens = generate_hashed_tokens(payment_amount, transaction_id)

        # Log only essential information
        print(f"Transaction ID: {transaction_id}")
        print(f"Email: {email}")
        print(f"Generated Tokens: {tokens}")

        # Send tokens back to the frontend
        return jsonify({"status": "success", "tokens": tokens}), 200

    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=10000, debug=True)
