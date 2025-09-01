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
from scrapy.core.collector import WebsiteCollector
# Government scrapers are now accessed through gov_backend/collector.py
# This provides a cleaner separation and redirects to gov.py for specialized scraping

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
    
    # Create government_sites table for government dashboard
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS government_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            schedule TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_check TIMESTAMP,
            status TEXT DEFAULT 'active'
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
    
            # Add comparison_result column to government_sites table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE government_sites ADD COLUMN comparison_result TEXT DEFAULT "NOT CHECKED"')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Reset all existing comparison_result values to "NOT CHECKED" to ensure clean state
        try:
            cursor.execute('UPDATE government_sites SET comparison_result = "NOT CHECKED"')
        except sqlite3.OperationalError:
            pass  # Column might not exist yet
    
    conn.commit()
    conn.close()

def _load_gov_collector():
    """Dynamically load the consolidated government collector."""
    try:
        import importlib.util
        base_dir = os.path.dirname(__file__)
        collector_path = os.path.join(base_dir, 'scrapy', 'code ', 'gov_backend', 'collector.py')
        spec = importlib.util.spec_from_file_location('gov_backend_collector', collector_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
    except Exception as e:
        print(f"❌ Failed to load consolidated collector: {e}")
        import traceback
        traceback.print_exc()
    return None

def check_gov_py_base_urls(url: str) -> str:
    """
    Check if the URL matches any base URLs in gov.py
    Returns the matching base URL or None
    """
    # Base URLs from gov.py ScraperConfig
    gov_base_urls = {
        "https://einvoice.belgium.be": "Belgium",
        "https://www.impots.gouv.fr": "France", 
        "https://ksef.podatki.gov.pl": "Poland",
        "https://www.imda.gov.sg": "Singapore"
    }
    
    # Check if the URL starts with any of the base URLs
    for base_url, country in gov_base_urls.items():
        if url.startswith(base_url):
            print(f"🎯 Found matching gov.py base URL: {base_url} ({country})")
            return base_url
    
    print(f"❌ No matching gov.py base URL found for: {url}")
    return None

def get_country_from_url(url: str) -> str:
    """
    Get the country name from a government URL
    Returns the country name or 'Unknown'
    """
    gov_base_urls = {
        "https://einvoice.belgium.be": "Belgium",
        "https://www.impots.gouv.fr": "France", 
        "https://ksef.podatki.gov.pl": "Poland",
        "https://www.imda.gov.sg": "Singapore"
    }
    
    for base_url, country in gov_base_urls.items():
        if url.startswith(base_url):
            return country
    
    return "Unknown"

def collect_links_to_xml(base_url: str):
    """Collect links for a base_url using specialized government scrapers via gov_backend collector, return (xml_path, count)."""
    try:
        print(f"🔄 Starting government collection for: {base_url}")
        
        # First, check if this URL matches any base URLs in gov.py
        matching_base_url = check_gov_py_base_urls(base_url)
        
        if matching_base_url:
            print(f"✅ URL matches gov.py base URL: {matching_base_url}")
            print(f"🎯 Using specialized gov.py scraper for this URL")
            
            # Try to use the specialized government backend collector first
            try:
                # Import the government backend collector
                import sys
                import os
                gov_backend_path = os.path.join(os.path.dirname(__file__), 'scrapy', 'code ', 'gov_backend')
                sys.path.append(gov_backend_path)
                
                from collector import collect_links_to_xml as gov_collect_links
                
                print(f"🔄 Redirecting to gov.py for specialized scraping...")
                xml_path, count = gov_collect_links(base_url)
                
                if xml_path and count > 0:
                    print(f"✅ Government Backend Collection completed: {count} URLs saved to {xml_path}")
                    return xml_path, count
                else:
                    print(f"⚠️ Government Backend Collector failed, falling back to generic collector")
                    
            except Exception as e:
                print(f"⚠️ Government Backend Collector not available: {e}")
                print(f"🔄 Falling back to generic collector")
        else:
            print(f"🌐 URL does not match any gov.py base URLs, using generic collector")
        
        # Fallback to generic collector for unknown government sites or if specialized collector fails
        print(f"🌐 Using generic collector for: {base_url}")
        collector = WebsiteCollector(output_dir="collections")
        collection_data = collector.collect_and_save(base_url, max_pages=300)
        
        if collection_data['total_urls'] > 0 and collection_data.get('files', {}).get('xml'):
            xml_path = collection_data['files']['xml']
            count = collection_data['total_urls']
            print(f"✅ Generic collection completed: {count} URLs saved to {xml_path}")
            return xml_path, count
        else:
            print(f"❌ Generic collection failed for: {base_url}")
            return None, 0
        
    except Exception as e:
        print(f"❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

def compare_and_find_updates(site_url: str, new_xml_path: str) -> list:
    """Compare new XML data with previous data and find new/updated URLs"""
    try:
        from urllib.parse import urlparse
        import xml.etree.ElementTree as ET
        
        domain = urlparse(site_url).netloc
        domain_clean = domain.replace('.', '_')
        
        # Find previous XML files for this domain
        collections_dir = "collections"
        if not os.path.exists(collections_dir):
            return []
        
        previous_files = []
        for filename in os.listdir(collections_dir):
            if (filename.startswith(domain_clean) and 
                filename.endswith('.xml') and 
                filename != os.path.basename(new_xml_path)):
                previous_files.append(os.path.join(collections_dir, filename))
        
        if not previous_files:
            print(f"📝 No previous data found for {domain}, marking all URLs as new")
            # Parse new XML and mark all URLs as new
            tree = ET.parse(new_xml_path)
            root = tree.getroot()
            new_urls = []
            for url_elem in root.findall('.//url'):
                loc_elem = url_elem.find('loc')
                if loc_elem is not None:
                    new_urls.append({
                        'domain': domain,
                        'new_url': loc_elem.text,
                        'discovered_at': datetime.now().isoformat(),
                        'comparison_file': new_xml_path
                    })
            return new_urls
        
        # Find the most recent previous file
        previous_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        previous_xml_path = previous_files[0]
        
        print(f"🔄 Comparing new data with previous: {os.path.basename(previous_xml_path)}")
        
        # Parse both XML files
        new_tree = ET.parse(new_xml_path)
        new_root = new_tree.getroot()
        
        previous_tree = ET.parse(previous_xml_path)
        previous_root = previous_tree.getroot()
        
        # Extract URLs from both files
        new_urls = set()
        for url_elem in new_root.findall('.//url'):
            loc_elem = url_elem.find('loc')
            if loc_elem is not None:
                new_urls.add(loc_elem.text)
        
        previous_urls = set()
        for url_elem in previous_root.findall('.//url'):
            loc_elem = url_elem.find('loc')
            if loc_elem is not None:
                previous_urls.add(loc_elem.text)
        
        # Find new URLs
        new_urls_only = new_urls - previous_urls
        
        print(f"📊 Comparison results for {domain}:")
        print(f"   Previous URLs: {len(previous_urls)}")
        print(f"   New URLs: {len(new_urls)}")
        print(f"   New URLs only: {len(new_urls_only)}")
        
        # Create update records
        updates = []
        for new_url in new_urls_only:
            updates.append({
                'domain': domain,
                'new_url': new_url,
                'discovered_at': datetime.now().isoformat(),
                'comparison_file': new_xml_path
            })
        
        return updates
        
    except Exception as e:
        print(f"❌ Error comparing data for {site_url}: {e}")
        return []

def store_updates_in_database(updates: list):
    """Store updates in the sitemap_updates table"""
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        
        for update in updates:
            cursor.execute('''
                INSERT INTO sitemap_updates (domain, new_url, discovered_at, comparison_file, is_read)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                update['domain'],
                update['new_url'],
                update['discovered_at'],
                update['comparison_file'],
                False
                    ))
        
        conn.commit()
        conn.close()
        print(f"💾 Stored {len(updates)} updates in database")
        
    except Exception as e:
        print(f"❌ Error storing updates in database: {e}")

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
    
    return redirect(url_for('tasks'))

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
    """Display government dashboard with existing government sites"""
    conn = sqlite3.connect('scraping_scheduler.db')
    cursor = conn.cursor()
    
    # First, ensure all sites have comparison_result set to "NOT CHECKED" if not already set
    cursor.execute('''
        UPDATE government_sites 
        SET comparison_result = "NOT CHECKED" 
        WHERE comparison_result IS NULL OR comparison_result = ""
    ''')
    
    cursor.execute('''
        SELECT id, url, schedule, created_at, last_check, status, comparison_result 
        FROM government_sites 
        ORDER BY created_at DESC
    ''')
    government_sites = cursor.fetchall()
    conn.commit()
    conn.close()
    
    # Format the timestamps
    formatted_sites = []
    for site in government_sites:
        try:
            # Format created_at using the same function as tasks page
            formatted_created = format_timestamp(site[3], 'date')
            
            # Format last_check using the same function as tasks page
            formatted_last_check = format_timestamp(site[4], 'datetime')
            
            # Handle comparison status based on comparison_result column
            comparison_result = site[6] if len(site) > 6 else "NOT CHECKED"
            
            if comparison_result == "NOT CHECKED" or comparison_result is None:
                status_display = '<span class="status-badge not-checked"><i class="fas fa-exclamation-triangle"></i> NOT CHECKED</span>'
            elif "new URLs found" in comparison_result:
                # Extract the number and show it
                import re
                match = re.search(r'(\d+) new URLs found', comparison_result)
                if match:
                    number = match.group(1)
                    status_display = f'<span class="status-badge checked"><i class="fas fa-plus-circle"></i> {number} NEW LINKS</span>'
                else:
                    status_display = '<span class="status-badge checked"><i class="fas fa-plus-circle"></i> NEW LINKS FOUND</span>'
            elif "No changes detected" in comparison_result:
                status_display = '<span class="status-badge checked"><i class="fas fa-check"></i> NO UPDATE</span>'
            else:
                status_display = '<span class="status-badge checked"><i class="fas fa-info-circle"></i> ' + comparison_result + '</span>'
            
            formatted_site = (site[0], site[1], site[2], formatted_created, formatted_last_check, status_display)
            formatted_sites.append(formatted_site)
        except:
            # If parsing fails, use the original data
            formatted_sites.append(site)
    
    return render_template('government_dashboard.html', government_sites=formatted_sites)

@app.route('/add_government_site', methods=['POST'])
def add_government_site():
    """Add a new government site to the government_sites table"""
    try:
        url = request.form.get('url')
        schedule = request.form.get('schedule')
        
        if not url or not schedule:
            flash('URL and schedule are required', 'error')
            return redirect(url_for('government_dashboard'))
        
        # Add to government_sites table (separate from scraping_tasks)
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO government_sites (url, schedule, created_at, status, comparison_result)
            VALUES (?, ?, ?, ?, ?)
        ''', (url, schedule, now_iso, 'active', 'NOT CHECKED'))
        site_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Start collection process in background thread
        def collect_website_data():
            try:
                print(f"🔄 Starting collection for new website: {url}")
                xml_path, url_count = collect_links_to_xml(url)
                
                if xml_path and url_count > 0:
                    print(f"✅ Collection completed for {url}: {url_count} URLs")
                    # Update last_check to indicate collection is complete
                    conn = sqlite3.connect('scraping_scheduler.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE government_sites 
                        SET last_check = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), site_id))
                    conn.commit()
                    conn.close()
                    print(f"📝 Site {url} added successfully with {url_count} URLs")
                else:
                    print(f"❌ Collection failed for {url}")
            except Exception as e:
                print(f"❌ Error in background collection for {url}: {e}")
        
        # Start collection in background
        collection_thread = threading.Thread(target=collect_website_data)
        collection_thread.daemon = True
        collection_thread.start()
        
        # Return JSON response instead of redirect to keep loading state
        return jsonify({
            'success': True,
            'message': 'Website added successfully! Collection process started in background.',
            'site_id': site_id
        })
        
    except Exception as e:
        flash(f'Error adding government site: {str(e)}', 'error')
        return redirect(url_for('government_dashboard'))

