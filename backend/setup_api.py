#!/usr/bin/env python3
"""
Setup script for configuring Gemini API key for the dress classification system.
"""

import os
import sys
from config import config
from gemini_client import gemini_classifier


def main():
    print("🔧 Dress Classification API Setup")
    print("=" * 40)
    
    # Check current status
    if config.is_configured():
        print(f"✅ API key is already configured!")
        print(f"📝 Current model: {config.get_gemini_model()}")
        
        # Test connection
        print("\n🔍 Testing connection...")
        success, message = gemini_classifier.test_connection()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        # Ask if user wants to update
        update = input("\n🤔 Do you want to update the API key? (y/N): ").strip().lower()
        if update not in ['y', 'yes']:
            print("👋 Setup completed!")
            return
    else:
        print("❌ No API key configured.")
    
    print("\n📋 To get your Gemini API key:")
    print("1. Go to https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Copy the API key")
    
    print("\n🔑 Please enter your Gemini API key:")
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return
    
    # Validate API key format (basic check)
    if not api_key.startswith('AIza') or len(api_key) < 39:
        print("⚠️  Warning: This doesn't look like a valid Gemini API key.")
        print("   Gemini API keys typically start with 'AIza' and are ~39 characters long.")
        confirm = input("   Do you want to continue anyway? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Setup cancelled.")
            return
    
    # Save the API key
    print("\n💾 Saving API key...")
    success = config.set_gemini_api_key(api_key)
    
    if success:
        print("✅ API key saved successfully!")
        
        # Test the connection
        print("\n🔍 Testing API connection...")
        
        # Reinitialize classifier
        gemini_classifier.__init__()
        
        success, message = gemini_classifier.test_connection()
        if success:
            print(f"✅ {message}")
            print("\n🎉 Setup completed successfully!")
            print("🚀 You can now start the Flask server with: python app.py")
        else:
            print(f"❌ Connection test failed: {message}")
            print("\n🔍 Please check your API key and try again.")
            print("   You can run this setup script again to update the key.")
    else:
        print("❌ Failed to save API key.")
        print("   Please check file permissions and try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)