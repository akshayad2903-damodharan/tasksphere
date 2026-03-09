from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'tasksphere_super_secure_key_2026_change_in_production'

# Database initialization
def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 task_title TEXT NOT NULL,
                 priority TEXT DEFAULT 'Medium',
                 status TEXT DEFAULT 'pending',
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                 )''')
    
    # Profile table
    c.execute('''CREATE TABLE IF NOT EXISTS profile (
                 user_id INTEGER PRIMARY KEY,
                 phone TEXT,
                 student_id TEXT,
                 department TEXT,
                 year_of_study TEXT,
                 college TEXT,
                 dob TEXT,
                 gender TEXT,
                 city TEXT,
                 skills TEXT,
                 linkedin TEXT,
                 github TEXT,
                 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                 )''')
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Home route
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, name, email, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('Please fill all fields.', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('signup.html')
        
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                     (name, email, generate_password_hash(password)))
            user_id = c.lastrowid
            
            # Create empty profile
            c.execute("""INSERT INTO profile (user_id) VALUES (?)""", (user_id,))
            conn.commit()
            conn.close()
            
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'error')
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('signup.html')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get statistics
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
    
    # Calculate progress
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

# Tasks route
@app.route('/tasks')
@login_required
def tasks():
    user_id = session['user_id']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("""SELECT id, task_title, priority, status, created_at 
                 FROM tasks WHERE user_id = ? ORDER BY id DESC""", (user_id,))
    tasks_list = c.fetchall()
    conn.close()
    
    current_time = datetime.now().strftime("%A, %B %d, %Y | %I:%M %p")
    return render_template('tasks.html', tasks=tasks_list, current_time=current_time)

# Add task route
@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task_title = request.form.get('task_title', '').strip()
    priority = request.form.get('priority', 'Medium')
    
    if not task_title:
        flash('Task title cannot be empty.', 'error')
        return redirect(url_for('tasks'))
    
    if len(task_title) > 200:
        flash('Task title too long.', 'error')
        return redirect(url_for('tasks'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task_title, priority) VALUES (?, ?, ?)",
              (session['user_id'], task_title, priority))
    conn.commit()
    conn.close()
    
    flash('Task added successfully!', 'success')
    return redirect(url_for('tasks'))

# Complete task route
@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET status = 'completed' WHERE id = ? AND user_id = ?",
              (task_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Task marked as completed!', 'success')
    return redirect(url_for('tasks'))

# Delete task route
@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks'))

# Profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        try:
            phone = request.form.get('phone', '')
            student_id = request.form.get('student_id', '')
            department = request.form.get('department', '')
            year = request.form.get('year', '')
            college = request.form.get('college', '')
            dob = request.form.get('dob', '')
            gender = request.form.get('gender', '')
            city = request.form.get('city', '')
            skills = request.form.get('skills', '')
            linkedin = request.form.get('linkedin', '')
            github = request.form.get('github', '')
            
            c.execute("""INSERT OR REPLACE INTO profile 
                        (user_id, phone, student_id, department, year_of_study, college, 
                         dob, gender, city, skills, linkedin, github) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (user_id, phone, student_id, department, year, college, 
                      dob, gender, city, skills, linkedin, github))
            conn.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            flash('Error updating profile.', 'error')
    
    # Get profile data
    c.execute("SELECT * FROM profile WHERE user_id = ?", (user_id,))
    profile_data = c.fetchone()
    conn.close()
    
    return render_template('profile.html', profile=profile_data)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# 404 handler
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
