from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import hashlib
import os

app = Flask(__name__)
CORS(app, origins=["https://suites11.com"])

DATABASE_URL = "postgresql://keypad_db:82pttLdEQgAqXh2enLTSBd2Zav4Pm5pu@dpg-cugg6a8gph6c73d24ofg-a.oregon-postgres.render.com/keypad_db"
SECRET_SALT = "my_secret_salt"  # Change this to a secure value

# Function to generate hashed tokens
def generate_hashed_tokens(amount, transaction_id):
    num_tokens = amount // 200  # Assuming 200 NGN per token
    tokens = []
    for i in range(num_tokens):
        unique_data = f"{transaction_id}-{i}-{SECRET_SALT}"
        token = hashlib.sha256(unique_data.encode()).hexdigest()[:8]  # 8-character token
        tokens.append(token)
    return tokens

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data['event'] == 'charge.success':
        email = data['data']['customer']['email']
        transaction_id = data['data']['id']  # Unique transaction ID
        payment_amount = data['data'].get('amount', 0)  # Amount paid in kobo

        try:
            payment_amount = int(payment_amount) // 100  # Convert kobo to Naira
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid payment amount"}), 400

        if payment_amount <= 0:
            return jsonify({"status": "error", "message": "Payment amount must be greater than zero"}), 400

        # Generate tokens
        tokens = generate_hashed_tokens(payment_amount, transaction_id)

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            # Store tokens in the database
            for token in tokens:
                cursor.execute(
                    "INSERT INTO tokens (email, transaction_id, token) VALUES (%s, %s, %s)",
                    (email, transaction_id, token)
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
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("SELECT token FROM tokens WHERE used = FALSE")
        tokens = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()

        return jsonify({"tokens": tokens}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500

@app.route('/validate-token', methods=['POST'])
def validate_token():
    data = request.json
    user_token = data.get('token')

    if not user_token:
        return jsonify({"status": "error", "message": "Token is required"}), 400

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tokens WHERE token = %s AND used = FALSE", (user_token,))
        result = cursor.fetchone()

        if result:
            token_id = result[0]

            # Mark token as used
            cursor.execute("UPDATE tokens SET used = TRUE WHERE id = %s", (token_id,))
            conn.commit()

            cursor.close()
            conn.close()
            return jsonify({"status": "success", "message": "Token is valid"}), 200
        else:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Invalid or already used token"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {e}"}), 500

if __name__ == '__main__':
    app.run(port=10000, debug=True)
