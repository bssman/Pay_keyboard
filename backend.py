from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import hashlib
import os

app = Flask(__name__)

# Allow frontend and ESP8266 (any origin) to access the backend
CORS(app, origins=["https://suites11.com.ng", "*"], allow_headers=["Content-Type"], methods=["GET", "POST"])

def get_db_connection():
    return psycopg2.connect(
        dbname="keypad_db",
        user="keypad_db",
        password="82pttLdEQgAqXh2enLTSBd2Zav4Pm5pu",
        host="dpg-cugg6a8gph6c73d24ofg-a.oregon-postgres.render.com",
        port="5432"
    )

SECRET_SALT = "your_secret_salt"

def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  
    tokens = []
    
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  
        tokens.append(token)
    
    return tokens

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if data.get('event') == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = str(data['data']['id'])  
        payment_amount = data['data'].get('amount', 0)  

        try:
            payment_amount = int(payment_amount) // 100  
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Payment amount must be greater than zero"}), 400

        tokens = generate_hashed_tokens(payment_amount, transaction_id)

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
            return jsonify({"status": "error", "message": f"Database error: {e}"}), 500

        return jsonify({"status": "success", "tokens": tokens}), 200

    return jsonify({"status": "ignored"}), 200

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

@app.route('/verify-token', methods=['POST'])
def verify_token():
    data = request.json
    input_token = data.get("token")

    if not input_token:
        return jsonify({"status": "error", "message": "Token is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tokens WHERE token = %s AND used = FALSE", (input_token,))
        token_row = cursor.fetchone()

        if token_row:
            token_id = token_row[0]
            cursor.execute("UPDATE tokens SET used = TRUE WHERE id = %s", (token_id,))
            conn.commit()

            cursor.close()
            conn.close()
            return jsonify({"status": "success", "message": "Token verified"}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Invalid or already used token"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=10000, debug=True)
