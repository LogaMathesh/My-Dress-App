#!/usr/bin/env python3
"""
Test script to verify image display in chatbot
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_chatbot_with_images():
    """Test chatbot query that should return images"""
    try:
        # Test with a user who has images
        data = {
            "user_id": "loga",  # Replace with an actual user who has images
            "query": "show me my clothes"
        }
        
        print("Testing chatbot query with images...")
        response = requests.post(
            f"{BASE_URL}/chatbot/query",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful!")
            print(f"📊 Found {result['count']} results")
            
            if result['results']:
                print("\n🖼️  Image URLs:")
                for i, img in enumerate(result['results'], 1):
                    print(f"  {i}. {img['url']}")
                    print(f"     Style: {img['style']}")
                    print(f"     Color: {img['color']}")
                    print(f"     Score: {img['score']:.2f}")
                    print()
            else:
                print("❌ No images found. Make sure to index existing images first.")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing chatbot: {e}")

def test_image_urls():
    """Test if image URLs are accessible"""
    try:
        # Test a sample image URL
        test_url = "http://localhost:5000/image/test.jpg"
        response = requests.head(test_url)
        print(f"Image URL test: {response.status_code}")
    except Exception as e:
        print(f"Image URL test failed: {e}")

if __name__ == "__main__":
    print("🖼️  Testing Image Display in Chatbot")
    print("=" * 40)
    
    test_chatbot_with_images()
    print("\n" + "=" * 40)
    test_image_urls()
