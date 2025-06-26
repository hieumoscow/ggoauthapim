# Google OAuth Client for Azure APIM

A Python client that implements Google OAuth2 authorization code flow to generate JWT tokens for Azure API Management (APIM) validation.

## Overview

This client performs Google OAuth authentication and returns the ID token (JWT) which can be validated by Azure APIM for user authentication and authorization.

## Files

- `google_oauth_config.json` - Google OAuth2 configuration
- `google_oauth_client.py` - Main OAuth client implementation
- `requirements.txt` - Python dependencies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your Google OAuth2 credentials in `google_oauth_config.json`

## Usage

Run the OAuth client:
```bash
python google_oauth_client.py
```

The script will:
1. Open your browser for Google authentication
2. Start a local server on port 8080 to receive the OAuth callback
3. Exchange the authorization code for tokens
4. Return the ID token (JWT) for APIM validation

## OAuth Flow

This implementation uses the **Authorization Code flow** with the following steps:

1. **Authorization Request** - Redirects user to Google OAuth consent screen
2. **Authorization Code** - Receives code via local callback server
3. **Token Exchange** - Exchanges code for access_token and id_token
4. **JWT Token** - Returns the ID token for APIM validation

## Important Notes

### Why ID Token vs Access Token

This client uses the **ID token** (not access token) for APIM authentication because:

- **ID Token**: JWT format, contains user claims, can be validated by APIM
- **Access Token**: Often opaque, meant for API access, cannot be validated as JWT

### Azure APIM Developer Portal Limitation

The Azure APIM developer portal OAuth service has a limitation:
- **Implicit Flow**: Supports OpenID Connect and ID tokens ✅
- **Authorization Code Flow**: Does NOT support OpenID Connect or ID tokens ❌

For proper JWT validation in APIM, you should use the implicit flow in the portal, or use this custom client for authorization code flow with ID tokens.

## Configuration

The Google OAuth configuration includes:
- `client_id` - Your Google OAuth client ID
- `client_secret` - Your Google OAuth client secret  
- `redirect_uris` - Configured redirect URIs (includes localhost:8080 for this client)

## Security

- Uses HTTPS for all OAuth endpoints
- Implements proper CSRF protection with state parameter
- Local server only accepts OAuth callback, then shuts down
- ID tokens can be validated using Google's public keys

## Example Output

```
Opening browser for authorization...
Waiting for authorization...
✓ Authorization code received
✓ Tokens received
✓ Id token received: eyJhbGciOiJSUzI1NiIs...
✓ User authenticated: user@example.com
✓ Using Google ID token as JWT for Azure APIM

==================================================
AUTHENTICATION SUCCESSFUL
==================================================
User: John Doe (user@example.com)

Google ID Token (JWT for Azure APIM):
eyJhbGciOiJSUzI1NiIsImtpZCI6IjY4M...
==================================================
JWT Payload:
{
  "iss": "https://accounts.google.com",
  "aud": "133913040985-5t6256am512cl4dm9voint6rkn6krird.apps.googleusercontent.com",
  "sub": "123456789",
  "email": "user@example.com",
  "name": "John Doe",
  "iat": 1640995200,
  "exp": 1640998800
}
```