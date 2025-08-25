from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os
import sys

# Add the scrapy directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapy'))

# Import scrapy components
from scrapy.main import ScrapingTool
from scrapy.core.config import Config

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize scrapy tool
def get_scraping_tool():
    """Get a configured scraping tool instance"""
    # Set the scrapy base directory to the scrapy folder
    scrapy_dir = os.path.join(os.path.dirname(__file__), 'scrapy')
    return ScrapingTool(base_dir=scrapy_dir)

# Database initialization
def init_db():
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    
    # Create table with original columns first
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
    
    # Create sitemap updates table for latest updates feature
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sitemap_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            new_url TEXT NOT NULL,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comparison_file TEXT,
            is_read BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Add new columns if they don't exist
    try:
        cursor.execute('ALTER TABLE scraping_tasks ADD COLUMN sitemap_fetched BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE scraping_tasks ADD COLUMN initial_sitemap_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute('ALTER TABLE scraping_tasks ADD COLUMN last_sitemap_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
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
        # Step 1: Immediately fetch the initial sitemap using scrapy
        print(f"🚀 Fetching initial sitemap for: {url}")
        scraping_tool = get_scraping_tool()
        
        # Fetch the sitemap (this will store it in scrapy/sitemaps/)
        sitemap_success = scraping_tool.fetch_sitemap(url)
        
        if sitemap_success:
            # Get sitemap count for tracking
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            initial_count = scraping_tool.get_latest_sitemap_url_count(domain)
            
            print(f"✅ Initial sitemap fetched successfully! Found {initial_count} URLs")
            flash(f'Task added successfully! Initial sitemap fetched with {initial_count} URLs.', 'success')
            
            # Step 2: Store the task in database with sitemap info
            conn = sqlite3.connect('scraping_scheduler.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_tasks (url, schedule, sitemap_fetched, initial_sitemap_count, last_sitemap_count) 
                VALUES (?, ?, ?, ?, ?)
            ''', (url, schedule, True, initial_count, initial_count))
            conn.commit()
            conn.close()
            
        else:
            print(f"❌ Failed to fetch initial sitemap for: {url}")
            flash(f'Task added successfully, but could not fetch sitemap for {url}. The URL may not have a sitemap or may be unreachable. The task will still monitor for changes.', 'warning')
            
            # Still store the task but mark sitemap as not fetched
            conn = sqlite3.connect('scraping_scheduler.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_tasks (url, schedule, sitemap_fetched, initial_sitemap_count, last_sitemap_count) 
                VALUES (?, ?, ?, ?, ?)
            ''', (url, schedule, False, 0, 0))
            conn.commit()
            conn.close()
            
    except Exception as e:
        print(f"❌ Error in add_task: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error adding task: {str(e)}', 'error')
    
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
            'status': task[5],
            'sitemap_fetched': task[6] if len(task) > 6 else False,
            'initial_sitemap_count': task[7] if len(task) > 7 else 0,
            'last_sitemap_count': task[8] if len(task) > 8 else 0
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

@app.route('/delete_all_tasks', methods=['POST'])
def delete_all_tasks():
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scraping_tasks')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All tasks deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error deleting all tasks'})

@app.route('/delete_all_updates', methods=['POST'])
def delete_all_updates():
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sitemap_updates')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All updates deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error deleting all updates'})

@app.route('/test_sitemap/<path:url>')
def test_sitemap(url):
    """Test if a URL has a fetchable sitemap"""
    try:
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        scraping_tool = get_scraping_tool()
        sitemap_success = scraping_tool.fetch_sitemap(url)
        
        if sitemap_success:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            count = scraping_tool.get_latest_sitemap_url_count(domain)
            return jsonify({
                'success': True, 
                'message': f'Sitemap found with {count} URLs',
                'url_count': count
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'No sitemap found or URL unreachable'
            })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error testing sitemap: {str(e)}'
        })

@app.route('/integrated_apps')
def integrated_apps():
    return render_template('integrated_apps.html')

@app.route('/latest_updates')
def latest_updates():
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, domain, new_url, discovered_at 
        FROM sitemap_updates 
        ORDER BY discovered_at DESC 
        LIMIT 100
    ''')
    updates = cursor.fetchall()
    conn.close()
    
    return render_template('latest_updates.html', updates=updates)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) 