from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import psycopg2
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com.ng"])  # Allow frontend access

# PostgreSQL Database Connection
DB_CONN = psycopg2.connect(
    dbname="keypad_db",
    user="keypad_db",
    password="82pttLdEQgAqXh2enLTSBd2Zav4Pm5pu",
    host="dpg-cugg6a8gph6c73d24ofg-a",
    port="5432"
)

SECRET_SALT = "your_secret_salt"

# Generate hashed tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # Assuming 200 NGN per token
    tokens = []
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

# Store tokens in the database
def store_tokens(email, transaction_id, tokens):
    with DB_CONN.cursor() as cursor:
        for token in tokens:
            cursor.execute("INSERT INTO tokens (email, transaction_id, token) VALUES (%s, %s, %s)", (email, transaction_id, token))
        DB_CONN.commit()

# Webhook Endpoint (Receives Payments)
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = data['data']['reference']
        payment_amount = int(data['data']['amount']) // 100  # Convert from kobo to NGN

        tokens = generate_hashed_tokens(payment_amount, transaction_id)
        store_tokens(email, transaction_id, tokens)

        return jsonify({"status": "success", "tokens": tokens}), 200

    return jsonify({"status": "ignored"}), 200

# ESP8266 Fetch Tokens
@app.route('/fetch_tokens', methods=['GET'])
def fetch_tokens():
    with DB_CONN.cursor() as cursor:
        cursor.execute("SELECT token FROM tokens WHERE used = FALSE")
        tokens = [row[0] for row in cursor.fetchall()]
    return jsonify({"tokens": tokens})

# ESP8266 Mark Token as Used
@app.route('/use_token', methods=['POST'])
def use_token():
    data = request.json
    token = data.get("token")

    with DB_CONN.cursor() as cursor:
        cursor.execute("UPDATE tokens SET used = TRUE WHERE token = %s AND used = FALSE RETURNING token", (token,))
        if cursor.fetchone():
            DB_CONN.commit()
            return jsonify({"status": "success", "message": "Token used successfully"}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid or already used token"}), 400

if __name__ == '__main__':
    app.run(port=10000, debug=True)
