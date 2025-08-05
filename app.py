from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime
import os

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

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if request.method == 'GET':
        conn = sqlite3.connect('scraping_scheduler.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM scraping_tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        conn.close()
        
        if task:
            return render_template('edit_task.html', task=task)
        else:
            flash('Task not found', 'error')
            return redirect(url_for('tasks'))
    
    elif request.method == 'POST':
        url = request.form.get('url')
        schedule = request.form.get('schedule')
        status = request.form.get('status')
        
        if not url or not schedule:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('edit_task', task_id=task_id))
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            conn = sqlite3.connect('scraping_scheduler.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scraping_tasks 
                SET url = ?, schedule = ?, status = ?
                WHERE id = ?
            ''', (url, schedule, status, task_id))
            conn.commit()
            conn.close()
            flash('Task updated successfully!', 'success')
        except Exception as e:
            flash('Error updating task. Please try again.', 'error')
        
        return redirect(url_for('tasks'))

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8080) 