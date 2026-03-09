from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tasksphere_secret_key_2026'

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL
                 )''')
    
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 task_title TEXT NOT NULL,
                 priority TEXT NOT NULL,
                 status TEXT DEFAULT 'pending',
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (id)
                 )''')
    
    # Profile table
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
                 user_id INTEGER PRIMARY KEY,
                 phone TEXT,
                 student_id TEXT,
                 department TEXT,
                 year TEXT,
                 college TEXT,
                 dob TEXT,
                 gender TEXT,
                 city TEXT,
                 skills TEXT,
                 linkedin TEXT,
                 github TEXT,
                 FOREIGN KEY (user_id) REFERENCES users (id)
                 )''')
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                     (name, email, generate_password_hash(password)))
            user_id = c.lastrowid
            conn.commit()
            
            # Create empty profile
            c.execute("INSERT INTO profile (user_id) VALUES (?)", (user_id,))
            conn.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'error')
        finally:
            conn.close()
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get stats
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
    total_tasks = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed_tasks = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'pending'", (user_id,))
    pending_tasks = c.fetchone()[0]
    
    # Get recent tasks
    c.execute("""SELECT task_title, priority, status, created_at 
                 FROM tasks WHERE user_id = ? 
                 ORDER BY created_at DESC LIMIT 5""", (user_id,))
    recent_tasks = c.fetchall()
    
    # Get progress percentage
    progress = 0
    if total_tasks > 0:
        progress = round((completed_tasks / total_tasks) * 100, 1)
    
    conn.close()
    
    current_time = datetime.now().strftime("%A, %B %d, %Y | %I:%M %p")
    
    return render_template('dashboard.html', 
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         pending_tasks=pending_tasks,
                         progress=progress,
                         recent_tasks=recent_tasks,
                         current_time=current_time,
                         user_name=session['user_name'])

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task_title = request.form['task_title']
    priority = request.form['priority']
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task_title, priority, status) VALUES (?, ?, ?, 'pending')",
              (user_id, task_title, priority))
    conn.commit()
    conn.close()
    
    flash('Task added successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks')
@login_required
def tasks():
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""SELECT id, task_title, priority, status 
                 FROM tasks WHERE user_id = ? ORDER BY id DESC""", (user_id,))
    tasks = c.fetchall()
    conn.close()
    
    return render_template('tasks.html', tasks=tasks)

@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = 'completed' WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        # Update profile
        profile_data = {
            'phone': request.form['phone'],
            'student_id': request.form['student_id'],
            'department': request.form['department'],
            'year': request.form['year'],
            'college': request.form['college'],
            'dob': request.form['dob'],
            'gender': request.form['gender'],
            'city': request.form['city'],
            'skills': request.form['skills'],
            'linkedin': request.form['linkedin'],
            'github': request.form['github']
        }
        
        c.execute("""UPDATE profile SET 
                     phone=?, student_id=?, department=?, year=?, college=?,
                     dob=?, gender=?, city=?, skills=?, linkedin=?, github=?
                     WHERE user_id=?""",
                 (profile_data['phone'], profile_data['student_id'], profile_data['department'],
                  profile_data['year'], profile_data['college'], profile_data['dob'],
                  profile_data['gender'], profile_data['city'], profile_data['skills'],
                  profile_data['linkedin'], profile_data['github'], user_id))
        conn.commit()
        flash('Profile updated successfully!', 'success')
    
    # Get profile data
    c.execute("SELECT * FROM profile WHERE user_id = ?", (user_id,))
    profile_data = c.fetchone()
    conn.close()
    
    return render_template('profile.html', profile=profile_data)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
