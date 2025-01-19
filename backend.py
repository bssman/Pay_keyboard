from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])

SECRET_SALT = os.getenv("SECRET_SALT", "default_salt")  # Replace with your actual secret salt

# Function to generate 10 MD5 hashed tokens
def generate_hashed_tokens():
    num_tokens = 10  # Fixed number of tokens
    tokens = []
    for i in range(num_tokens):
        unique_data = f"{i}-{SECRET_SALT}"  # Combine index and salt
        # Use MD5 hash instead of SHA256
        token = hashlib.md5(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook data:", data)  # Log incoming data for debugging
    
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']

        # Generate tokens (fixed at 10 tokens) using MD5
        tokens = generate_hashed_tokens()

        # Log tokens to the console
        print(f"Generated tokens for {email}: {tokens}")

        # Send tokens back to the frontend
        return jsonify({"status": "success", "tokens": tokens}), 200
    
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=10000, debug=True)
