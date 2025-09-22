#!/usr/bin/env python3
"""
Test script for analysis endpoints in FPAS API
"""

import requests
import json
import sys

def test_analysis_endpoints():
    """Test the analysis endpoints"""
    BASE_URL = "http://localhost:8000/api/v1"

    print("Testing analysis endpoints...")

    # Test 1: Custom analysis endpoint
    print("\n1. Testing /analysis/custom endpoint")
    try:
        response = requests.post(
            f"{BASE_URL}/analysis/custom",
            json={
                "query": "Test analysis query",
                "context_ids": ["test-politician"],
                "detailed_response": False
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        elif response.status_code == 404:
            print("❌ 404 Error - Endpoint not found")
            return False
        elif response.status_code == 503:
            print("❌ 503 Error - Service unavailable")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_analysis_endpoints()
    if success:
        print("\n✅ Analysis endpoints are working!")
    else:
        print("\n❌ Analysis endpoints have issues!")
