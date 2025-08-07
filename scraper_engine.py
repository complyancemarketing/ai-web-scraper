import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import json
import logging
from urllib.parse import urljoin, urlparse
import time
import random
from typing import Dict, List, Optional, Any
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebScraper:
    """Advanced web scraping engine with intelligent data extraction"""
    
    def __init__(self, db_path: str = 'scraping_scheduler.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.init_scraping_db()
    
    def init_scraping_db(self):
        """Initialize database tables for storing scraped data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing scraped content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                content TEXT,
                extracted_data TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                FOREIGN KEY (task_id) REFERENCES scraping_tasks (id)
            )
        ''')
        
        # Table for storing scraping statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                response_time REAL,
                content_size INTEGER,
                status_code INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES scraping_tasks (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Scraping database initialized")
    
    def scrape_url(self, url: str, task_id: int) -> Dict[str, Any]:
        """
        Scrape a URL and extract structured data
        
        Args:
            url: The URL to scrape
            task_id: The ID of the scraping task
            
        Returns:
            Dictionary containing scraped data and metadata
        """
        start_time = time.time()
        result = {
            'url': url,
            'task_id': task_id,
            'success': False,
            'title': None,
            'content': None,
            'extracted_data': {},
            'error_message': None,
            'response_time': 0,
            'status_code': None,
            'content_size': 0
        }
        
        try:
            logger.info(f"Starting scrape for URL: {url}")
            
            # Add random delay to be respectful
            time.sleep(random.uniform(1, 3))
            
            # Make the request
            response = self.session.get(url, timeout=30)
            result['status_code'] = response.status_code
            result['response_time'] = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.reason}")
            
            # Parse the content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            result['title'] = self._extract_title(soup)
            result['content'] = self._extract_main_content(soup)
            result['extracted_data'] = self._extract_structured_data(soup, url)
            result['content_size'] = len(response.content)
            result['success'] = True
            
            logger.info(f"Successfully scraped {url} - Content size: {result['content_size']} bytes")
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout error while scraping {url}"
            logger.error(error_msg)
            result['error_message'] = error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"Connection error while scraping {url}"
            logger.error(error_msg)
            result['error_message'] = error_msg
        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            logger.error(error_msg)
            result['error_message'] = error_msg
        
        # Store the result in database
        self._store_scraped_data(result)
        
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Try to find main content areas
        main_content = ""
        
        # Look for main content containers
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '#content',
            '#main',
            '.post-content',
            '.entry-content'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                main_content = content.get_text(separator=' ', strip=True)
                break
        
        # If no main content found, get all text
        if not main_content:
            main_content = soup.get_text(separator=' ', strip=True)
        
        # Clean up the content
        main_content = re.sub(r'\s+', ' ', main_content)
        return main_content[:10000]  # Limit content size
    
    def _extract_structured_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract structured data from the page"""
        structured_data = {
            'meta_tags': {},
            'links': [],
            'images': [],
            'tables': [],
            'forms': []
        }
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                structured_data['meta_tags'][name] = content
        
        # Extract links
        links = soup.find_all('a', href=True)
        for link in links[:50]:  # Limit to first 50 links
            href = link.get('href')
            text = link.get_text(strip=True)
            if href and text:
                full_url = urljoin(url, href)
                structured_data['links'].append({
                    'url': full_url,
                    'text': text[:100]  # Limit text length
                })
        
        # Extract images
        images = soup.find_all('img')
        for img in images[:20]:  # Limit to first 20 images
            src = img.get('src')
            alt = img.get('alt', '')
            if src:
                full_url = urljoin(url, src)
                structured_data['images'].append({
                    'url': full_url,
                    'alt': alt[:100]
                })
        
        # Extract tables
        tables = soup.find_all('table')
        for table in tables[:5]:  # Limit to first 5 tables
            table_data = []
            rows = table.find_all('tr')
            for row in rows[:10]:  # Limit to first 10 rows
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    table_data.append(row_data)
            if table_data:
                structured_data['tables'].append(table_data)
        
        return structured_data
    
    def _store_scraped_data(self, result: Dict[str, Any]):
        """Store scraped data in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store main scraped data
            cursor.execute('''
                INSERT INTO scraped_data 
                (task_id, url, title, content, extracted_data, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['task_id'],
                result['url'],
                result['title'],
                result['content'],
                json.dumps(result['extracted_data']),
                'success' if result['success'] else 'error',
                result['error_message']
            ))
            
            # Store scraping statistics
            cursor.execute('''
                INSERT INTO scraping_stats 
                (task_id, url, response_time, content_size, status_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                result['task_id'],
                result['url'],
                result['response_time'],
                result['content_size'],
                result['status_code']
            ))
            
            conn.commit()
            logger.info(f"Stored scraped data for task {result['task_id']}")
            
        except Exception as e:
            logger.error(f"Error storing scraped data: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_scraped_data(self, task_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve scraped data for a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, url, title, content, extracted_data, scraped_at, status, error_message
            FROM scraped_data 
            WHERE task_id = ? 
            ORDER BY scraped_at DESC 
            LIMIT ?
        ''', (task_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'content': row[3],
                'extracted_data': json.loads(row[4]) if row[4] else {},
                'scraped_at': row[5],
                'status': row[6],
                'error_message': row[7]
            })
        
        conn.close()
        return results
    
    def get_scraping_stats(self, task_id: int) -> Dict[str, Any]:
        """Get scraping statistics for a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_scrapes,
                AVG(response_time) as avg_response_time,
                AVG(content_size) as avg_content_size,
                MAX(scraped_at) as last_scrape,
                MIN(scraped_at) as first_scrape
            FROM scraping_stats 
            WHERE task_id = ?
        ''', (task_id,))
        
        stats = cursor.fetchone()
        
        # Get success rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
            FROM scraped_data 
            WHERE task_id = ?
        ''', (task_id,))
        
        success_stats = cursor.fetchone()
        
        conn.close()
        
        if stats and success_stats:
            return {
                'total_scrapes': stats[0],
                'avg_response_time': round(stats[1], 2) if stats[1] else 0,
                'avg_content_size': round(stats[2], 2) if stats[2] else 0,
                'last_scrape': stats[3],
                'first_scrape': stats[4],
                'success_rate': round((success_stats[1] / success_stats[0]) * 100, 2) if success_stats[0] > 0 else 0
            }
        
        return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old scraped data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete old scraped data
            cursor.execute('''
                DELETE FROM scraped_data 
                WHERE scraped_at < datetime('now', '-{} days')
            '''.format(days))
            
            # Delete old stats
            cursor.execute('''
                DELETE FROM scraping_stats 
                WHERE scraped_at < datetime('now', '-{} days')
            '''.format(days))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
            conn.rollback()
        finally:
            conn.close() 