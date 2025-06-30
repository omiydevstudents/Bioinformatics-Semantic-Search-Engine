"""
smithery_client.config
----------------------

This module loads MCP or Smithery API configuration from an external .env file.

Expected environment variables:
- SMITHERY_API_URL
- SMITHERY_API_KEY
- BIO_MCP_URL (optional if using MCP only)
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root
if not load_dotenv():
    print("[WARN] .env file not found or could not be loaded.")

# Load Smithery variables
SMITHERY_API_URL = os.getenv("SMITHERY_API_URL")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")

# Load MCP fallback
BIO_MCP_URL = os.getenv("BIO_MCP_URL")

# Check config integrity
if not (SMITHERY_API_URL or BIO_MCP_URL):
    raise ValueError("Missing both SMITHERY_API_URL and BIO_MCP_URL — one must be set in .env")

if not SMITHERY_API_KEY:
    print("[WARN] SMITHERY_API_KEY is not set — Smithery API will not be available.")

# Determine which API to use
if SMITHERY_API_URL and SMITHERY_API_KEY:
    API_BASE_URL = SMITHERY_API_URL
    API_KEY = SMITHERY_API_KEY
    PROVIDER = "smithery"
elif BIO_MCP_URL:
    API_BASE_URL = BIO_MCP_URL
    API_KEY = None
    PROVIDER = "mcp"
else:
    raise ValueError("No usable provider found. Please check your environment variables.")

# Optional debug prints
# print(f"[INFO] Provider: {PROVIDER}")
# print(f"[INFO] Using API URL: {API_BASE_URL}")
