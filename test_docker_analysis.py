#!/usr/bin/env python3
"""
Test analysis endpoints in Docker environment
"""

import requests
import json
import time

def test_docker_analysis_endpoints():
    """Test analysis endpoints in Docker environment"""

    # Use the Docker internal API URL
    BASE_URL = "http://localhost:8000/api/v1"

    print("🐳 Testing analysis endpoints in Docker...")
    print("=" * 50)

    # Step 1: Test basic API health
    print("\n1. Testing API health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API is healthy")
        else:
            print(f"   ❌ API returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False

    # Step 2: Test analysis submission
    print("\n2. Testing analysis submission...")
    try:
        response = requests.post(
            f"{BASE_URL}/analysis/custom",
            json={
                "query": "What are Petteri Orpo's main political positions?",
                "context_ids": ["petteri-orpo"],
                "detailed_response": True
            },
            timeout=15
        )

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analysis submitted successfully")
            print(f"   Analysis ID: {data.get('analysis_id')}")
            print(f"   Status URL: {data.get('status_url')}")

            # Step 3: Test status polling
            analysis_id = data.get('analysis_id')
            status_url = data.get('status_url')

            print(f"\n3. Testing status polling for {analysis_id}...")
            max_attempts = 15  # Increased for Docker
            attempt = 0

            while attempt < max_attempts:
                attempt += 1
                print(f"   Attempt {attempt}/{max_attempts}")

                try:
                    # Use the status URL as returned by the API
                    poll_url = f"{BASE_URL}{status_url}"
                    print(f"   Polling: {poll_url}")

                    poll_response = requests.get(poll_url, timeout=10)
                    print(f"   Status: {poll_response.status_code}")

                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        status = poll_data.get("status")
                        print(f"   Task Status: {status}")

                        if status == "completed":
                            print("   ✅ Analysis completed successfully!")
                            print(f"   Result preview: {str(poll_data.get('result', {}))[:200]}...")
                            return True
                        elif status == "failed":
                            print(f"   ❌ Analysis failed: {poll_data.get('error', 'Unknown error')}")
                            return False
                        elif status == "processing":
                            print("   ⏳ Still processing...")
                    elif poll_response.status_code == 404:
                        print(f"   ❌ 404 - Analysis task not found")
                        print("   This suggests the background task failed to store the result")
                        return False
                    else:
                        print(f"   Unexpected status: {poll_response.status_code}")

                except Exception as e:
                    print(f"   Error during polling: {e}")

                if attempt < max_attempts:
                    print("   Waiting 2 seconds...")
                    time.sleep(2)

            print("   ⏰ Timed out waiting for analysis completion")
            return False

        else:
            print(f"   ❌ Analysis submission failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Analysis test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_docker_analysis_endpoints()

    if success:
        print("\n🎉 Analysis endpoints are working in Docker!")
    else:
        print("\n💥 Analysis endpoints have issues in Docker.")
        print("\n🔧 Troubleshooting:")
        print("1. Check API logs: docker logs fpas-api")
        print("2. Check if background tasks are running")
        print("3. Check Neo4j connection in Docker")
        print("4. Check AI pipeline initialization in Docker")
