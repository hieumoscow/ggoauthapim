#!/usr/bin/env python3
"""
Google OAuth Client for Azure APIM JWT Token Generation
"""

import json
import jwt
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import base64

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.auth_code = parse_qs(urlparse(self.path).query).get('code', [None])[0]
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<html><body><h1>Authorization successful! You can close this window.</h1></body></html>')
        
    def log_message(self, format, *args):
        pass

class GoogleOAuthClient:
    def __init__(self, config_file='google_oauth_config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)['web']
        
        self.client_id = self.config['client_id']
        self.client_secret = self.config['client_secret']
        self.redirect_uri = 'http://localhost:8080/callback'
        self.scope = 'openid email profile'
        
    def get_authorization_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        return f"{self.config['auth_uri']}?{urlencode(params)}"
    
    def get_authorization_code(self):
        auth_url = self.get_authorization_url()
        print(f"Opening browser for authorization: {auth_url}")
        
        # Start local server to catch callback
        server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
        server.auth_code = None
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("Waiting for authorization...")
        while server.auth_code is None:
            server.handle_request()
        
        auth_code = server.auth_code
        server.server_close()
        return auth_code
    
    def exchange_code_for_tokens(self, auth_code):
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.config['token_uri'], data=token_data)
        response.raise_for_status()
        return response.json()
    
    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
        response.raise_for_status()
        return response.json()
    
    def decode_id_token(self, id_token):
        """Decode Google ID token for inspection"""
        try:
            # Decode without verification for inspection
            decoded = jwt.decode(id_token, options={"verify_signature": False})
            return decoded
        except Exception as e:
            print(f"Could not decode ID token: {e}")
            return None
    
    def authenticate_and_get_jwt(self):
        """Complete OAuth flow and return JWT for APIM"""
        try:
            # Step 1: Get authorization code
            auth_code = self.get_authorization_code()
            print("✓ Authorization code received")
            
            # Step 2: Exchange code for tokens
            tokens = self.exchange_code_for_tokens(auth_code)
            print("✓ Tokens received: ", tokens)
            access_token = tokens['access_token']
            id_token = tokens.get('id_token')
            print("✓ Id token received: ", id_token)
            
            # Step 3: Use ID token as JWT for APIM
            if not id_token:
                raise Exception("No ID token received from Google")
            
            decoded_token = self.decode_id_token(id_token)
            print(f"✓ User authenticated: {decoded_token.get('email') if decoded_token else 'Unknown'}")
            print("✓ Using Google ID token as JWT for Azure APIM")
            
            return {
                'jwt_token': id_token,
                'decoded_token': decoded_token,
                'google_tokens': tokens
            }
            
        except Exception as e:
            print(f"✗ Authentication failed: {str(e)}")
            return None

def main():
    client = GoogleOAuthClient()
    result = client.authenticate_and_get_jwt()
    
    if result:
        print("\n" + "="*50)
        print("AUTHENTICATION SUCCESSFUL")
        print("="*50)
        
        if result['decoded_token']:
            user_info = result['decoded_token']
            print(f"User: {user_info.get('name')} ({user_info.get('email')})")
        
        print(f"\nGoogle ID Token (JWT for Azure APIM):")
        print(result['jwt_token'])
        print("\n" + "="*50)
        
        # Display JWT payload
        if result['decoded_token']:
            print("JWT Payload:")
            print(json.dumps(result['decoded_token'], indent=2))
    else:
        print("Authentication failed!")

if __name__ == "__main__":
    main()