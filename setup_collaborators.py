#!/usr/bin/env python3
"""
One-Time Collaborator Setup Script
-----------------------------------
Jalankan ini 1x saja sebelum pakai GitHub Actions
Script ini akan:
1. Add semua user sebagai collaborator
2. Auto-accept invitation untuk semua user
"""

import os, time, requests
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
TARGET_REPO = os.getenv("TARGET_REPO", "")
TOKENS = [os.getenv(f"PAT{i}") for i in range(1, 21) if os.getenv(f"PAT{i}")]
USERS = [os.getenv(f"USERNAME{i}") for i in range(1, 21) if os.getenv(f"USERNAME{i}")]

if not TARGET_REPO or "/" not in TARGET_REPO:
    TARGET_REPO = f"{ADMIN_USERNAME}/hapus"

class GitHubClient:
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        })
    
    def call(self, endpoint, method="GET", data=None):
        url = f"https://api.github.com{endpoint}"
        try:
            if method == "POST":
                resp = self.session.post(url, json=data, timeout=10)
            elif method == "PUT":
                resp = self.session.put(url, json=data, timeout=10)
            elif method == "PATCH":
                resp = self.session.patch(url, json=data, timeout=10)
            else:
                resp = self.session.get(url, timeout=10)
            
            if resp.status_code in [200, 201, 204]:
                return resp.json() if resp.text else {}
            return None
        except Exception as e:
            print(f"   Error: {e}")
            return None

def setup_collaborators():
    print("\n" + "="*60)
    print("🔧 ONE-TIME COLLABORATOR SETUP")
    print("="*60)
    print(f"📦 Target Repo: {TARGET_REPO}")
    print(f"👥 Total Users: {len(USERS)}\n")
    
    admin_client = GitHubClient(TOKENS[0])
    
    # Step 1: Add collaborators
    print("📨 Step 1: Sending invitations...")
    for u in USERS[1:]:
        if not u:
            continue
        
        result = admin_client.call(
            f"/repos/{TARGET_REPO}/collaborators/{u}",
            method="PUT",
            data={"permission": "push"}
        )
        
        if result is not None:
            print(f"   ✅ Invitation sent to: {u}")
        else:
            print(f"   ⚠️  Failed to invite: {u}")
        
        time.sleep(0.8)
    
    print("\n⏳ Waiting 5 seconds for invitations to propagate...\n")
    time.sleep(5)
    
    # Step 2: Accept invitations
    print("🔔 Step 2: Auto-accepting invitations...")
    
    for u, t in zip(USERS[1:], TOKENS[1:]):
        if not u or not t:
            continue
        
        client = GitHubClient(t)
        
        # Get all invitations
        invitations = client.call("/user/repository_invitations")
        
        if not invitations or not isinstance(invitations, list):
            print(f"   ⚠️  {u}: No invitations found")
            continue
        
        # Find target repo invitation
        accepted = False
        for invite in invitations:
            repo_name = invite.get("repository", {}).get("full_name")
            if repo_name == TARGET_REPO:
                invite_id = invite.get("id")
                result = client.call(
                    f"/user/repository_invitations/{invite_id}",
                    method="PATCH"
                )
                if result is not None:
                    print(f"   ✅ {u} accepted invitation")
                    accepted = True
                else:
                    print(f"   ⚠️  {u} failed to accept")
                break
        
        if not accepted:
            print(f"   ℹ️  {u}: No invitation for {TARGET_REPO}")
        
        time.sleep(0.8)
    
    print("\n" + "="*60)
    print("✅ COLLABORATOR SETUP COMPLETED!")
    print("="*60)
    print("\n💡 Next step:")
    print("   Run GitHub Actions workflow atau lanjut dengan aktivitas lain\n")

if __name__ == "__main__":
    setup_collaborators()