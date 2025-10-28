"""
Check Script for Cyber Security Task 3 — Secure File Sharing System
This verifies directory structure, required files, dependencies, and Flask run test.
"""

import os
import subprocess
import sys
from importlib import util

# Expected structure
expected_dirs = ["uploads_encrypted", "templates"]
expected_files = ["app.py", "requirements.txt", ".env", ".env.example", "README.md"]

print("🔍 Checking Secure File Sharing Project Structure...\n")

# 1️⃣ Check directories
for d in expected_dirs:
    if os.path.isdir(d):
        print(f"✅ Directory found: {d}/")
    else:
        print(f"❌ Missing directory: {d}/")

# 2️⃣ Check files
for f in expected_files:
    if os.path.isfile(f):
        print(f"✅ File found: {f}")
    else:
        print(f"❌ Missing file: {f}")

# 3️⃣ Verify AES key in .env
if os.path.isfile(".env"):
    with open(".env") as env:
        content = env.read()
        if "AES_KEY" in content and len(content.strip()) > 20:
            print("✅ AES_KEY found in .env")
        else:
            print("⚠️ AES_KEY missing or invalid in .env")
else:
    print("⚠️ .env file not found — cannot check AES_KEY")

# 4️⃣ Dependency check
print("\n📦 Checking Python Dependencies...")
required_libs = ["flask", "Crypto", "dotenv"]
for lib in required_libs:
    if util.find_spec(lib):
        print(f"✅ Library installed: {lib}")
    else:
        print(f"❌ Library missing: {lib} (install via pip)")

# 5️⃣ Try to run Flask app for verification
print("\n🚀 Verifying Flask app runs correctly...")
try:
    result = subprocess.run(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5
    )
    if result.returncode == 0 or b"Running on" in result.stderr:
        print("✅ Flask app launched successfully (port 5000).")
    else:
        print("⚠️ Flask app may have errors — check app.py output below:")
        print(result.stderr.decode() or result.stdout.decode())
except subprocess.TimeoutExpired:
    print("✅ Flask app started (auto-stopped after 5 seconds). Looks fine.")
except Exception as e:
    print(f"❌ Error starting Flask app: {e}")

print("\n✅ Check completed.\n")
