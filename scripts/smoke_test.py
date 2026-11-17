import os

import httpx

url = os.environ.get("DEPLOYED_URL", "http://localhost:8000").rstrip("/")
with httpx.Client(timeout=30) as client:
    for endpoint in ("/health", "/ready", "/api/v1/stats"):
        response = client.get(url + endpoint)
        response.raise_for_status()
        print(endpoint, response.json())
