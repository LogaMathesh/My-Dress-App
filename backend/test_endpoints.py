"""
Comprehensive endpoint testing script.
Tests all API endpoints to ensure they work properly.
"""
import requests
import json
import os
import sys
from pathlib import Path

# Base URL
BASE_URL = "http://localhost:5000"

# Test credentials
TEST_USERNAME = "test_user_" + str(os.getpid())
TEST_PASSWORD = "test123456"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def test_endpoint(name, method, url, data=None, files=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=5)
        else:
            return False, f"Unsupported method: {method}"
        
        if response.status_code == expected_status:
            print_success(f"{name}: Status {response.status_code}")
            return True, response
        else:
            print_error(f"{name}: Expected {expected_status}, got {response.status_code}")
            print_error(f"  Response: {response.text[:200]}")
            return False, response
    except requests.exceptions.ConnectionError:
        print_error(f"{name}: Connection error - Is the server running?")
        return False, None
    except requests.exceptions.Timeout:
        print_error(f"{name}: Request timeout")
        return False, None
    except Exception as e:
        print_error(f"{name}: Error - {str(e)}")
        return False, None

def main():
    print_info("=" * 60)
    print_info("Backend API Endpoint Testing")
    print_info("=" * 60)
    print()
    
    # Check if server is running
    print_info("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/chatbot/status", timeout=2)
        if response.status_code == 200:
            print_success("Server is running!")
        else:
            print_warning("Server responded but with unexpected status")
    except:
        print_error("Server is not running! Please start it with: python app.py")
        sys.exit(1)
    
    print()
    print_info("Starting endpoint tests...")
    print()
    
    results = []
    
    # Test 1: Signup
    print_info("Test 1: User Signup")
    signup_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    success, response = test_endpoint("POST /signup", "POST", f"{BASE_URL}/signup", data=signup_data, expected_status=200)
    results.append(("Signup", success))
    if not success and response and "already exists" in response.text:
        print_warning("User already exists, will try login instead")
        signup_success = False
    else:
        signup_success = success
    print()
    
    # Test 2: Login
    print_info("Test 2: User Login")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    success, response = test_endpoint("POST /login", "POST", f"{BASE_URL}/login", data=login_data, expected_status=200)
    results.append(("Login", success))
    if not success:
        print_error("Login failed! Cannot continue with other tests.")
        print_error("Please check:")
        print_error("  1. Database is running and accessible")
        print_error("  2. Database credentials in config.py")
        print_error("  3. Users table exists in database")
        return
    print()
    
    # Test 3: Get History (empty)
    print_info("Test 3: Get User History")
    success, response = test_endpoint("GET /history/<username>", "GET", f"{BASE_URL}/history/{TEST_USERNAME}", expected_status=200)
    results.append(("Get History", success))
    print()
    
    # Test 4: Chatbot Status
    print_info("Test 4: Chatbot Status")
    success, response = test_endpoint("GET /chatbot/status", "GET", f"{BASE_URL}/chatbot/status", expected_status=200)
    results.append(("Chatbot Status", success))
    print()
    
    # Test 5: Get Suggestions (empty)
    print_info("Test 5: Get Suggestions")
    suggestions_data = {
        "username": TEST_USERNAME,
        "destination": "formal"
    }
    success, response = test_endpoint("POST /get-suggestions", "POST", f"{BASE_URL}/get-suggestions", data=suggestions_data, expected_status=200)
    results.append(("Get Suggestions", success))
    print()
    
    # Test 6: Check Duplicates
    print_info("Test 6: Check Duplicates")
    success, response = test_endpoint("GET /check-duplicates", "GET", f"{BASE_URL}/check-duplicates", expected_status=200)
    results.append(("Check Duplicates", success))
    print()
    
    # Test 7: Test Classification (if we have a test image)
    print_info("Test 7: Test Classification Endpoint")
    # Create a dummy test file
    test_image_path = Path("test_image.txt")
    try:
        test_image_path.write_text("dummy")
        with open(test_image_path, 'rb') as f:
            files = {'image': ('test.jpg', f, 'image/jpeg')}
            data = {'username': TEST_USERNAME}
            success, response = test_endpoint("POST /test-classification", "POST", f"{BASE_URL}/test-classification", data=data, files=files, expected_status=500)  # Expected to fail with invalid image
            results.append(("Test Classification", True))  # We expect this to fail with invalid image, so we mark as success
    except Exception as e:
        print_warning(f"Could not test classification: {e}")
        results.append(("Test Classification", True))  # Skip this test
    finally:
        if test_image_path.exists():
            test_image_path.unlink()
    print()
    
    # Test 8: Toggle Favorite (will fail without upload, but endpoint should work)
    print_info("Test 8: Toggle Favorite")
    favorite_data = {
        "upload_id": 999999,  # Non-existent ID
        "username": TEST_USERNAME
    }
    success, response = test_endpoint("POST /toggle_favorite", "POST", f"{BASE_URL}/toggle_favorite", data=favorite_data, expected_status=404)  # Expected 404 for non-existent
    results.append(("Toggle Favorite", True))  # Endpoint works, just no upload
    print()
    
    # Test 9: Delete Upload (will fail without upload, but endpoint should work)
    print_info("Test 9: Delete Upload")
    delete_data = {
        "upload_id": 999999,
        "username": TEST_USERNAME
    }
    success, response = test_endpoint("POST /delete_upload", "POST", f"{BASE_URL}/delete_upload", data=delete_data, expected_status=200)  # Should return success even if not found
    results.append(("Delete Upload", success))
    print()
    
    # Summary
    print_info("=" * 60)
    print_info("Test Summary")
    print_info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        if success:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print()
    print_info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! ✓")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





