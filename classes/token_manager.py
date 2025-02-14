import time
import json
import lzma
import os

class TokenManager:
    def __init__(self):
        self.tokens = {}
        self.load_tokens()

    def update_tokens(self, user_id, access_token, refresh_token, expires_in):
        expiry_time = time.time() + expires_in
        self.tokens[user_id] = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expiry': expiry_time
        }
        print(f"Tokens Updated for {user_id}: {self.tokens[user_id]}")
        self.save_tokens()

    def get_access_token(self, user_id):
        self.load_tokens()  # Reload tokens each time to ensure the latest state
        current_time = time.time()
        token_info = self.tokens.get(str(user_id))
        if not token_info:
            print(f"No token entry found for user {user_id}.")
            return None
        token_expiry = token_info.get('token_expiry')
        if token_expiry is None:
            return None
        token_expiry = float(token_expiry)  # Ensure token_expiry is a float
        if current_time > token_expiry:
            return None  # Token has expired
        access_token = token_info.get('access_token')
        if access_token is None:
            return None
        return access_token

    def get_refresh_token(self, user_id):
        self.load_tokens()  # Reload tokens each time to ensure the latest state
        token_info = self.tokens.get(str(user_id))
        if not token_info:
            return None
        refresh_token = token_info.get('refresh_token')
        if refresh_token is None:
            return None
        return refresh_token

    def save_tokens(self):
        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache'))
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, 'spotify-tokens.lzma')
        with lzma.open(file_path, 'wt') as file:
            json.dump(self.tokens, file)

    def load_tokens(self):
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'cache', 'spotify-tokens.lzma'))
        if os.path.exists(file_path):
            with lzma.open(file_path, 'rt') as file:
                self.tokens = json.load(file)
        else:
            print(f"No token file found at {file_path}")

# Ensure the token manager is initialized globally
token_manager = TokenManager()
