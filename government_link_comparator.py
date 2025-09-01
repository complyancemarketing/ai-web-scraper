#!/usr/bin/env python3
"""
Government Link Comparator
- Collects links like the initial add task
- Compares old XML with new XML
- Finds new/updated links
- Deletes old XML, keeps new one for next comparison
- Sends new links to latest updates page
"""

import os
import xml.etree.ElementTree as ET
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Dict, Tuple


class GovernmentLinkComparator:
    def __init__(self, db_path: str = 'scraping_scheduler.db'):
        self.db_path = db_path
        self.collections_dir = "collections"
        
    def collect_links_for_site(self, site_url: str) -> Tuple[str, int]:
        """
        Collect links for a government site using the same method as initial add task
        Returns: (xml_file_path, url_count)
        """
        try:
            print(f"🔄 Collecting links for: {site_url}")
            
            # Import the existing collection function
            from app import collect_links_to_xml
            
            # Use the same function that's used when adding a new task
            xml_path, url_count = collect_links_to_xml(site_url)
            
            if xml_path and url_count > 0:
                print(f"✅ Collected {url_count} links, saved to: {xml_path}")
                return xml_path, url_count
            else:
                print(f"❌ Failed to collect links for: {site_url}")
                return None, 0
                
        except Exception as e:
            print(f"❌ Error collecting links for {site_url}: {e}")
            return None, 0
    
    def find_previous_xml(self, site_url: str, current_xml_path: str) -> str:
        """Find the previous XML file for comparison"""
        try:
            domain = urlparse(site_url).netloc
            domain_clean = domain.replace('.', '_')
            
            previous_files = []
            
            # Look for XML files in collections directory
            if os.path.exists(self.collections_dir):
                for filename in os.listdir(self.collections_dir):
                    if (filename.startswith(domain_clean) and 
                        filename.endswith('.xml') and 
                        filename != os.path.basename(current_xml_path)):
                        filepath = os.path.join(self.collections_dir, filename)
                        previous_files.append(filepath)
            
            if previous_files:
                # Return the most recent previous file
                previous_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return previous_files[0]
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding previous XML: {e}")
            return None
    
    def extract_urls_from_xml(self, xml_path: str) -> List[str]:
        """Extract URLs from XML file"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            urls = []
            
            # Look for URLs in different possible XML structures
            for url_elem in root.findall('.//url'):
                loc_elem = url_elem.find('loc')
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text)
            
            # Also check for direct URL elements
            for url_elem in root.findall('.//url'):
                if url_elem.text:
                    urls.append(url_elem.text)
            
            # Check for any other URL-like elements
            for elem in root.iter():
                if elem.text and 'http' in elem.text:
                    # Simple heuristic to find URLs
                    text = elem.text.strip()
                    if text.startswith('http'):
                        urls.append(text)
            
            return list(set(urls))  # Remove duplicates
            
        except Exception as e:
            print(f"❌ Error extracting URLs from {xml_path}: {e}")
            return []
    
    def compare_xml_files(self, old_xml_path: str, new_xml_path: str) -> List[str]:
        """Compare old and new XML files to find new URLs"""
        try:
            print(f"🔄 Comparing XML files:")
            print(f"   Old: {old_xml_path}")
            print(f"   New: {new_xml_path}")
            
            # Extract URLs from both files
            old_urls = set(self.extract_urls_from_xml(old_xml_path))
            new_urls = set(self.extract_urls_from_xml(new_xml_path))
            
            print(f"📊 URLs found:")
            print(f"   Old XML: {len(old_urls)} URLs")
            print(f"   New XML: {len(new_urls)} URLs")
            
            # Find new URLs
            new_urls_only = new_urls - old_urls
            
            print(f"🎯 New URLs found: {len(new_urls_only)}")
            
            return list(new_urls_only)
            
        except Exception as e:
            print(f"❌ Error comparing XML files: {e}")
            return []
    
    def store_new_urls_in_database(self, domain: str, new_urls: List[str], comparison_file: str = None):
        """Store new URLs in the database for latest updates"""
        if not new_urls:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert each new URL
            for url in new_urls:
                cursor.execute('''
                    INSERT INTO sitemap_updates (domain, new_url, discovered_at, comparison_file, is_read)
                    VALUES (?, ?, ?, ?, ?)
                ''', (domain, url, datetime.now().isoformat(), comparison_file, False))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Stored {len(new_urls)} new URLs in database for domain: {domain}")
            
        except Exception as e:
            print(f"❌ Error storing new URLs in database: {e}")
    
    def cleanup_old_xml(self, old_xml_path: str):
        """Delete the old XML file after comparison"""
        try:
            if old_xml_path and os.path.exists(old_xml_path):
                os.remove(old_xml_path)
                print(f"🗑️ Deleted old XML: {old_xml_path}")
                
                # Also try to delete corresponding .txt and .json files if they exist
                base_path = old_xml_path.replace('.xml', '')
                txt_file = base_path + '.txt'
                json_file = base_path + '.json'
                
                if os.path.exists(txt_file):
                    os.remove(txt_file)
                    print(f"🗑️ Deleted old text file: {txt_file}")
                
                if os.path.exists(json_file):
                    os.remove(json_file)
                    print(f"🗑️ Deleted old JSON file: {json_file}")
                
                print(f"✅ Old files cleaned up successfully")
            else:
                print(f"⚠️ No old XML file to delete")
                
        except Exception as e:
            print(f"❌ Error cleaning up old XML: {e}")
    
    def process_site(self, site_url: str) -> Dict:
        """Process a single site: collect, compare, and update"""
        try:
            print(f"\n{'='*60}")
            print(f"🔄 Processing site: {site_url}")
            print(f"{'='*60}")
            
            # Step 1: Collect new links
            new_xml_path, url_count = self.collect_links_for_site(site_url)
            
            if not new_xml_path or url_count == 0:
                return {
                    'success': False,
                    'url': site_url,
                    'message': 'Failed to collect links',
                    'updates_found': 0
                }
            
            # Step 2: Find previous XML for comparison
            old_xml_path = self.find_previous_xml(site_url, new_xml_path)
            
            if not old_xml_path:
                print(f"📝 No previous data found for {site_url}, marking all URLs as new")
                # Extract all URLs from new XML and mark as new
                all_urls = self.extract_urls_from_xml(new_xml_path)
                domain = urlparse(site_url).netloc
                
                # Store all URLs as new
                self.store_new_urls_in_database(domain, all_urls, new_xml_path)
                
                return {
                    'success': True,
                    'url': site_url,
                    'url_count': url_count,
                    'xml_path': new_xml_path,
                    'updates_found': len(all_urls),
                    'message': f'First time collection: {len(all_urls)} URLs found'
                }
            
            # Step 3: Compare old vs new XML
            new_urls = self.compare_xml_files(old_xml_path, new_xml_path)
            
            # Step 4: Store new URLs in database
            if new_urls:
                domain = urlparse(site_url).netloc
                self.store_new_urls_in_database(domain, new_urls, new_xml_path)
            
            # Step 5: Clean up old XML (keep new one for next comparison)
            self.cleanup_old_xml(old_xml_path)
            
            return {
                'success': True,
                'url': site_url,
                'url_count': url_count,
                'xml_path': new_xml_path,
                'updates_found': len(new_urls),
                'message': f'Found {len(new_urls)} new URLs' if new_urls else 'No new URLs found'
            }
            
        except Exception as e:
            print(f"❌ Error processing site {site_url}: {e}")
            return {
                'success': False,
                'url': site_url,
                'message': f'Error: {str(e)}',
                'updates_found': 0
            }
    
    def process_all_sites(self) -> List[Dict]:
        """Process all active government sites"""
        try:
            print(f"🚀 Starting government link comparison for all sites")
            print(f"{'='*60}")
            
            # Get all active government sites from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, url FROM government_sites WHERE status = "active"')
            sites = cursor.fetchall()
            conn.close()
            
            if not sites:
                print("❌ No active government sites found")
                return []
            
            print(f"📋 Found {len(sites)} active government sites to process")
            
            results = []
            total_updates = 0
            
            # Process each site
            for site_id, site_url in sites:
                result = self.process_site(site_url)
                results.append(result)
                
                if result['success']:
                    total_updates += result.get('updates_found', 0)
            
            # Summary
            print(f"\n{'='*60}")
            print(f"📊 PROCESSING COMPLETE")
            print(f"{'='*60}")
            print(f"Total sites processed: {len(sites)}")
            print(f"Successful: {len([r for r in results if r['success']])}")
            print(f"Failed: {len([r for r in results if not r['success']])}")
            print(f"Total new URLs found: {total_updates}")
            print(f"{'='*60}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error processing all sites: {e}")
            return []


def main():
    """Main function for testing"""
    comparator = GovernmentLinkComparator()
    
    # Test with a single site
    test_url = input("Enter a government site URL to test: ").strip()
    if test_url:
        result = comparator.process_site(test_url)
        print(f"\nResult: {result}")
    
    # Or process all sites
    # results = comparator.process_all_sites()
    # print(f"\nAll results: {results}")


if __name__ == "__main__":
    main()
