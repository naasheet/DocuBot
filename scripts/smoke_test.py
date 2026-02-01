#!/usr/bin/env python3
import sys
import socket
import time
try:
    import requests
except ImportError:
    print("❌ 'requests' library not found. Please run: pip install requests")
    sys.exit(1)

SERVICES = [
    {"name": "Frontend", "url": "http://localhost:3000", "type": "http"},
    {"name": "Backend API", "url": "http://localhost:8000/health", "type": "http"},
    {"name": "Qdrant", "url": "http://localhost:6333/healthz", "type": "http"},
    {"name": "Postgres", "host": "localhost", "port": 5432, "type": "tcp"},
    {"name": "Redis", "host": "localhost", "port": 6379, "type": "tcp"},
]

def check_tcp(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_http(url):
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def main():
    print("🚀 Running Smoke Test...")
    print(f"{'Service':<15} | {'Type':<5} | {'Status'}")
    print("-" * 35)
    
    all_passed = True
    
    for service in SERVICES:
        name = service["name"]
        sType = service["type"]
        
        passed = False
        if sType == "http":
            passed = check_http(service["url"])
        elif sType == "tcp":
            passed = check_tcp(service["host"], service["port"])
            
        status = "✅ UP" if passed else "❌ DOWN"
        print(f"{name:<15} | {sType:<5} | {status}")
        
        if not passed:
            all_passed = False
            
    print("-" * 35)
    if all_passed:
        print("✨ All systems operational!")
        sys.exit(0)
    else:
        print("⚠️  Some services are down. Check 'docker-compose logs'.")
        sys.exit(1)

if __name__ == "__main__":
    main()