@app.route('/check_collection_status/<int:site_id>')
def check_collection_status(site_id):
    """Check the collection status for a specific site"""
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT url, last_check, status FROM government_sites WHERE id = ?
        ''', (site_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            url, last_check, status = result
            
            # If last_check is set, collection is complete
            if last_check:
                return jsonify({
                    'status': 'completed',
                    'last_check': last_check,
                    'message': 'Collection completed successfully'
                })
            
            # Check if collection files exist in collections directory
            import os
            from urllib.parse import urlparse
            
            domain = urlparse(url).netloc
            domain_clean = domain.replace('.', '_')
            
            collections_dir = "collections"
            if os.path.exists(collections_dir):
                # Look for XML files for this domain
                for filename in os.listdir(collections_dir):
                    if (filename.startswith(domain_clean) and 
                        filename.endswith('.xml')):
                        # Found collection file, mark as completed
                        conn = sqlite3.connect('scraping_scheduler.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE government_sites 
                            SET last_check = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), site_id))
                        conn.commit()
                        conn.close()
                        
                        return jsonify({
                            'status': 'completed',
                            'last_check': datetime.now().isoformat(),
                            'message': 'Collection completed successfully (detected by file)'
                        })
            
            # Still in progress
            return jsonify({
                'status': 'in_progress',
                'message': 'Collection in progress...'
            })
        else:
            return jsonify({
                'status': 'not_found',
                'message': 'Site not found'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking status: {str(e)}'
        })

@app.route('/delete_all_government_sites', methods=['GET'])
def delete_all_government_sites():
    """Delete all government sites from the government_sites table"""
    try:
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM government_sites')
        conn.commit()
        conn.close()
        
        flash('All government sites deleted successfully!', 'success')
        return redirect(url_for('government_dashboard'))
        
    except Exception as e:
        flash(f'Error deleting all government sites: {str(e)}', 'error')
        return redirect(url_for('government_dashboard'))

# Global status tracking for real-time updates
collection_status = {
    'current_site': None,
    'current_step': None,
    'progress': 0,
    'total_sites': 0,
    'completed_sites': 0,
    'is_running': False
}

@app.route('/run_all_government', methods=['POST'])
def run_all_government():
    """Collect links for all active government sites, compare with previous data, and update latest updates."""
    global collection_status
    
    try:
        # Reset status
        collection_status = {
            'current_site': None,
            'current_step': None,
            'progress': 0,
            'total_sites': 0,
            'completed_sites': 0,
            'is_running': True
        }
        
        # Import the new comparator
        from government_link_comparator import GovernmentLinkComparator
        
        # Initialize the comparator
        comparator = GovernmentLinkComparator()
        
        # Get all government sites
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM government_sites')
        sites = cursor.fetchall()
        conn.close()
        
        collection_status['total_sites'] = len(sites)
        
        # Process all sites with status updates
        results = []
        total_updates = 0
        
        for i, (site_url,) in enumerate(sites):
            collection_status['current_site'] = site_url
            collection_status['current_step'] = f"Processing site {i+1}/{len(sites)}"
            collection_status['progress'] = (i / len(sites)) * 100
            
            try:
                # Update status for collection
                collection_status['current_step'] = f"🔄 Redirecting to gov.py for {site_url}"
                
                # Process the site
                result = comparator.process_site(site_url)
                
                if result['success']:
                    # Get the site ID from database
                    conn = sqlite3.connect('scraping_scheduler.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM government_sites WHERE url = ?', (site_url,))
                    site_data = cursor.fetchone()
                    conn.close()
                    
                    site_id = site_data[0] if site_data else 0
                    updates_found = result.get('updates_found', 0)
                    total_updates += updates_found
                    
                    # Update database with comparison results
                    conn = sqlite3.connect('scraping_scheduler.db')
                    cursor = conn.cursor()
                    
                    if updates_found > 0:
                        comparison_result = f"{updates_found} new URLs found"
                    else:
                        comparison_result = "No changes detected"
                    
                    cursor.execute('''
                        UPDATE government_sites 
                        SET last_check = ?,
                            comparison_result = ?
                        WHERE url = ?
                    ''', (datetime.now().isoformat(), comparison_result, site_url))
                    
                    conn.commit()
                    conn.close()
                    

                    
                    results.append({
                        'id': site_id,
                        'url': site_url,
                        'ok': True,
                        'count': result.get('url_count', 0),
                        'xml': result.get('xml_path'),
                        'updates_found': updates_found
                    })
                else:
                    results.append({
                        'id': 0,
                        'url': site_url,
                        'ok': False,
                        'count': 0,
                        'xml': None,
                        'updates_found': 0
                    })
                
                collection_status['completed_sites'] = i + 1
                collection_status['progress'] = ((i + 1) / len(sites)) * 100
                
            except Exception as e:
                print(f"❌ Error processing site {site_url}: {e}")
                results.append({
                    'id': 0,
                    'url': site_url,
                    'ok': False,
                    'count': 0,
                    'xml': None,
                    'updates_found': 0
                })
        
        # Final status update
        collection_status['current_step'] = "Collection completed successfully!"
        collection_status['progress'] = 100
        collection_status['is_running'] = False
        
        # Send batch Teams notification summarizing all results
        try:
            from scrapy.core.teams_notifier import TeamsNotifier
            notifier = TeamsNotifier()
            
            # Prepare batch summary
            batch_results = []
            for result in results:
                if result['ok']:
                    country = get_country_from_url(result['url'])
                    batch_results.append({
                        'domain': result['url'],
                        'country': country,
                        'has_changes': result['updates_found'] > 0,
                        'updates_found': result['updates_found']
                    })
            
            # Send batch notification
            if batch_results:
                notifier.send_batch_summary(batch_results)
                print(f"📱 Batch Teams notification sent for {len(batch_results)} government sites")
                
                # Update workflow app last run time
                update_workflow_app_last_run('Microsoft Teams')
                
        except Exception as e:
            print(f"⚠️ Failed to send batch Teams notification: {e}")
        
        return jsonify({
            'success': True,
            'results': results,
            'total_updates': total_updates
        })
        
    except Exception as e:
        collection_status['is_running'] = False
        collection_status['current_step'] = f"Error: {str(e)}"
        print(f"❌ Error in run_all_government: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/collection_status')
def get_collection_status():
    """Get the current collection status for real-time updates"""
    global collection_status
    return jsonify(collection_status)



if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) 