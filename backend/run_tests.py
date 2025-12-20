"""
Quick test runner - checks if server can start and basic endpoints work.
"""
import subprocess
import time
import sys
import os

def check_server():
    """Check if server is running"""
    try:
        import requests
        response = requests.get("http://localhost:5000/chatbot/status", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("=" * 60)
    print("Backend Server Test Runner")
    print("=" * 60)
    print()
    
    # Check if server is already running
    if check_server():
        print("✓ Server is already running!")
        print("  You can now run: python test_endpoints.py")
        return 0
    
    print("Server is not running.")
    print("Starting server in test mode...")
    print()
    print("=" * 60)
    print("IMPORTANT: Keep this window open!")
    print("The server will start and you can test endpoints.")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)
    print()
    
    # Try to start the server
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        process = subprocess.Popen([sys.executable, "app.py"], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if server started
        if check_server():
            print("✓ Server started successfully!")
            print()
            print("You can now:")
            print("  1. Run 'python test_endpoints.py' in another terminal")
            print("  2. Test endpoints manually")
            print()
            print("Server is running. Press Ctrl+C to stop...")
            
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\nStopping server...")
                process.terminate()
                process.wait()
                print("Server stopped.")
        else:
            print("✗ Server failed to start!")
            stdout, stderr = process.communicate(timeout=5)
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return 1
            
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())





