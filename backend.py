from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com"])

# Generate hashed tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # Example: 1 token per 200 NGN
    tokens = []

    for i in range(num_tokens):
        # Generate a unique token based on transaction_id and index
        token_seed = f"{transaction_id}-{i}-{os.urandom(16)}"
        token = hashlib.sha256(token_seed.encode()).hexdigest()[:8]  # Use first 8 characters of the hash
        tokens.append(token)

    return tokens

@app.route('/')
def home():
    return "Backend is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook data:", data)  # Log incoming data for debugging
    
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = data['data']['id']  # Unique transaction ID
        payment_amount = data['data'].get('amount')  # Safely access the 'amount' field

        if not payment_amount:
            return jsonify({"status": "error", "message": "Amount not provided in webhook payload"}), 400

        try:
            payment_amount = int(payment_amount) // 100  # Convert kobo to Naira
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Payment amount must be greater than zero"}), 400

        # Generate tokens based on payment amount and transaction ID
        tokens = generate_hashed_tokens(payment_amount, transaction_id)

        # Return the tokens in the response
        return jsonify({
            "status": "success",
            "message": "Tokens generated successfully",
            "tokens": tokens
        }), 200
    
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=10000, debug=True)
