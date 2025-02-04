from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import hashlib
import os

app = Flask(__name__)

# Enable CORS for both the frontend and ESP8266
CORS(app, origins=["https://suites11.com.ng", "*"], supports_credentials=True)

# PostgreSQL Connection
DB_CONFIG = {
    "dbname": "keypad_db",
    "user": "keypad_db",
    "password": "82pttLdEQgAqXh2enLTSBd2Zav4Pm5pu",
    "host": "dpg-cugg6a8gph6c73d24ofg-a.oregon-postgres.render.com",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Generate Hashed Tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # Assuming 200 NGN per token
    tokens = []
    
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{os.urandom(8).hex()}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    
    return tokens

# Handle Payment Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = data['data']['id']
        payment_amount = int(data['data']['amount']) // 100  # Convert kobo to NGN
        
        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400
        
        tokens = generate_hashed_tokens(payment_amount, transaction_id)

        # Store tokens in DB
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            for token in tokens:
                cursor.execute(
                    "INSERT INTO tokens (email, transaction_id, token, used) VALUES (%s, %s, %s, %s)",
                    (email, transaction_id, token, False)
                )

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

        return jsonify({"status": "success", "tokens": tokens}), 200
    
    return jsonify({"status": "ignored"}), 200

# Fetch Unused Tokens (For ESP8266)
@app.route('/tokens', methods=['GET'])
def get_tokens():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT token FROM tokens WHERE used = FALSE LIMIT 10")
        tokens = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        return jsonify({"tokens": tokens}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Mark Token as Used (For ESP8266)
@app.route('/verify-token', methods=['POST'])
def verify_token():
    data = request.json
    token = data.get("token")

    if not token:
        return jsonify({"status": "error", "message": "Token is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT used FROM tokens WHERE token = %s", (token,))
        result = cursor.fetchone()
        
        if result is None:
            return jsonify({"status": "error", "message": "Invalid token"}), 400
        if result[0]:  # If token is already used
            return jsonify({"status": "error", "message": "Token already used"}), 400

        # Mark token as used
        cursor.execute("UPDATE tokens SET used = TRUE WHERE token = %s", (token,))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"status": "success", "message": "Token verified"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=10000, debug=True)
