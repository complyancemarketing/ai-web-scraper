import os
import sys
import sqlite3
import threading
import time
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Add the scrapy directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapy'))

# Import scrapy components
from scrapy.main import ScrapingTool

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize scrapy tool
def get_scraping_tool():
    """Get a configured scraping tool instance"""
    # Set the scrapy base directory to the scrapy folder
    scrapy_dir = os.path.join(os.path.dirname(__file__), 'scrapy')
    return ScrapingTool(base_dir=scrapy_dir)

def format_timestamp(timestamp_str, format_type='date'):
    """Format timestamp string for display"""
    if not timestamp_str:
        return 'N/A' if format_type == 'date' else 'Never'
    
    try:
        # Try ISO format first (with T and microseconds)
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('T', ' '))
        else:
            # Fall back to standard format
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        
        if format_type == 'date':
            return dt.strftime('%d-%m-%Y')
        elif format_type == 'datetime':
            formatted_date = dt.strftime('%d-%m-%Y')
            formatted_time = dt.strftime('%I:%M%p').lower()
            return f"{formatted_date} / {formatted_time}"
        else:
            return timestamp_str
    except:
        return timestamp_str[:10] if timestamp_str else ('N/A' if format_type == 'date' else 'Never')

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
    
    # Create workflow_apps table to track last run times
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_apps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL UNIQUE,
            description TEXT,
            status TEXT DEFAULT 'Connected',
            last_run TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default workflow apps if they don't exist
    default_apps = [
        ('Webhook', 'Send data to external services via HTTP requests'),
        ('n8n', 'Workflow automation and data processing'),
        ('Google Drive', 'Store and manage files in the cloud'),
        ('Google Sheets', 'Export data to spreadsheets for analysis'),
        ('Airtable', 'Organize data in flexible databases'),
        ('Microsoft Teams', 'Send notifications and updates to teams'),
        ('LinkedIn', 'Professional networking and lead generation')
    ]
    
    for app_name, description in default_apps:
        cursor.execute('''
            INSERT OR IGNORE INTO workflow_apps (app_name, description) 
            VALUES (?, ?)
        ''', (app_name, description))
    
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
        
    try:
        cursor.execute('ALTER TABLE scraping_tasks ADD COLUMN comparison_result TEXT DEFAULT "Not checked"')
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
            domain = urlparse(url).netloc
            initial_count = scraping_tool.get_latest_sitemap_url_count(domain)
            
            print(f"✅ Initial sitemap fetched successfully! Found {initial_count} URLs")
            print(f"📁 Initial sitemap stored for future comparison")
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
    tasks_raw = cursor.fetchall()
    conn.close()
    
    # Format the timestamps for display
    tasks = []
    for task in tasks_raw:
        task_list = list(task)
        
        # Format created_at (task[3])
        task_list[3] = format_timestamp(task[3], 'date')
        
        # Format last_run (task[4]) 
        task_list[4] = format_timestamp(task[4], 'datetime')
        
        tasks.append(tuple(task_list))
    
    return render_template('tasks.html', tasks=tasks)

@app.route('/api/tasks')
def api_tasks():
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scraping_tasks ORDER BY created_at DESC')
    tasks_raw = cursor.fetchall()
    conn.close()
    
    # Format the timestamps for display (same as /tasks route)
    tasks = []
    for task in tasks_raw:
        task_list = list(task)
        
        # Format created_at (task[3])
        task_list[3] = format_timestamp(task[3], 'date')
        
        # Format last_run (task[4]) 
        task_list[4] = format_timestamp(task[4], 'datetime')
        
        tasks.append(tuple(task_list))
    
    return jsonify({'success': True, 'tasks': tasks})

