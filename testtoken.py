import hashlib

SECRET_SALT = "your_secret_salt"  # Replace with your actual salt
maxTokens = 25

def generate_hashed_tokens():
    for i in range(maxTokens):
        token = hashlib.sha256(f"{i}-{SECRET_SALT}".encode()).hexdigest()[:8]
        print(f"Backend Token (index {i}): {token}")

generate_hashed_tokens()
