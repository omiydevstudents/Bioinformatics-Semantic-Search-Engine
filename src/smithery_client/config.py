"""
smithery_client.config
----------------------

This module loads Smithery API configuration from an external .env file.

Expected environment variables:
- SMITHERY_API_URL
- SMITHERY_API_KEY
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root
if not load_dotenv():
    print("[WARN] .env file not found or could not be loaded.")

API_BASE_URL = os.getenv("SMITHERY_API_URL")
API_KEY = os.getenv("SMITHERY_API_KEY")

if not API_BASE_URL:
    raise ValueError("Missing required environment variable: SMITHERY_API_URL")

if not API_KEY:
    raise ValueError("Missing required environment variable: SMITHERY_API_KEY")


# print(f"[INFO] Loaded API URL: {API_BASE_URL}")
# print(f"[INFO] Loaded API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