@app.route('/edit_task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    schedule = request.form.get('schedule')
    
    if not schedule:
        return jsonify({'success': False, 'message': 'Please fill in schedule field'}), 400
    
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE scraping_tasks 
            SET schedule = ?
            WHERE id = ?
        ''', (schedule, task_id))
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

@app.route('/run_all_tasks', methods=['POST'])
def run_all_tasks():
    try:
        # Get all active tasks
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, url FROM scraping_tasks WHERE status = "active"')
        active_tasks = cursor.fetchall()
        conn.close()
        
        if not active_tasks:
            return jsonify({'success': False, 'message': 'No active tasks found'})
        
        # Shared list to collect results for batch notification
        batch_results = []
        batch_results_lock = threading.Lock()
        
        # Function to fetch sitemap and compare for a single task
        def process_single_task(task_id, task_url, task_index, total_tasks):
            try:
                print(f"\n{'='*60}")
                print(f"PROCESSING TASK {task_index}/{total_tasks}: {task_url}")
                print(f"{'='*60}")
                
                # Get scraping tool instance
                tool = get_scraping_tool()
                
                # Enable individual Teams notifications for batch processing
                # This ensures notifications are sent when changes are detected
                tool.configure_teams_notifications(enabled=True)
                
                # Extract domain from URL
                domain = urlparse(task_url).netloc
                
                # Step 1: Fetch current sitemap
                print(f"📥 Step 1: Fetching sitemap for {task_url}...")
                sitemap_fetched = tool.fetch_sitemap(task_url)
                
                result_text = "Error fetching sitemap"
                result_data = {
                    'domain': domain,
                    'has_changes': False,
                    'total_added': 0,
                    'total_modified': 0,
                    'error': False
                }
                
                if sitemap_fetched:
                    # Step 2: Compare with previous sitemap (old sitemap will be automatically deleted after comparison)
                    print(f"🔍 Step 2: Comparing sitemaps for {domain}...")
                    print(f"Note: Old sitemap will be automatically deleted after comparison")
                    comparison_result = tool.compare_sitemaps(domain)
                    
                    # The comparison automatically stores new URLs in sitemap_updates table
                    if comparison_result and comparison_result.get('has_changes'):
                        added_count = comparison_result.get('total_added', 0)
                        modified_count = comparison_result.get('total_modified', 0)
                        
                        if added_count > 0 or modified_count > 0:
                            update_parts = []
                            if added_count > 0:
                                update_parts.append(f"{added_count} new URLs")
                            if modified_count > 0:
                                update_parts.append(f"{modified_count} modified URLs")
                            result_text = " and ".join(update_parts) + " found"
                            
                            result_data.update({
                                'has_changes': True,
                                'total_added': added_count,
                                'total_modified': modified_count
                            })
                        else:
                            result_text = "No update"
                        print(f"✅ Found {added_count} new URLs and {modified_count} modified URLs for {domain}")
                    else:
                        result_text = "No update"
                        print(f"✅ No changes found for {domain}")
                else:
                    print(f"❌ Failed to fetch sitemap for {task_url}")
                    result_data['error'] = True
                    result_text = "Error"
                
                # Add result to batch collection
                with batch_results_lock:
                    batch_results.append(result_data)
                
                # Update the comparison result in the database
                conn = sqlite3.connect('scraping_scheduler.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE scraping_tasks SET comparison_result = ? WHERE id = ?', (result_text, task_id))
                conn.commit()
                conn.close()
                
                print(f"✅ Task {task_index}/{total_tasks} completed for {domain}")
                    
            except Exception as e:
                print(f"❌ Error processing task {task_index}/{total_tasks} for {task_url}: {e}")
                import traceback
                traceback.print_exc()
                
                # Add error result to batch collection
                with batch_results_lock:
                    batch_results.append({
                        'domain': domain if 'domain' in locals() else 'Unknown',
                        'has_changes': False,
                        'total_added': 0,
                        'total_modified': 0,
                        'error': True
                    })
                
                # Update with error status
                try:
                    conn = sqlite3.connect('scraping_scheduler.db')
                    cursor = conn.cursor()
                    cursor.execute('UPDATE scraping_tasks SET comparison_result = ? WHERE id = ?', ("Error", task_id))
                    conn.commit()
                    conn.close()
                except:
                    pass
        
        # Process tasks sequentially to handle load properly
        print(f"\n🚀 Starting sequential processing of {len(active_tasks)} tasks...")
        print(f"📊 Processing one task at a time to ensure stability and proper sitemap deletion")
        
        for index, (task_id, task_url) in enumerate(active_tasks, 1):
            print(f"\n🔄 Processing task {index}/{len(active_tasks)}...")
            
            try:
                process_single_task(task_id, task_url, index, len(active_tasks))
            except Exception as e:
                print(f"❌ Unexpected error in task {index}: {e}")
                import traceback
                traceback.print_exc()
            
            # Add a small delay between tasks to prevent overwhelming servers
            if index < len(active_tasks):
                print(f"⏳ Waiting 2 seconds before next task...")
                time.sleep(2)
        
        # Update last_run for all active tasks
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute('UPDATE scraping_tasks SET last_run = ? WHERE status = "active"', (current_time,))
        conn.commit()
        conn.close()
        
        # Send batch notification after sequential processing
        def send_batch_notification():
            try:
                # Send batch Teams notification if there are results
                if batch_results:
                    from scrapy.core.teams_notifier import TeamsNotifier
                    notifier = TeamsNotifier()
                    success = notifier.send_batch_summary(batch_results)
                    if success:
                        print(f"✅ Batch Teams notification sent for {len(batch_results)} domains")
                        # Update last run time for workflow apps
                        update_workflow_app_last_run('Webhook')
                        update_workflow_app_last_run('n8n')
                        update_workflow_app_last_run('Microsoft Teams')
                    else:
                        print(f"⚠️ Failed to send batch Teams notification")
                else:
                    print("ℹ️ No batch results to send notification for")
                
            except Exception as e:
                print(f"Error in batch notification: {e}")
        
        # Send batch notification immediately after sequential processing
        send_batch_notification()
        
        return jsonify({
            'success': True, 
            'message': f'Started sequential sitemap checking for {len(active_tasks)} active tasks. Processing one task at a time for stability. Teams notification sent.'
        })
        
    except Exception as e:
        print(f"❌ Error in run_all_tasks: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error running tasks: {str(e)}'})

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

@app.route('/api/workflow_apps')
def api_workflow_apps():
    """Get all workflow apps with their last run times"""
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT app_name, description, status, last_run FROM workflow_apps ORDER BY app_name')
    apps = cursor.fetchall()
    conn.close()
    
    app_list = []
    for app in apps:
        app_list.append({
            'app_name': app[0],
            'description': app[1],
            'status': app[2],
            'last_run': app[3]
        })
    
    return jsonify(app_list)

def update_workflow_app_last_run(app_name: str):
    """Update the last run time for a workflow app"""
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        current_time = datetime.now().isoformat()
        cursor.execute('''
            UPDATE workflow_apps 
            SET last_run = ? 
            WHERE app_name = ?
        ''', (current_time, app_name))
        conn.commit()
        conn.close()
        print(f"✅ Updated last run time for {app_name}")
    except Exception as e:
        print(f"❌ Error updating last run time for {app_name}: {e}")



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
    updates_raw = cursor.fetchall()
    conn.close()
    
    # Format the timestamps
    updates = []
    for update in updates_raw:
        # Parse the timestamp and format it as "26-08-2025 / 4:55pm"
        try:
            # Try ISO format first (with T and microseconds)
            if 'T' in update[3]:
                dt = datetime.fromisoformat(update[3].replace('T', ' '))
            else:
                # Fall back to standard format
                dt = datetime.strptime(update[3], '%Y-%m-%d %H:%M:%S')
            formatted_time = dt.strftime('%d-%m-%Y / %I:%M%p').lower()
        except:
            # If parsing fails, use the original timestamp
            formatted_time = update[3]
        # Create new tuple with formatted timestamp
        formatted_update = (update[0], update[1], update[2], formatted_time)
        updates.append(formatted_update)
    
    return render_template('latest_updates.html', updates=updates)

@app.route('/government_dashboard')
def government_dashboard():
    return render_template('government_dashboard.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) 