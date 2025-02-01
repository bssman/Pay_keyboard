from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["*"])

# Secret salt for token hashing starting feb
SECRET_SALT = os.getenv("SECRET_SALT", "default_salt")

# Function to generate hashed tokens attempt at (010225)
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
    print(f"Webhook invoked. Raw data: {data}")  # Log raw webhook data
    
    if data.get('event') == 'charge.success':
        try:
            email = data['data']['customer']['email']
            transaction_id = data['data']['id']
            payment_amount = data['data'].get('amount', 0)

            print(f"Processing: email={email}, transaction_id={transaction_id}, amount={payment_amount}")

            payment_amount = int(payment_amount) // 100  # Convert kobo to Naira

            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than zero")

            # Generate tokens
            tokens = generate_hashed_tokens(payment_amount, transaction_id)
            print(f"Generated tokens for {email}: {tokens}")

            # Send tokens via email
            send_email(email, tokens)

            return jsonify({"status": "success", "message": "Tokens sent to email"}), 200
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    print("Ignored webhook event.")
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=10000, debug=True)
