"""
Quick test script to verify backend is working.
Run this to test if the backend is responding.
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_backend():
    print("=" * 60)
    print("Testing Backend Endpoints")
    print("=" * 60)
    print()
    
    # Test 1: Chatbot status
    print("Test 1: Chatbot Status Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/chatbot/status", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✓ Chatbot status endpoint working")
        else:
            print("✗ Chatbot status endpoint failed")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend. Is Flask app running?")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    print()
    
    # Test 2: Upload test endpoint
    print("Test 2: Upload Test Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/upload/test", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✓ Upload test endpoint working")
        else:
            print("✗ Upload test endpoint failed")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Test 3: Test CORS
    print("Test 3: CORS Headers")
    try:
        response = requests.options(f"{BASE_URL}/upload-multiple", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✓ CORS configured")
        else:
            print("⚠ CORS headers not found")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Test 4: Test upload endpoint (without files)
    print("Test 4: Upload Endpoint (without files)")
    try:
        response = requests.post(f"{BASE_URL}/upload-multiple", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 400:
            print("✓ Upload endpoint responding (expected 400 without files)")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    print("=" * 60)
    print("Backend Test Complete")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_backend()





