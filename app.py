import os
import subprocess
import bcrypt
import pyotp
import qrcode
import io
import base64
from datetime import datetime
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template_string
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'replace_with_a_random_secret_key'

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'mysql-f55ad75-charlotteosei070-a506.h.aivencloud.com'),
    'user': os.environ.get('DB_USER', 'avnadmin'),
    'password': os.getenv('DB_PASSWORD'),  
    'database': os.environ.get('DB_NAME', 'defaultdb'),
    'port': 16380,
    'ssl_disabled': False
}
PEPPER = "school_mvp_pepper_2024"

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def log_action(user_id, action):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (user_id, action, ip_address) VALUES (%s, %s, %s)",
        (user_id, action, request.remote_addr)
    )
    conn.commit()
    cursor.close()
    conn.close()

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                return "Access Denied: You do not have permission to view this page.", 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def page_wrapper(content):
    sidebar_html = f"""
    <!-- Mobile Top Bar -->
    <div class="d-md-none bg-dark text-white p-3 d-flex justify-content-between align-items-center" style="border-bottom: 1px solid #1E293B;">
        <div class="d-flex align-items-center">
            <div class="bg-primary text-white rounded p-1 me-2 d-flex align-items-center justify-content-center" style="width: 30px; height: 30px;">
                <i class="fas fa-cube"></i>
            </div>
            <span class="fs-5 fw-bold" style="color: #38BDF8;">EduPilot</span>
        </div>
        <button class="btn btn-outline-light btn-sm" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileSidebar">
            <i class="fas fa-bars"></i>
        </button>
    </div>

    <!-- Sidebar (Offcanvas on mobile, fixed on desktop) -->
    <div class="offcanvas-md offcanvas-start sidebar d-flex flex-column p-3 text-white" tabindex="-1" id="mobileSidebar" style="width: 260px; min-height: 100vh; background-color: #0B1120; border-right: 1px solid #1E293B;">
        <div class="offcanvas-header d-md-none">
            <h5 class="offcanvas-title text-white">Menu</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas" data-bs-target="#mobileSidebar"></button>
        </div>
        
        <div class="offcanvas-body d-flex flex-column p-0">
            <a href="/dashboard" class="d-none d-md-flex align-items-center mb-4 text-white text-decoration-none">
                <div class="bg-primary text-white rounded p-2 me-2 d-flex align-items-center justify-content-center" style="width: 35px; height: 35px;">
                    <i class="fas fa-cube"></i>
                </div>
                <span class="fs-4 fw-bold" style="color: #38BDF8;">EduPilot</span>
            </a>
            
            <div class="input-group mb-4" style="background: #1E293B; border-radius: 8px; padding: 5px;">
                <span class="input-group-text bg-transparent border-0 text-light"><i class="fas fa-search"></i></span>
                <input type="text" class="form-control bg-transparent border-0 text-white shadow-none" placeholder="Search..." style="font-size: 0.85rem;">
            </div>

            <ul class="nav nav-pills flex-column mb-auto gap-1">
                <li class="nav-item">
                    <a href="/dashboard" class="nav-link text-light d-flex align-items-center {'active bg-primary text-white' if request.path == '/dashboard' else ''}" style="border-radius: 8px;">
                        <i class="fas fa-th-large me-3"></i> Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a href="/register" class="nav-link text-light d-flex align-items-center hover-light" style="border-radius: 8px;">
                        <i class="fas fa-user-graduate me-3"></i> Students
                    </a>
                </li>
                <li class="nav-item">
                    <a href="/admin/users" class="nav-link text-light d-flex align-items-center hover-light" style="border-radius: 8px;">
                        <i class="fas fa-chalkboard-teacher me-3"></i> Teachers
                    </a>
                </li>
                <li class="nav-item">
                    <a href="#" onclick="alert('Class Schedules module is under construction!')" class="nav-link text-light d-flex align-items-center hover-light" style="border-radius: 8px;">
                        <i class="fas fa-calendar-alt me-3"></i> Class Schedules
                    </a>
                </li>
                {f'''
                <li class="nav-item mt-3 mb-2 text-secondary text-uppercase" style="font-size: 0.7rem; letter-spacing: 1px;">Admin Controls</li>
                <li class="nav-item">
                    <a href="/admin/users" class="nav-link text-light d-flex align-items-center {'active bg-primary text-white' if request.path == '/admin/users' else ''}" style="border-radius: 8px;">
                        <i class="fas fa-users me-3"></i> User Management
                    </a>
                </li>
                <li class="nav-item">
                    <a href="/admin/backup" class="nav-link text-light d-flex align-items-center hover-light" style="border-radius: 8px;">
                        <i class="fas fa-database me-3"></i> Backup DB
                    </a>
                </li>
                <li class="nav-item">
                    <a href="/admin/restore" class="nav-link text-light d-flex align-items-center hover-light" style="border-radius: 8px;">
                        <i class="fas fa-undo me-3"></i> Restore DB
                    </a>
                </li>
                <li class="nav-item">
                    <a href="/security_vault" class="nav-link text-light d-flex align-items-center hover-light {'active bg-primary text-white' if request.path == '/security_vault' else ''}" style="border-radius: 8px;">
                        <i class="fas fa-key me-3"></i> Security Vault
                    </a>
                </li>
                ''' if session.get('role') == 'admin' else ''}
                <li class="nav-item">
                    <a href="/setup_2fa" class="nav-link text-light d-flex align-items-center hover-light" style="border-radius: 8px;">
                        <i class="fas fa-shield-alt me-3"></i> Setup 2FA
                    </a>
                </li>
            </ul>
            
            <hr style="border-color: #1E293B;">
            <div class="dropdown">
                <a href="#" class="d-flex align-items-center text-white text-decoration-none dropdown-toggle p-2 rounded" data-bs-toggle="dropdown" style="background: #1E293B;">
                    <img src="https://ui-avatars.com/api/?name={session.get('username', 'Guest')}&background=0ea5e9&color=fff" alt="mdo" width="32" height="32" class="rounded-circle me-2">
                    <div>
                        <strong class="d-block" style="font-size: 0.9rem;">{session.get('username', 'Guest')}</strong>
                        <span class="text-secondary" style="font-size: 0.75rem;">{session.get('role', '').capitalize()}</span>
                    </div>
                </a>
                <ul class="dropdown-menu dropdown-menu-dark text-small shadow" style="background-color: #0B1120;">
                    <li><a class="dropdown-item" href="/logout">Logout</a></li>
                </ul>
            </div>
        </div>
    </div>
    <style>
        body {{ background-color: #030712 !important; color: #F3F4F6; }}
        .hover-light:hover {{ color: #38BDF8 !important; background-color: #1E293B; }}
        .card-custom {{ background-color: #0F172A; border: 1px solid #1E293B; border-radius: 12px; color: #fff; }}
        .text-muted-custom {{ color: #94A3B8 !important; }}
        .nav-link {{ color: #CBD5E1; }}
        .nav-link:hover {{ color: #fff; }}
        
        @media (min-width: 768px) {{
            .sidebar {{ position: fixed !important; top: 0; left: 0; visibility: visible !important; transform: none !important; }}
            .main-content {{ margin-left: 260px; }}
        }}
        @media (max-width: 767px) {{
            .main-content {{ margin-left: 0; }}
        }}
    </style>
    """

    if not session.get('username'):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Innocent School Management System</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Montserrat', sans-serif; margin: 0; padding: 0; overflow-x: hidden; background-color: #f4f7fc; }}
                .login-container {{ height: 100vh; padding: 0; }}
                .left-panel {{ background: linear-gradient(135deg, #002B7F 0%, #0056b3 100%); position: relative; flex-direction: column; justify-content: space-between; padding: 40px; overflow: hidden; }}
                .left-panel::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.1) 0%, transparent 60%); pointer-events: none; }}
                .left-content {{ position: relative; z-index: 2; }}
                .brand-header {{ display: flex; flex-direction: column; color: white; }}
                .logo-shield {{ display: inline-flex; flex-direction: column; align-items: center; justify-content: center; background: #FFC000; color: #002B7F; width: 80px; height: 90px; border-radius: 0 0 40px 40px; font-weight: 800; margin-bottom: 15px; border: 3px solid white; }}
                .logo-shield i {{ font-size: 24px; }}
                .logo-shield span {{ font-size: 10px; letter-spacing: 1px; }}
                .system-title {{ font-weight: 800; font-size: 2.5rem; line-height: 1.1; margin: 0; text-transform: uppercase; }}
                .system-title span {{ font-size: 1.1rem; font-weight: 600; color: #FFC000; letter-spacing: 2px; }}
                .tagline {{ font-size: 1.1rem; font-weight: 600; margin-top: 10px; color: #e0e0e0; letter-spacing: 3px; }}
                .catchphrase h2 {{ font-size: 3.5rem; font-weight: 800; color: white; font-style: italic; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
                .catchphrase h2 span {{ color: #FFC000; }}
                .feature-bar {{ display: flex; justify-content: space-between; background: rgba(0, 20, 60, 0.8); border-radius: 20px; padding: 20px; position: relative; z-index: 2; border: 1px solid rgba(255, 192, 0, 0.3); }}
                .feature-item {{ text-align: center; color: white; flex: 1; border-right: 1px solid rgba(255,255,255,0.2); }}
                .feature-item:last-child {{ border-right: none; }}
                .feature-item i {{ font-size: 24px; color: #FFC000; margin-bottom: 10px; }}
                .feature-item p {{ font-size: 0.8rem; font-weight: 600; margin: 0; line-height: 1.2; }}
                .right-panel {{ background-color: #f4f7fc; background-image: radial-gradient(#d1d9e6 1px, transparent 1px); background-size: 20px 20px; }}
                .login-card {{ background: white; padding: 40px; border-radius: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 100%; max-width: 450px; border: 2px solid #e0e0e0; position: relative; border-top: 5px solid #002B7F; }}
                .login-icon-wrapper {{ position: absolute; top: -40px; left: 50%; transform: translateX(-50%); background: #002B7F; color: #FFC000; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 35px; border: 4px solid white; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
                .welcome-text {{ text-align: center; color: #002B7F; font-weight: 800; margin-top: 30px; margin-bottom: 5px; }}
                .sub-text {{ text-align: center; color: #666; font-size: 0.9rem; margin-bottom: 30px; }}
                .input-group-custom {{ position: relative; display: flex; align-items: center; background: #f8f9fa; border-radius: 50px; border: 1px solid #ced4da; overflow: hidden; transition: all 0.3s; }}
                .input-group-custom:focus-within {{ border-color: #002B7F; box-shadow: 0 0 0 0.2rem rgba(0, 43, 127, 0.15); }}
                .input-icon {{ padding: 0 15px 0 20px; color: #002B7F; font-size: 1.1rem; }}
                .input-group-custom .form-control {{ border: none; background: transparent; padding: 12px 10px; box-shadow: none; }}
                .toggle-password {{ padding: 0 20px; cursor: pointer; color: #666; }}
                .form-check-label {{ font-size: 0.85rem; color: #444; font-weight: 600; }}
                .forgot-link {{ font-size: 0.85rem; color: #002B7F; font-weight: 700; text-decoration: none; }}
                .btn-login {{ background: #002B7F; color: white; border-radius: 50px; padding: 12px; font-weight: 700; font-size: 1.1rem; border: none; transition: 0.3s; }}
                .btn-login:hover {{ background: #001f5c; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 43, 127, 0.3); }}
                .divider {{ text-align: center; margin: 20px 0; position: relative; }}
                .divider::before {{ content: ''; position: absolute; top: 50%; left: 0; width: 45%; height: 1px; background: #ddd; }}
                .divider::after {{ content: ''; position: absolute; top: 50%; right: 0; width: 45%; height: 1px; background: #ddd; }}
                .divider span {{ background: white; padding: 0 10px; color: #999; font-size: 0.85rem; font-weight: 600; }}
                .btn-create {{ background: white; color: #002B7F; border: 2px solid #002B7F; border-radius: 50px; padding: 10px; font-weight: 700; font-size: 1rem; transition: 0.3s; }}
                .btn-create:hover {{ background: #f8f9fa; color: #001f5c; }}
                @media (max-width: 991px) {{ .login-container {{ height: 100vh; display: flex; align-items: center; justify-content: center; }} .right-panel {{ height: 100vh; }} .login-card {{ padding: 30px 20px; margin: 20px; max-width: 400px; }} }}
            </style>
        </head>
        <body>
            <div class="container-fluid login-container">
                <div class="row w-100 h-100">
                    <div class="col-lg-7 d-none d-lg-flex left-panel">
                        <div class="left-content">
                            <div class="brand-header">
                                <div class="logo-shield"><i class="fas fa-graduation-cap"></i><span>INNOCENT</span></div>
                                <h1 class="system-title">INNOCENT<br><span>SCHOOL MANAGEMENT SYSTEM</span></h1>
                                <p class="tagline">Learn • Manage • Excel</p>
                            </div>
                            <div class="catchphrase mt-5">
                                <h2>Smart School.<br><span>Brighter Future.</span></h2>
                            </div>
                        </div>
                        <div class="feature-bar">
                            <div class="feature-item"><i class="fas fa-users"></i><p>Manage<br>Students</p></div>
                            <div class="feature-item"><i class="fas fa-chalkboard-teacher"></i><p>Track<br>Lecturers</p></div>
                            <div class="feature-item"><i class="fas fa-chart-line"></i><p>Monitor<br>Performance</p></div>
                            <div class="feature-item"><i class="fas fa-cogs"></i><p>Streamline<br>Administration</p></div>
                        </div>
                    </div>
                    <div class="col-lg-5 right-panel d-flex align-items-center justify-content-center">
                        <div class="login-card">
                            <div class="login-icon-wrapper"><i class="fas fa-graduation-cap"></i></div>
                            <h3 class="welcome-text">Welcome Back!</h3>
                            <p class="sub-text">Login to your account</p>
                            {content}
                        </div>
                    </div>
                </div>
            </div>
            <script>
                function togglePassword() {{
                    var passwordField = document.getElementById("passwordField");
                    var eyeIcon = document.getElementById("eyeIcon");
                    if (passwordField.type === "password") {{
                        passwordField.type = "text";
                        eyeIcon.classList.remove("fa-eye-slash");
                        eyeIcon.classList.add("fa-eye");
                    }} else {{
                        passwordField.type = "password";
                        eyeIcon.classList.remove("fa-eye");
                        eyeIcon.classList.add("fa-eye-slash");
                    }}
                }}
            </script>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EduPilot Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background-color: #030712; font-family: 'Inter', sans-serif; color: #F3F4F6; }}
            .main-content {{ padding: 20px; }}
            @media (min-width: 768px) {{
                .main-content {{ margin-left: 260px; }}
            }}
            .stat-card {{ background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 20px; }}
            .stat-icon {{ width: 45px; height: 45px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
            .control-panel {{ background: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 15px; height: 100%; }}
            .btn-dark-blue {{ background: #1E293B; color: #F3F4F6; border: 1px solid #334155; font-size: 0.8rem; padding: 5px 10px; border-radius: 6px; transition: 0.2s; }}
            .btn-dark-blue:hover {{ background: #334155; color: #fff; }}
            .alert-card {{ background: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
        </style>
    </head>
    <body>
        {sidebar_html}
        <div class="main-content">
            <nav class="navbar navbar-expand-lg mb-4" style="background: transparent;">
                <div class="container-fluid px-0 flex-wrap gap-2">
                    <div class="d-flex align-items-center gap-3">
                        {'<a href="/dashboard" class="btn btn-outline-light btn-sm"><i class="fas fa-arrow-left"></i> Back</a>' if request.path != '/dashboard' else ''}
                        <span class="navbar-brand text-white fw-bold mb-0 h1">Admin Dashboard</span>
                    </div>
                    <div class="d-flex gap-3 align-items-center flex-wrap">
                        <a href="/admin/backup" class="btn btn-dark-blue text-decoration-none"><i class="fas fa-file-export me-2"></i>Export Data</a>
                        <a href="/register" class="btn btn-primary text-decoration-none" style="background: #2563EB; border: none; border-radius: 6px;"><i class="fas fa-plus me-2"></i>Add Student</a>
                    </div>
                </div>
            </nav>
            
            {content}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    content = """
    <form method="POST" action="/login">
        <div class="mb-3 input-group-custom">
            <span class="input-icon"><i class="fas fa-user"></i></span>
            <input type="text" class="form-control" name="username" placeholder="Username" required>
        </div>
        <div class="mb-3 input-group-custom">
            <span class="input-icon"><i class="fas fa-lock"></i></span>
            <input type="password" class="form-control" name="password" id="passwordField" placeholder="Password" required>
            <span class="toggle-password" onclick="togglePassword()">
                <i class="fas fa-eye-slash" id="eyeIcon"></i>
            </span>
        </div>
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="remember" id="rememberMe">
                <label class="form-check-label" for="rememberMe">Remember Me</label>
            </div>
            <a href="#" class="forgot-link">Forgot Password?</a>
        </div>
        <button type="submit" class="btn btn-login w-100">
            <i class="fas fa-sign-in-alt me-2"></i> Login
        </button>
        <div class="divider"><span>OR</span></div>
        <a href="/register" class="btn btn-create w-100 text-decoration-none text-center">
            <i class="fas fa-user-plus me-2"></i> Create an Account
        </a>
    </form>
    """
    return page_wrapper(content)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'student')

        salt = bcrypt.gensalt()
        peppered = (password + PEPPER).encode('utf-8')
        password_hash = bcrypt.hashpw(peppered, salt)

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, role) VALUES (%s, %s, %s, %s)",
                (username, password_hash.decode(), salt.decode(), role)
            )
            conn.commit()
            return "<div class='text-center'><h4 class='text-success'>Registration Successful!</h4><a href='/dashboard' class='btn btn-primary mt-3'>Go to Dashboard</a></div>"
        except mysql.connector.Error as err:
            return f"<div class='text-center text-danger'>Registration failed: {err}</div>"
        finally:
            cursor.close()
            conn.close()

    content = """
    <h4 class="text-center mb-4 text-white">Create an Account</h4>
    <form method="POST">
        <div class="mb-3 text-white">
            <label class="form-label">Username</label>
            <input type="text" name="username" class="form-control" required>
        </div>
        <div class="mb-3 text-white">
            <label class="form-label">Password</label>
            <input type="password" name="password" class="form-control" required>
        </div>
        <div class="mb-3 text-white">
            <label class="form-label">Role</label>
            <select name="role" class="form-select">
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
                <option value="admin">Admin</option>
            </select>
        </div>
        <button type="submit" class="btn btn-primary w-100 mb-3">Register</button>
    </form>
    <p class="text-center mb-0 text-muted">Already have an account? <a href="/" class="text-decoration-none fw-bold text-primary">Login</a></p>
    """
    return page_wrapper(content)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND deleted_at IS NULL", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return "User does not exist or has been deleted. <a href='/'>Try again</a>"

    peppered = (password + PEPPER).encode('utf-8')
    if bcrypt.checkpw(peppered, user['password_hash'].encode('utf-8')):
        if user['totp_secret']:
            session['pending_2fa_user_id'] = user['id']
            session['pending_2fa_username'] = user['username']
            session['pending_2fa_role'] = user['role']
            return redirect(url_for('verify_2fa'))
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        log_action(user['id'], 'Login (no 2FA)')
        return redirect(url_for('dashboard'))
    else:
        return "Incorrect password. <a href='/'>Try again</a>"

@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'pending_2fa_user_id' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        otp = request.form['otp']
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT totp_secret FROM users WHERE id = %s", (session['pending_2fa_user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and user['totp_secret']:
            totp = pyotp.TOTP(user['totp_secret'])
            if totp.verify(otp):
                session['user_id'] = session.pop('pending_2fa_user_id')
                session['username'] = session.pop('pending_2fa_username')
                session['role'] = session.pop('pending_2fa_role')
                log_action(session['user_id'], 'Login (2FA verified)')
                return redirect(url_for('dashboard'))
            else:
                return "Verification code incorrect. <a href='/verify_2fa'>Try again</a>"

    content = """
    <h4 class="text-center mb-4 text-white">Two-Factor Authentication</h4>
    <p class="text-muted text-center">Enter the 6-digit code from your authenticator app.</p>
    <form method="POST">
        <div class="mb-3">
            <input type="text" name="otp" class="form-control text-center fs-3" maxlength="6" required>
        </div>
        <button type="submit" class="btn btn-primary w-100">Verify</button>
    </form>
    """
    return page_wrapper(content)

@app.route('/setup_2fa')
def setup_2fa():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=session['username'], issuer_name="SchoolMVP")

    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET totp_secret = %s WHERE id = %s", (secret, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    content = f"""
    <h4 class="text-center mb-4 text-white">Enable Two-Factor Authentication</h4>
    <div class="text-center mb-3">
        <img src="data:image/png;base64,{qr_b64}" alt="QR Code" class="img-fluid border p-2 rounded bg-white">
    </div>
    <p class="text-center text-muted">Scan this QR code with Google Authenticator. Or enter this secret manually:</p>
    <div class="alert alert-secondary text-center font-monospace text-dark">{secret}</div>
    <a href="/dashboard" class="btn btn-outline-light w-100">Return to Dashboard</a>
    """
    return page_wrapper(content)

@app.route('/security_vault')
@role_required('admin')
def security_vault():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, salt, password_hash FROM users WHERE deleted_at IS NULL")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    user_rows = "".join([f"""
        <tr>
            <td>{u['id']}</td>
            <td><strong>{u['username']}</strong></td>
            <td><code style="color: #38BDF8; word-break: break-all;">{u['salt']}</code></td>
            <td><small class="text-muted" style="word-break: break-all;">{u['password_hash'][:20]}...</small></td>
        </tr>
    """ for u in users])

    content = f"""
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card card-custom border-primary" style="border-width: 2px;">
                <div class="card-body">
                    <h4 class="card-title text-white"><i class="fas fa-shield-alt text-primary me-2"></i> Global Pepper (Hidden in Backend)</h4>
                    <p class="text-muted-custom">This is the app-level secret appended to every password before hashing. It is never stored in the database.</p>
                    <div class="alert alert-dark border-primary font-monospace fs-5 text-center" style="letter-spacing: 2px; word-break: break-all;">
                        {PEPPER}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="card card-custom">
        <div class="card-header border-0 bg-transparent">
            <h5 class="mb-0 text-white"><i class="fas fa-database text-info me-2"></i> Database Salts & Hashes</h5>
            <p class="text-muted-custom mb-0" style="font-size: 0.85rem;">Each user has a unique random salt. The final Bcrypt hash is shown truncated.</p>
        </div>
        <div class="card-body table-responsive">
            <table class="table table-dark table-hover" style="background: transparent;">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Unique Salt</th>
                        <th>Bcrypt Hash</th>
                    </tr>
                </thead>
                <tbody>
                    {user_rows}
                </tbody>
            </table>
        </div>
    </div>
    """
    return page_wrapper(content)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    role = session.get('role')
    
    if role == 'admin':
        content = f"""
        <div class="row mb-4 g-3">
            <div class="col-6 col-md-3">
                <div class="stat-card d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted-custom mb-1" style="font-size: 0.85rem;">Total Students</p>
                        <h3 class="mb-0 fw-bold">1,850</h3>
                        <small class="text-success" style="font-size: 0.75rem;">Present: 1,800</small>
                    </div>
                    <div class="stat-icon d-none d-sm-flex" style="background: rgba(37, 99, 235, 0.2); color: #3B82F6;">
                        <i class="fas fa-user-graduate"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted-custom mb-1" style="font-size: 0.85rem;">Total Teachers</p>
                        <h3 class="mb-0 fw-bold">125</h3>
                        <small class="text-warning" style="font-size: 0.75rem;">Present: 90</small>
                    </div>
                    <div class="stat-icon d-none d-sm-flex" style="background: rgba(245, 158, 11, 0.2); color: #F59E0B;">
                        <i class="fas fa-chalkboard-teacher"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted-custom mb-1" style="font-size: 0.85rem;">Total Classes</p>
                        <h3 class="mb-0 fw-bold">73</h3>
                    </div>
                    <div class="stat-icon d-none d-sm-flex" style="background: rgba(168, 85, 247, 0.2); color: #A855F7;">
                        <i class="fas fa-door-open"></i>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="stat-card d-flex justify-content-between align-items-center">
                    <div>
                        <p class="text-muted-custom mb-1" style="font-size: 0.85rem;">System Users</p>
                        <h3 class="mb-0 fw-bold">2,150</h3>
                        <small class="text-muted-custom d-none d-sm-block" style="font-size: 0.75rem;">Admins: 3 | Staff: 50</small>
                    </div>
                    <div class="stat-icon d-none d-sm-flex" style="background: rgba(16, 185, 129, 0.2); color: #10B981;">
                        <i class="fas fa-users-cog"></i>
                    </div>
                </div>
            </div>
        </div>

        <h6 class="mb-3 text-white">Master Control Panel</h6>
        <div class="row mb-4 g-3">
            <div class="col-6 col-md-4 col-lg-2">
                <div class="control-panel text-center">
                    <div class="stat-icon mx-auto mb-2" style="background: rgba(37, 99, 235, 0.2); color: #3B82F6;"><i class="fas fa-user-plus"></i></div>
                    <h6 style="font-size: 0.9rem;">Student Management</h6>
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="/register" class="btn btn-dark-blue w-100 text-decoration-none">Add New</a>
                        <a href="/admin/users" class="btn btn-dark-blue w-100 text-decoration-none">Edit Profile</a>
                        <a href="/admin/users" class="btn btn-dark-blue w-100 text-decoration-none text-danger">Delete</a>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="control-panel text-center">
                    <div class="stat-icon mx-auto mb-2" style="background: rgba(245, 158, 11, 0.2); color: #F59E0B;"><i class="fas fa-user-shield"></i></div>
                    <h6 style="font-size: 0.9rem;">User Roles</h6>
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="/register" class="btn btn-dark-blue w-100 text-decoration-none">Create</a>
                        <a href="/admin/users" class="btn btn-dark-blue w-100 text-decoration-none">Admin Access</a>
                        <a href="/admin/users" class="btn btn-dark-blue w-100 text-decoration-none">Teacher Access</a>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="control-panel text-center">
                    <div class="stat-icon mx-auto mb-2" style="background: rgba(168, 85, 247, 0.2); color: #A855F7;"><i class="fas fa-chalkboard"></i></div>
                    <h6 style="font-size: 0.9rem;">Teacher Management</h6>
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="#" onclick="alert('Assign Classes module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Assign Classes</a>
                        <a href="/admin/users" class="btn btn-dark-blue w-100 text-decoration-none">View</a>
                        <a href="/admin/users" class="btn btn-dark-blue w-100 text-decoration-none">Deactivate</a>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="control-panel text-center">
                    <div class="stat-icon mx-auto mb-2" style="background: rgba(16, 185, 129, 0.2); color: #10B981;"><i class="fas fa-school"></i></div>
                    <h6 style="font-size: 0.9rem;">Class & Section</h6>
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="#" onclick="alert('Assign Teacher module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Assign Teacher</a>
                        <a href="#" onclick="alert('Merge module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Merge</a>
                        <a href="#" onclick="alert('Change Section module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Change Section</a>
                    </div>
                </div>
            </div>
            <div class="col-6 col-md-4 col-lg-2">
                <div class="control-panel text-center">
                    <div class="stat-icon mx-auto mb-2" style="background: rgba(239, 68, 68, 0.2); color: #EF4444;"><i class="fas fa-book"></i></div>
                    <h6 style="font-size: 0.9rem;">Subject Management</h6>
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="#" onclick="alert('Add Subjects module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Add Subjects</a>
                        <a href="#" onclick="alert('Assign module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Assign</a>
                        <a href="#" onclick="alert('Syllabus module is coming soon!')" class="btn btn-dark-blue w-100 text-decoration-none">Syllabus</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="row g-3">
            <div class="col-12 col-lg-8">
                <div class="control-panel">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="mb-0">Attendance by Class</h6>
                        <a href="#" class="text-primary text-decoration-none" style="font-size: 0.85rem;">View Details</a>
                    </div>
                    <div style="height: 200px; background: repeating-linear-gradient(0deg, transparent, transparent 39px, #1E293B 40px); display: flex; align-items: flex-end; gap: 10px; padding: 10px;">
                        <div style="width: 12%; height: 40%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                        <div style="width: 12%; height: 70%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                        <div style="width: 12%; height: 50%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                        <div style="width: 12%; height: 90%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                        <div style="width: 12%; height: 60%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                        <div style="width: 12%; height: 30%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                        <div style="width: 12%; height: 80%; background: #3B82F6; border-radius: 4px 4px 0 0;"></div>
                    </div>
                </div>
            </div>
            <div class="col-12 col-lg-4">
                <div class="control-panel">
                    <h6 class="mb-3">System Alerts</h6>
                    <div class="alert-card">
                        <div class="d-flex align-items-center gap-3">
                            <i class="fas fa-exclamation-triangle text-danger fs-5"></i>
                            <div>
                                <h6 class="mb-0" style="font-size: 0.85rem;">155 Unpaid Fees</h6>
                                <small class="text-muted-custom" style="font-size: 0.75rem;">Due date passed</small>
                            </div>
                        </div>
                        <a href="/admin/users" class="btn btn-sm btn-danger text-decoration-none" style="font-size: 0.75rem;">Resolve</a>
                    </div>
                    <div class="alert-card">
                        <div class="d-flex align-items-center gap-3">
                            <i class="fas fa-user-slash text-warning fs-5"></i>
                            <div>
                                <h6 class="mb-0" style="font-size: 0.85rem;">Inactive Staff</h6>
                                <small class="text-muted-custom" style="font-size: 0.75rem;">4 accounts inactive</small>
                            </div>
                        </div>
                        <a href="/admin/users" class="btn btn-sm btn-warning text-dark text-decoration-none" style="font-size: 0.75rem;">Review</a>
                    </div>
                </div>
            </div>
        </div>
        """
    elif role == 'teacher':
        content = """
        <div class="alert alert-info shadow-sm" style="background: #0F172A; border: 1px solid #1E293B; color: #fff;">
            <h4 class="alert-heading"><i class="fas fa-chalkboard-teacher me-2 text-primary"></i> Welcome, Teacher!</h4>
            <p class="text-muted-custom">Use the sidebar to manage your courses and student grades.</p>
        </div>
        """
    else:
        content = """
        <div class="alert alert-success shadow-sm" style="background: #0F172A; border: 1px solid #1E293B; color: #fff;">
            <h4 class="alert-heading"><i class="fas fa-user-graduate me-2 text-success"></i> Welcome, Student!</h4>
            <p class="text-muted-custom">Use the sidebar to view your enrolled courses and grades.</p>
        </div>
        """

    return page_wrapper(content)

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role, deleted_at FROM users WHERE deleted_at IS NULL")
    users = cursor.fetchall()
    cursor.execute("SELECT id, username, role, deleted_at FROM users WHERE deleted_at IS NOT NULL")
    deleted_users = cursor.fetchall()
    cursor.close()
    conn.close()

    active_rows = "".join([f"<tr><td>{u['id']}</td><td>{u['username']}</td><td><span class='badge bg-secondary'>{u['role']}</span></td><td><a href='/admin/delete_user/{u['id']}' class='btn btn-sm btn-danger'>Delete</a></td></tr>" for u in users])
    deleted_rows = "".join([f"<tr><td>{u['id']}</td><td>{u['username']}</td><td><span class='badge bg-secondary'>{u['role']}</span></td><td>{u['deleted_at']}</td><td><a href='/admin/restore_user/{u['id']}' class='btn btn-sm btn-success'>Restore</a></td></tr>" for u in deleted_users])

    content = f"""
    <div class="card card-custom mb-4">
        <div class="card-header" style="border-bottom: 1px solid #1E293B;">Active Users</div>
        <div class="card-body table-responsive">
            <table class="table table-dark table-hover" style="background: transparent;">
                <thead>
                    <tr><th>ID</th><th>Username</th><th>Role</th><th>Action</th></tr>
                </thead>
                <tbody>{active_rows}</tbody>
            </table>
        </div>
    </div>
    
    <div class="card card-custom">
        <div class="card-header text-danger" style="border-bottom: 1px solid #1E293B;">Deleted Users (Recycle Bin)</div>
        <div class="card-body table-responsive">
            <table class="table table-dark table-hover" style="background: transparent;">
                <thead>
                    <tr><th>ID</th><th>Username</th><th>Role</th><th>Deleted At</th><th>Action</th></tr>
                </thead>
                <tbody>{deleted_rows if deleted_users else '<tr><td colspan="5" class="text-center text-muted">No deleted users.</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    return page_wrapper(content)

@app.route('/admin/delete_user/<int:user_id>')
@role_required('admin')
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET deleted_at = NOW() WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    log_action(session['user_id'], f'Soft deleted user ID {user_id}')
    return redirect(url_for('admin_users'))

@app.route('/admin/restore_user/<int:user_id>')
@role_required('admin')
def restore_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET deleted_at = NULL WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    log_action(session['user_id'], f'Restored user ID {user_id}')
    return redirect(url_for('admin_users'))

@app.route('/admin/backup')
@role_required('admin')
def backup_db():
    backup_dir = os.path.join(os.getcwd(), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"school_mvp_{timestamp}.sql")

    try:
        cmd = f'mysqldump -u root -pAdamptey@1 school_mvp > "{backup_file}"'
        subprocess.run(cmd, shell=True, check=True)
        log_action(session['user_id'], f'Database backup: {backup_file}')
        return f"<div class='alert alert-success'>Backup successful: {backup_file}<br><a href='/dashboard' class='btn btn-sm btn-outline-success mt-2'>Back to Dashboard</a></div>"
    except Exception as e:
        return f"<div class='alert alert-danger'>Backup failed: {e}. You can also use Workbench Data Export.<br><a href='/dashboard' class='btn btn-sm btn-outline-danger mt-2'>Back</a></div>"

@app.route('/admin/restore')
@role_required('admin')
def restore_db():
    backup_dir = os.path.join(os.getcwd(), 'backups')
    if not os.path.exists(backup_dir):
        return "<div class='alert alert-warning'>No backup directory.<br><a href='/dashboard'>Back</a></div>"
    files = [f for f in os.listdir(backup_dir) if f.endswith('.sql')]
    if not files:
        return "<div class='alert alert-warning'>No backup files.<br><a href='/dashboard'>Back</a></div>"
    latest = sorted(files)[-1]
    filepath = os.path.join(backup_dir, latest)

    try:
        cmd = f'mysql -u root -pAdamptey@1 school_mvp < "{filepath}"'
        subprocess.run(cmd, shell=True, check=True)
        log_action(session['user_id'], f'Database restored from {latest}')
        return f"<div class='alert alert-success'>Restore successful: {latest}<br><a href='/dashboard' class='btn btn-sm btn-outline-success mt-2'>Back to Dashboard</a></div>"
    except Exception as e:
        return f"<div class='alert alert-danger'>Restore failed: {e}. You can also use Workbench Data Import.<br><a href='/dashboard' class='btn btn-sm btn-outline-danger mt-2'>Back</a></div>"

@app.route('/logout')
def logout():
    log_action(session.get('user_id'), 'Logout')
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)