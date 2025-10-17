#!/usr/bin/env python3
"""
Auto GitHub Secrets Setup
-------------------------
Otomatis add semua PAT tokens ke GitHub repository secrets
Tidak perlu manual 1-1 lagi!

Requirements:
  pip install pynacl requests python-dotenv
"""

import os, base64, requests
from nacl import encoding, public
from dotenv import load_dotenv

load_dotenv()

# Config
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
TARGET_REPO = os.getenv("TARGET_REPO", "")
ADMIN_TOKEN = os.getenv("PAT1")  # Token admin untuk akses repo settings

if not ADMIN_TOKEN:
    print("❌ PAT1 (admin token) tidak ditemukan di .env")
    exit(1)

if not TARGET_REPO or "/" not in TARGET_REPO:
    TARGET_REPO = f"{ADMIN_USERNAME}/hapus"

# Collect all tokens from .env
TOKENS = {}
for i in range(1, 21):
    token = os.getenv(f"PAT{i}")
    if token:
        TOKENS[f"PAT{i}"] = token

if not TOKENS:
    print("❌ Tidak ada PAT tokens di .env")
    exit(1)

print(f"📦 Target Repo: {TARGET_REPO}")
print(f"🔑 Found {len(TOKENS)} tokens in .env\n")

# ======================
# Encryption Functions
# ======================
def get_public_key(repo, token):
    """Get repository public key for encrypting secrets"""
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"❌ Failed to get public key: {resp.status_code}")
        print(f"   Response: {resp.text}")
        return None

def encrypt_secret(public_key, secret_value):
    """Encrypt secret using repository public key"""
    public_key_bytes = base64.b64decode(public_key)
    sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def create_or_update_secret(repo, token, secret_name, secret_value):
    """Create or update a repository secret"""
    # Get public key
    key_data = get_public_key(repo, token)
    if not key_data:
        return False
    
    # Encrypt secret
    encrypted_value = encrypt_secret(key_data["key"], secret_value)
    
    # Create/update secret
    url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_data["key_id"]
    }
    
    resp = requests.put(url, headers=headers, json=data)
    return resp.status_code in [201, 204]

# ======================
# Main Setup
# ======================
def setup_secrets():
    print("="*60)
    print("🔐 AUTO GITHUB SECRETS SETUP")
    print("="*60)
    print(f"📍 Repository: {TARGET_REPO}")
    print(f"🔑 Secrets to add: {len(TOKENS)}\n")
    
    success_count = 0
    failed = []
    
    for secret_name, secret_value in TOKENS.items():
        print(f"⏳ Adding {secret_name}...", end=" ")
        
        if create_or_update_secret(TARGET_REPO, ADMIN_TOKEN, secret_name, secret_value):
            print("✅")
            success_count += 1
        else:
            print("❌")
            failed.append(secret_name)
    
    print("\n" + "="*60)
    print(f"✅ Successfully added: {success_count}/{len(TOKENS)} secrets")
    
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
    
    print("="*60)
    
    if success_count == len(TOKENS):
        print("\n🎉 All secrets added successfully!")
        print("💡 You can now run GitHub Actions workflows\n")
    else:
        print("\n⚠️  Some secrets failed to add")
        print("💡 Check if admin token has 'repo' and 'workflow' permissions\n")

# ======================
# Permission Checker
# ======================
def check_permissions():
    """Check if admin token has required permissions"""
    print("🔍 Checking admin token permissions...\n")
    
    headers = {
        "Authorization": f"token {ADMIN_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check token scopes
    resp = requests.get("https://api.github.com/user", headers=headers)
    if resp.status_code != 200:
        print("❌ Invalid admin token!")
        return False
    
    scopes = resp.headers.get("X-OAuth-Scopes", "").split(", ")
    print(f"📋 Token scopes: {', '.join(scopes)}")
    
    required = ["repo", "workflow"]
    missing = [s for s in required if s not in scopes]
    
    if missing:
        print(f"\n⚠️  Missing required scopes: {', '.join(missing)}")
        print("\n💡 How to fix:")
        print("   1. Go to: https://github.com/settings/tokens")
        print("   2. Edit PAT1 token")
        print("   3. Enable these scopes:")
        print("      ☑️  repo (Full control of private repositories)")
        print("      ☑️  workflow (Update GitHub Action workflows)")
        print("   4. Click 'Update token'")
        print("   5. Copy new token to .env file\n")
        return False
    
    print("✅ All required permissions available!\n")
    return True

# ======================
# Run
# ======================
if __name__ == "__main__":
    try:
        # Check permissions first
        if not check_permissions():
            print("❌ Setup aborted due to permission issues\n")
            exit(1)
        
        # Setup secrets
        setup_secrets()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")