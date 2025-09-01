#!/usr/bin/env python3
"""
Test script for Government Link Comparator
This shows how the new system works without touching the sitemap dashboard
"""

from government_link_comparator import GovernmentLinkComparator

def test_single_site():
    """Test with a single government site"""
    print("🧪 Testing Government Link Comparator with single site")
    print("=" * 60)
    
    comparator = GovernmentLinkComparator()
    
    # Test URL (you can change this)
    test_url = "https://www.impots.gouv.fr/recherche/e-invoicing"
    
    print(f"Testing with: {test_url}")
    
    # Process the site
    result = comparator.process_site(test_url)
    
    print(f"\n📊 Result:")
    print(f"Success: {result['success']}")
    print(f"URLs collected: {result.get('url_count', 0)}")
    print(f"New URLs found: {result.get('updates_found', 0)}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    return result

def test_all_sites():
    """Test with all government sites"""
    print("🧪 Testing Government Link Comparator with all sites")
    print("=" * 60)
    
    comparator = GovernmentLinkComparator()
    
    # Process all sites
    results = comparator.process_all_sites()
    
    print(f"\n📊 All Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['url']}")
        print(f"   Success: {result['success']}")
        print(f"   URLs: {result.get('url_count', 0)}")
        print(f"   Updates: {result.get('updates_found', 0)}")
        print(f"   Message: {result.get('message', 'N/A')}")
        print()
    
    return results

if __name__ == "__main__":
    print("🚀 Government Link Comparator Test")
    print("=" * 60)
    
    # Choose what to test
    choice = input("Choose test:\n1. Single site\n2. All sites\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_single_site()
    elif choice == "2":
        test_all_sites()
    else:
        print("Invalid choice. Running single site test...")
        test_single_site()
