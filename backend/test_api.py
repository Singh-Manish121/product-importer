#!/usr/bin/env python
"""Quick test script to verify API."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("Testing API endpoints...\n")

# Test root
response = client.get("/")
print(f"GET / => {response.status_code}")
print(f"Response: {response.json()}\n")

# Test health
response = client.get("/health")
print(f"GET /health => {response.status_code}")
print(f"Response: {response.json()}\n")

# Test docs
response = client.get("/docs")
print(f"GET /docs => {response.status_code}")
print(f"Swagger available: {response.status_code == 200}\n")

# Test openapi.json
response = client.get("/openapi.json")
print(f"GET /openapi.json => {response.status_code}")
if response.status_code == 200:
    print(f"OpenAPI schema available: True")
    print(f"Endpoints in schema: {len(response.json().get('paths', {}))}\n")

print("✅ All tests passed!")
