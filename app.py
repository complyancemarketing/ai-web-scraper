from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Database initialization
def init_db():
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraping_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            schedule TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Create table for storing scraped updates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            page_url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_hash TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_task', methods=['POST'])
def add_task():
    url = request.form.get('url')
    schedule = request.form.get('schedule')
    
    if not url or not schedule:
        flash('Please fill in all fields', 'error')
        return redirect(url_for('index'))
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scraping_tasks (url, schedule) 
            VALUES (?, ?)
        ''', (url, schedule))
        conn.commit()
        conn.close()
        flash('Task added successfully!', 'success')
    except Exception as e:
        flash('Error adding task. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/tasks')
def tasks():
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraping_tasks ORDER BY created_at DESC')
    tasks = cursor.fetchall()
    conn.close()
    
    return render_template('tasks.html', tasks=tasks)

@app.route('/api/tasks')
def api_tasks():
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraping_tasks ORDER BY created_at DESC')
    tasks = cursor.fetchall()
    conn.close()
    
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task[0],
            'url': task[1],
            'schedule': task[2],
            'created_at': task[3],
            'last_run': task[4],
            'status': task[5]
        })
    
    return jsonify(task_list)

@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    schedule = request.form.get('schedule')
    status = request.form.get('status')
    
    if not schedule or not status:
        return jsonify({'success': False, 'message': 'Please fill in all fields'}), 400
    
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE scraping_tasks 
            SET schedule = ?, status = ?
            WHERE id = ?
        ''', (schedule, status, task_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Task updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error updating task'}), 500

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scraping_tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error deleting task'})

@app.route('/integrated_apps')
def integrated_apps():
    return render_template('integrated_apps.html')

@app.route('/latest_updates')
def latest_updates():
    # Fetch the latest scraped updates from the database
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, page_url, title, scraped_at 
        FROM scraped_updates 
        ORDER BY scraped_at DESC 
        LIMIT 50
    ''')
    updates = cursor.fetchall()
    conn.close()
    
    return render_template('latest_updates.html', updates=updates)

@app.route('/delete_update/<int:update_id>', methods=['POST'])
def delete_update(update_id):
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scraped_updates WHERE id = ?', (update_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Update deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error deleting update'}), 500

@app.route('/delete_all_updates', methods=['POST'])
def delete_all_updates():
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scraped_updates')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All updates deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error deleting all updates'}), 500

def scrape_latest_updates(url):
    """
    Scrape the latest updates from the given URL for the last 5 days
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get all links from the page
        links = soup.find_all('a', href=True)
        
        updates = []
        base_url = url
        five_days_ago = datetime.now() - timedelta(days=5)
        
        for link in links:
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute URLs
                full_url = urljoin(base_url, href)
                
                # Only process links that are from the same domain
                if urlparse(full_url).netloc == urlparse(url).netloc:
                    # Create a hash for this URL to avoid duplicates
                    url_hash = hashlib.md5(full_url.encode()).hexdigest()
                    
                    # Check if this update already exists in database
                    conn = sqlite3.connect('scraping_scheduler.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM scraped_updates WHERE update_hash = ?', (url_hash,))
                    existing = cursor.fetchone()
                    
                    if not existing:
                        # Get the title of the link
                        title = link.get_text(strip=True)
                        if not title:
                            title = full_url
                        
                        # Look for date patterns in the link text or nearby elements
                        link_text = link.get_text()
                        parent_text = link.parent.get_text() if link.parent else ""
                        
                        # Check for recent date patterns (last 5 days)
                        recent_date_patterns = [
                            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
                            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # MM.DD.YYYY
                        ]
                        
                        is_recent = False
                        for pattern in recent_date_patterns:
                            matches = re.findall(pattern, link_text + " " + parent_text)
                            for match in matches:
                                try:
                                    if len(match) == 3:
                                        month, day, year = int(match[0]), int(match[1]), int(match[2])
                                        # Handle different date formats
                                        if year > 2000:  # Assume it's YYYY-MM-DD or YYYY/MM/DD
                                            date_obj = datetime(year, month, day)
                                        else:  # Assume it's MM/DD/YYYY
                                            date_obj = datetime(year, month, day)
                                        
                                        if date_obj >= five_days_ago:
                                            is_recent = True
                                            break
                                except:
                                    continue
                        
                        # Also check for "today", "yesterday", "recent" keywords
                        recent_keywords = ['today', 'yesterday', 'recent', 'new', 'latest', 'updated']
                        if any(keyword in link_text.lower() for keyword in recent_keywords):
                            is_recent = True
                        
                        # For now, include all links but prioritize recent ones
                        # Store the update in database
                        cursor.execute('''
                            INSERT INTO scraped_updates (url, page_url, title, content, update_hash)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (url, full_url, title, str(link), url_hash))
                        conn.commit()
                        
                        updates.append({
                            'url': full_url,
                            'title': title,
                            'scraped_at': datetime.now(),
                            'is_recent': is_recent
                        })
                    
                    conn.close()
        
        return updates
        
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return []

@app.route('/scrape_now', methods=['POST'])
def scrape_now():
    url = request.form.get('url')
    
    if not url:
        return jsonify({'success': False, 'message': 'Please provide a URL'}), 400
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Perform the scraping
        updates = scrape_latest_updates(url)
        
        if updates:
            return jsonify({
                'success': True, 
                'message': f'Successfully scraped {len(updates)} new updates from {url}',
                'updates_count': len(updates)
            })
        else:
            return jsonify({
                'success': True, 
                'message': f'No new updates found for {url}',
                'updates_count': 0
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error scraping {url}: {str(e)}'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) 