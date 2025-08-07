#!/usr/bin/env python3
"""
Test script for the web scraping functionality
"""

import requests
import json

def test_scraping():
    """Test the scraping functionality"""
    url = "http://localhost:8080"
    
    # Test data
    test_url = "https://example.com"
    
    print("Testing scraping functionality...")
    print(f"Target URL: {test_url}")
    
    try:
        # Test the scraping endpoint
        response = requests.post(
            f"{url}/scrape_now",
            data={'url': test_url},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Scraping successful!")
            print(f"Message: {result.get('message', 'No message')}")
            print(f"Updates found: {result.get('updates_count', 0)}")
        else:
            print(f"❌ Scraping failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Make sure the Flask app is running.")
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    test_scraping() 