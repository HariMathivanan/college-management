from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import hmac
import hashlib
import json
from decimal import Decimal
from config import db, get_razorpay_client, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, get_allocation_splits, auto_allocate_donation
from email_utils import send_registration_email, send_registration_sms

app = Flask(__name__)
# Read Flask secret key from environment to avoid embedding secrets in source
app.secret_key = os.getenv('FLASK_SECRET_KEY', '')

# ─── Decorators ───────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ('admin', 'staff'):
            flash('Admin or staff access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def alumni_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ('alumni', 'admin', 'staff'):
            flash('Alumni access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ('student', 'admin', 'staff'):
            flash('Student access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def job_poster_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ('alumni', 'admin', 'staff'):
            flash('Job posting access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated
def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ('staff', 'admin'):
            flash('Staff access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

# ─── Home / Portal Selection ──────────────────────────────────────────────────

@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':   return redirect(url_for('admin_dashboard'))
        if role == 'alumni':  return redirect(url_for('alumni_dashboard'))
        if role == 'student': return redirect(url_for('student_dashboard'))
        if role == 'staff':   return redirect(url_for('staff_dashboard')) 
    return render_template('home.html')

# ─── ADMIN LOGIN ──────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        with db() as (conn, cur):
            cur.execute("SELECT * FROM users WHERE email=%s AND role='admin'",
                        (request.form['email'],))
            user = cur.fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user_id': user['id'], 'name': user['name'], 'role': 'admin'})
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin_login.html')

# ─── ALUMNI LOGIN & REGISTER ──────────────────────────────────────────────────

@app.route('/alumni/login', methods=['GET', 'POST'])
def alumni_login():
    if request.method == 'POST':
        with db() as (conn, cur):
            cur.execute("SELECT * FROM users WHERE email=%s AND role='alumni'",
                        (request.form['email'],))
            user = cur.fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user_id': user['id'], 'name': user['name'], 'role': 'alumni'})
            return redirect(url_for('alumni_dashboard'))
        flash('Invalid alumni credentials.', 'danger')
    return render_template('alumni_login.html')

@app.route('/alumni/register', methods=['GET', 'POST'])
def alumni_register():
    if request.method == 'POST':
        data = request.form
        with db() as (conn, cur):
            cur.execute("SELECT id FROM users WHERE email=%s", (data['email'],))
            if cur.fetchone():
                flash('Email already registered.', 'danger')
                return redirect(url_for('alumni_register'))
            hashed = generate_password_hash(data['password'])
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,'alumni')",
                (data['name'], data['email'], hashed)
            )
            uid = cur.lastrowid
            cur.execute(
                """INSERT INTO alumni
                   (user_id, name, email, batch_year, department, phone, city, company, job_title)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (uid, data['name'], data['email'], data['batch_year'], data['department'],
                 data.get('phone', ''), data.get('city', ''),
                 data.get('company', ''), data.get('job_title', ''))
            )
        # Send welcome email
        send_registration_email(data['email'], data['name'], 'alumni')
        # Send welcome SMS if phone number is provided
        if data.get('phone'):
            send_registration_sms(data['phone'], data['name'], 'alumni')
        flash('Registration successful! A welcome email has been sent to your inbox. Please log in.', 'success')
        return redirect(url_for('alumni_login'))
    return render_template('alumni_register.html')

# ─── STAFF LOGIN & REGISTER ────────────────────────────────────────────────────
@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        with db() as (conn, cur):
            cur.execute("SELECT * FROM users WHERE email=%s AND role='staff'",
                        (request.form['email'],))
            user = cur.fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user_id': user['id'], 'name': user['name'], 'role': 'staff'})
            return redirect(url_for('staff_dashboard'))
        flash('Invalid staff credentials.', 'danger')
    return render_template('staff_login.html')

@app.route('/staff/register', methods=['GET', 'POST'])
def staff_register():
    if request.method == 'POST':
        data = request.form
        with db() as (conn, cur):
            cur.execute("SELECT id FROM users WHERE email=%s", (data['email'],))
            if cur.fetchone():
                flash('Email already registered.', 'danger')
                return redirect(url_for('staff_register'))
            hashed = generate_password_hash(data['password'])
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,'staff')",
                (data['name'], data['email'], hashed)
            )
            uid = cur.lastrowid
            cur.execute(
                """INSERT INTO staff
                   (user_id, name, email, department, phone, bio, linkedin)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (uid, data['name'], data['email'], data['department'],
                 data.get('phone', ''), data.get('bio', ''), data.get('linkedin', ''))
            )
        # Send welcome email
        send_registration_email(data['email'], data['name'], 'staff')
        # Send welcome SMS if phone number is provided
        if data.get('phone'):
            send_registration_sms(data['phone'], data['name'], 'staff')
        flash('Staff registration successful! A welcome email has been sent to your inbox. Please log in.', 'success')
        return redirect(url_for('staff_login'))
    return render_template('staff_register.html')

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM staff WHERE user_id=%s", (session['user_id'],))
        staff = cur.fetchone()
        cur.execute("SELECT COUNT(*) as c FROM alumni");   ta = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM events");   te = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM jobs");     tj = cur.fetchone()['c']
        cur.execute("SELECT IFNULL(SUM(amount),0) as total FROM donations")
        td = cur.fetchone()['total']
        cur.execute("SELECT * FROM events ORDER BY event_date DESC LIMIT 3")
        recent_events = cur.fetchall()
        cur.execute("SELECT * FROM jobs ORDER BY posted_date DESC LIMIT 3")
        recent_jobs = cur.fetchall()
    return render_template('staff_dashboard.html',
        total_alumni=ta, total_events=te, total_jobs=tj, total_donations=td,
        recent_events=recent_events, recent_jobs=recent_jobs,
        staff=staff)

@app.route('/staff/donation-allocations', methods=['GET', 'POST'])
@staff_required
def staff_donation_allocations():
    with db() as (conn, cur):
        if request.method == 'POST':
            donation_id = request.form.get('donation_id')
            student_id = request.form.get('student_id')
            amount = request.form.get('amount', '').strip()
            note = request.form.get('note', '').strip()
            if not donation_id or not student_id:
                flash('Select a donation and a student.', 'danger')
                return redirect(url_for('staff_donation_allocations'))
            if not amount or not amount.replace('.', '', 1).isdigit():
                flash('Enter a valid allocation amount.', 'danger')
                return redirect(url_for('staff_donation_allocations'))
            amount = float(amount)
            if amount <= 0:
                flash('Allocation amount must be greater than zero.', 'danger')
                return redirect(url_for('staff_donation_allocations'))

            cur.execute(
                "SELECT amount FROM donations WHERE id=%s", (donation_id,)
            )
            donation = cur.fetchone()
            if not donation:
                flash('Selected donation does not exist.', 'danger')
                return redirect(url_for('staff_donation_allocations'))

            cur.execute(
                "SELECT IFNULL(SUM(amount),0) AS allocated FROM donation_allocations WHERE donation_id=%s",
                (donation_id,)
            )
            allocated = cur.fetchone()['allocated']
            remaining = float(donation['amount']) - float(allocated)
            if amount > remaining:
                flash(f'Allocation exceeds remaining donation balance (₹{remaining:.2f}).', 'danger')
                return redirect(url_for('staff_donation_allocations'))

            cur.execute("SELECT user_id FROM students WHERE user_id=%s", (student_id,))
            if not cur.fetchone():
                flash('Selected student does not exist.', 'danger')
                return redirect(url_for('staff_donation_allocations'))

            cur.execute(
                "INSERT INTO donation_allocations (donation_id, student_id, allocated_by, amount, note) VALUES (%s,%s,%s,%s,%s)",
                (donation_id, student_id, session['user_id'], amount, note)
            )

            if amount == remaining:
                cur.execute(
                    "UPDATE donations SET donation_status='Distributed' WHERE id=%s",
                    (donation_id,)
                )
            else:
                cur.execute(
                    "UPDATE donations SET donation_status='Partially Distributed' WHERE id=%s",
                    (donation_id,)
                )

            flash('Donation amount allocated to student successfully.', 'success')
            return redirect(url_for('staff_donation_allocations'))

        cur.execute(
            "SELECT d.id, d.name, d.email, d.amount, d.donation_status, d.created_at, "
            "IFNULL(SUM(a.amount),0) AS allocated_amount "
            "FROM donations d "
            "LEFT JOIN donation_allocations a ON d.id=a.donation_id "
            "GROUP BY d.id, d.name, d.email, d.amount, d.donation_status, d.created_at "
            "ORDER BY d.created_at DESC"
        )
        donations = cur.fetchall()
        for d in donations:
            d['remaining'] = float(d['amount']) - float(d['allocated_amount'])

        cur.execute("SELECT user_id, name, email FROM students ORDER BY name")
        students = cur.fetchall()

        cur.execute(
            "SELECT a.*, s.name AS student_name, d.name AS donation_name, u.name AS allocated_by_name "
            "FROM donation_allocations a "
            "JOIN students s ON a.student_id=s.user_id "
            "JOIN donations d ON a.donation_id=d.id "
            "LEFT JOIN users u ON a.allocated_by=u.id "
            "ORDER BY a.allocated_at DESC"
        )
        allocations = cur.fetchall()

    return render_template('staff_allocations.html', donations=donations, students=students, allocations=allocations)


@app.route('/staff/donation-split', methods=['GET', 'POST'])
@staff_required
def staff_donation_split():
    selected_donation = request.values.get('donation_id')
    with db() as (conn, cur):
        if request.method == 'POST':
            donation_id = request.form.get('donation_id')
            student_ids = request.form.getlist('student_id')
            amounts = request.form.getlist('amount')
            notes = request.form.getlist('note_row')

            if not donation_id:
                flash('Select a donation to split.', 'danger')
                return redirect(url_for('staff_donation_split'))

            # Normalize lists
            pairs = []
            for i in range(len(student_ids)):
                sid = student_ids[i].strip()
                amt = amounts[i].strip() if i < len(amounts) else ''
                note = notes[i].strip() if i < len(notes) else ''
                if not sid or not amt:
                    continue
                if not amt.replace('.', '', 1).isdigit():
                    flash('Enter valid numeric amounts for all rows.', 'danger')
                    return redirect(url_for('staff_donation_split'))
                amt_f = float(amt)
                if amt_f <= 0:
                    flash('Allocation amounts must be greater than zero.', 'danger')
                    return redirect(url_for('staff_donation_split'))
                pairs.append((sid, amt_f, note))

            if not pairs:
                flash('Add at least one valid allocation row.', 'danger')
                return redirect(url_for('staff_donation_split'))

            cur.execute("SELECT amount FROM donations WHERE id=%s", (donation_id,))
            donation = cur.fetchone()
            if not donation:
                flash('Donation not found.', 'danger')
                return redirect(url_for('staff_donation_split'))

            cur.execute(
                "SELECT IFNULL(SUM(amount),0) AS allocated FROM donation_allocations WHERE donation_id=%s",
                (donation_id,)
            )
            allocated = cur.fetchone()['allocated']
            remaining = float(donation['amount']) - float(allocated)

            total_to_allocate = sum(p[1] for p in pairs)
            if total_to_allocate > remaining:
                flash(f'Total allocation (₹{total_to_allocate:.2f}) exceeds remaining donation (₹{remaining:.2f}).', 'danger')
                return redirect(url_for('staff_donation_split'))

            # Insert allocations
            for sid, amt_f, note in pairs:
                cur.execute("SELECT user_id FROM students WHERE user_id=%s", (sid,))
                if not cur.fetchone():
                    flash('One of the selected students does not exist.', 'danger')
                    return redirect(url_for('staff_donation_split'))
                cur.execute(
                    "INSERT INTO donation_allocations (donation_id, student_id, allocated_by, amount, note) VALUES (%s,%s,%s,%s,%s)",
                    (donation_id, sid, session['user_id'], amt_f, note)
                )

            # Update donation status
            if total_to_allocate == remaining:
                cur.execute("UPDATE donations SET donation_status='Distributed' WHERE id=%s", (donation_id,))
            else:
                cur.execute("UPDATE donations SET donation_status='Partially Distributed' WHERE id=%s", (donation_id,))

            flash('Donation split and allocated successfully.', 'success')
            return redirect(url_for('staff_donation_allocations'))

        # GET: show available donations and students
        cur.execute(
            "SELECT d.id, d.name, d.email, d.amount, d.donation_status, d.created_at, "
            "IFNULL(SUM(a.amount),0) AS allocated_amount "
            "FROM donations d "
            "LEFT JOIN donation_allocations a ON d.id=a.donation_id "
            "GROUP BY d.id, d.name, d.email, d.amount, d.donation_status, d.created_at "
            "ORDER BY d.created_at DESC"
        )
        donations = cur.fetchall()
        for d in donations:
            d['remaining'] = float(d['amount']) - float(d['allocated_amount'])

        cur.execute("SELECT user_id, name, email FROM students ORDER BY name")
        students = cur.fetchall()

    return render_template('staff_split_donation.html', donations=donations, students=students, selected_donation=selected_donation)


# ─── STUDENT LOGIN & REGISTER ─────────────────────────────────────────────────

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        with db() as (conn, cur):
            cur.execute("SELECT * FROM users WHERE email=%s AND role='student'",
                        (request.form['email'],))
            user = cur.fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session.update({'user_id': user['id'], 'name': user['name'], 'role': 'student'})
            return redirect(url_for('student_dashboard'))
        flash('Invalid student credentials.', 'danger')
    return render_template('student_login.html')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        data = request.form
        with db() as (conn, cur):
            cur.execute("SELECT id FROM users WHERE email=%s", (data['email'],))
            if cur.fetchone():
                flash('Email already registered.', 'danger')
                return redirect(url_for('student_register'))
            hashed = generate_password_hash(data['password'])
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,'student')",
                (data['name'], data['email'], hashed)
            )
            uid = cur.lastrowid
            cur.execute(
                """INSERT INTO students
                   (user_id, name, email, enrollment_year, department, phone, roll_number)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (uid, data['name'], data['email'], data['enrollment_year'], data['department'],
                 data.get('phone', ''), data.get('roll_number', ''))
            )
        # Send welcome email
        send_registration_email(data['email'], data['name'], 'student')
        # Send welcome SMS if phone number is provided
        if data.get('phone'):
            send_registration_sms(data['phone'], data['name'], 'student')
        flash('Student registration successful! A welcome email has been sent to your inbox. Please log in.', 'success')
        return redirect(url_for('student_login'))
    return render_template('student_register.html')

@app.route('/logout')
def logout():
    role = session.get('role', '')
    session.clear()
    if role == 'admin':   return redirect(url_for('admin_login'))
    if role == 'student': return redirect(url_for('student_login'))
    if role == 'staff': return redirect(url_for('staff_login'))
    return redirect(url_for('alumni_login'))

# ─── ADMIN DASHBOARD ──────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    with db() as (conn, cur):
        cur.execute("SELECT COUNT(*) as c FROM alumni");   ta = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM students"); ts = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM events");   te = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM jobs");     tj = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM news");     tn = cur.fetchone()['c']
        cur.execute("SELECT IFNULL(SUM(amount),0) as total FROM donations")
        td = cur.fetchone()['total']
        cur.execute("SELECT * FROM events ORDER BY event_date DESC LIMIT 4")
        recent_events = cur.fetchall()
        cur.execute("SELECT * FROM jobs ORDER BY posted_date DESC LIMIT 4")
        recent_jobs = cur.fetchall()
    return render_template('admin_dashboard.html',
        total_alumni=ta, total_students=ts, total_events=te,
        total_jobs=tj, total_news=tn, total_donations=td,
        recent_events=recent_events, recent_jobs=recent_jobs)

@app.route('/admin/users')
@admin_required
def admin_users():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM users ORDER BY role, name")
        users = cur.fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/delete/<int:uid>')
@admin_required
def delete_user(uid):
    if uid == session['user_id']:
        flash("Can't delete yourself.", 'danger')
        return redirect(url_for('admin_users'))
    with db() as (conn, cur):
        cur.execute("DELETE FROM alumni   WHERE user_id=%s", (uid,))
        cur.execute("DELETE FROM students WHERE user_id=%s", (uid,))
        cur.execute("DELETE FROM users    WHERE id=%s",      (uid,))
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/students')
@admin_required
def admin_students():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM students ORDER BY name")
        students = cur.fetchall()
    return render_template('admin_students.html', students=students)

# ─── ALUMNI DASHBOARD ─────────────────────────────────────────────────────────

@app.route('/alumni/dashboard')
@alumni_required
def alumni_dashboard():
    with db() as (conn, cur):
        cur.execute("SELECT COUNT(*) as c FROM alumni"); ta = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM events"); te = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM jobs");   tj = cur.fetchone()['c']
        cur.execute("SELECT IFNULL(SUM(amount),0) as total FROM donations")
        td = cur.fetchone()['total']
        cur.execute("SELECT * FROM events ORDER BY event_date DESC LIMIT 3")
        recent_events = cur.fetchall()
        cur.execute("SELECT * FROM jobs ORDER BY posted_date DESC LIMIT 3")
        recent_jobs = cur.fetchall()
    return render_template('alumni_dashboard.html',
        total_alumni=ta, total_events=te, total_jobs=tj, total_donations=td,
        recent_events=recent_events, recent_jobs=recent_jobs)

@app.route('/alumni/donate', methods=['GET', 'POST'])
@alumni_required
def alumni_donate():
    if request.method == 'POST':
        amount = request.form.get('amount', '').strip()
        donation_type = request.form.get('donation_type', '').strip()
        payment_method = request.form.get('payment_method', '').strip()
        phone = request.form.get('phone', '').strip()
        note = request.form.get('note', '').strip()
        
        if not amount or not amount.replace('.', '', 1).isdigit():
            flash('Please enter a valid donation amount.', 'danger')
            return redirect(url_for('alumni_donate'))
        if not payment_method:
            flash('Please select a payment method.', 'danger')
            return redirect(url_for('alumni_donate'))
        
        amount_float = float(amount)
        if amount_float <= 0:
            flash('Donation amount must be greater than zero.', 'danger')
            return redirect(url_for('alumni_donate'))
        
        # For Razorpay, amount must be in paise (smallest unit)
        amount_paise = int(amount_float * 100)
        
        with db() as (conn, cur):
            cur.execute("SELECT name, email FROM users WHERE id=%s", (session['user_id'],))
            user = cur.fetchone()
            
            try:
                # Create Razorpay order using new function
                razorpay_client = get_razorpay_client()
                razorpay_order = razorpay_client.order.create({
                    'amount': amount_paise,
                    'currency': 'INR',
                    'payment_capture': 1,
                    'notes': {
                        'donation_type': donation_type,
                        'user_id': session['user_id']
                    }
                })
                
                # Save donation record with order ID
                cur.execute(
                    "INSERT INTO donations (user_id, name, email, amount, payment_method, donation_type, phone, note, donation_status, razorpay_order_id, payment_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (session['user_id'], user['name'], user['email'], amount,
                     payment_method, donation_type, phone, note, 'Pending', 
                     razorpay_order['id'], 'Pending')
                )
                
                # Get the inserted donation ID
                donation_id = cur.lastrowid
                
                # Auto-allocate donation based on type
                auto_allocate_donation(cur, donation_id, amount, donation_type)
                
                conn.commit()
                
                # Redirect to payment page
                return redirect(url_for('alumni_payment', order_id=razorpay_order['id']))
            
            except Exception as e:
                flash(f'Error creating payment: {str(e)}', 'danger')
                return redirect(url_for('alumni_donate'))
    
    return render_template('donate.html', razorpay_key=RAZORPAY_KEY_ID)


@app.route('/alumni/payment/<order_id>')
@alumni_required
def alumni_payment(order_id):
    """Display Razorpay payment form"""
    with db() as (conn, cur):
        cur.execute(
            "SELECT id, amount, name, email, phone, donation_type FROM donations WHERE razorpay_order_id=%s AND user_id=%s",
            (order_id, session['user_id'])
        )
        donation = cur.fetchone()
    
    if not donation:
        flash('Donation not found.', 'danger')
        return redirect(url_for('alumni_dashboard'))
    
    return render_template('payment.html', 
                         donation=donation, 
                         order_id=order_id,
                         razorpay_key=RAZORPAY_KEY_ID)


@app.route('/alumni/payment/verify', methods=['POST'])
@alumni_required
def verify_payment():
    """Verify Razorpay payment"""
    data = request.get_json()
    
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')
    
    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return jsonify({'status': 'error', 'message': 'Missing payment details'}), 400
    
    try:
        # Verify signature
        verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
        
        with db() as (conn, cur):
            # Update donation with payment details
            cur.execute(
                "UPDATE donations SET razorpay_payment_id=%s, razorpay_signature=%s, payment_status=%s, donation_status=%s WHERE razorpay_order_id=%s AND user_id=%s",
                (razorpay_payment_id, razorpay_signature, 'Success', 'Completed', razorpay_order_id, session['user_id'])
            )
            conn.commit()
        
        return jsonify({'status': 'success', 'message': 'Payment verified successfully'})
    
    except Exception as e:
        with db() as (conn, cur):
            cur.execute(
                "UPDATE donations SET payment_status=%s WHERE razorpay_order_id=%s",
                ('Failed', razorpay_order_id)
            )
            conn.commit()
        
        return jsonify({'status': 'error', 'message': f'Payment verification failed: {str(e)}'}), 400


@app.route('/alumni/payment/callback', methods=['POST'])
def payment_callback():
    """Razorpay webhook callback"""
    data = request.get_json()
    
    try:
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        
        # Verify the payment
        verify_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
        
        with db() as (conn, cur):
            cur.execute(
                "UPDATE donations SET payment_status=%s, donation_status=%s WHERE razorpay_order_id=%s",
                ('Success', 'Completed', razorpay_order_id)
            )
            conn.commit()
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


def verify_signature(order_id, payment_id, signature):
    """Verify Razorpay payment signature"""
    from config import RAZORPAY_KEY_SECRET
    
    message = f"{order_id}|{payment_id}"
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_signature:
        raise ValueError('Invalid payment signature')


@app.route('/alumni/payment-success/<order_id>')
@alumni_required
def payment_success(order_id):
    """Payment success page"""
    with db() as (conn, cur):
        cur.execute(
            "SELECT id, amount, name, donation_type FROM donations WHERE razorpay_order_id=%s AND user_id=%s AND payment_status=%s",
            (order_id, session['user_id'], 'Success')
        )
        donation = cur.fetchone()
    
    if not donation:
        flash('Payment not found or not successful.', 'danger')
        return redirect(url_for('alumni_dashboard'))
    
    return render_template('payment_success.html', donation=donation)


@app.route('/alumni/payment-failed/<order_id>')
@alumni_required
def payment_failed(order_id):
    """Payment failed page"""
    with db() as (conn, cur):
        cur.execute(
            "SELECT id, amount, name, donation_type FROM donations WHERE razorpay_order_id=%s AND user_id=%s",
            (order_id, session['user_id'])
        )
        donation = cur.fetchone()
    
    if not donation:
        flash('Donation record not found.', 'danger')
        return redirect(url_for('alumni_dashboard'))
    
    return render_template('payment_failed.html', donation=donation)

@app.route('/alumni/donations')
@alumni_required
def alumni_donations():
    with db() as (conn, cur):
        cur.execute("SELECT IFNULL(SUM(amount),0) as total_given FROM donations WHERE user_id=%s", (session['user_id'],))
        total_given = cur.fetchone()['total_given']

        cur.execute("SELECT * FROM donations WHERE user_id=%s ORDER BY created_at DESC", (session['user_id'],))
        donations = cur.fetchall()
        # attach allocations info to each donation
        for d in donations:
            cur.execute(
                "SELECT a.amount, s.user_id FROM donation_allocations a JOIN students s ON a.student_id=s.user_id WHERE a.donation_id=%s",
                (d['id'],)
            )
            allocs = cur.fetchall()
            d['allocations'] = allocs
            d['beneficiary_count'] = len(allocs) if allocs else 0
    return render_template('alumni_donations.html', donations=donations, total_given=total_given)

@app.route('/donations')
@admin_required
def donations():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM donations ORDER BY created_at DESC")
        donors = cur.fetchall()
    return render_template('donations.html', donors=donors)

@app.route('/alumni/directory')
@login_required
def alumni_list():
    search = request.args.get('search', '')
    batch  = request.args.get('batch', '')
    dept   = request.args.get('dept', '')
    query  = "SELECT * FROM alumni WHERE 1=1"
    params = []
    if search:
        query  += " AND (name LIKE %s OR company LIKE %s OR city LIKE %s)"
        params += [f'%{search}%'] * 3
    if batch:
        query  += " AND batch_year=%s"; params.append(batch)
    if dept:
        query  += " AND department=%s"; params.append(dept)
    with db() as (conn, cur):
        cur.execute(query + " ORDER BY name", params)
        alumni = cur.fetchall()
        cur.execute("SELECT DISTINCT batch_year FROM alumni ORDER BY batch_year DESC")
        batches = [r['batch_year'] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT department FROM alumni ORDER BY department")
        depts = [r['department'] for r in cur.fetchall()]
    return render_template('alumni_list.html', alumni=alumni, batches=batches,
                           depts=depts, search=search, batch=batch, dept=dept)

@app.route('/alumni/<int:aid>')
@login_required
def alumni_detail(aid):
    with db() as (conn, cur):
        cur.execute("SELECT * FROM alumni WHERE id=%s", (aid,))
        alumnus = cur.fetchone()
    return render_template('alumni_detail.html', alumnus=alumnus)

@app.route('/alumni/profile', methods=['GET', 'POST'])
@alumni_required
def alumni_profile():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM alumni WHERE user_id=%s", (session['user_id'],))
        alumnus = cur.fetchone()
        if request.method == 'POST':
            d = request.form
            cur.execute(
                """UPDATE alumni SET phone=%s, city=%s, company=%s, job_title=%s,
                   bio=%s, linkedin=%s WHERE user_id=%s""",
                (d['phone'], d['city'], d['company'], d['job_title'],
                 d['bio'], d['linkedin'], session['user_id'])
            )
            flash('Profile updated!', 'success')
            return redirect(url_for('alumni_profile'))
    return render_template('alumni_profile.html', alumnus=alumnus)

# ─── STUDENT DASHBOARD ────────────────────────────────────────────────────────

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    with db() as (conn, cur):
        cur.execute("SELECT COUNT(*) as c FROM alumni"); ta = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM events"); te = cur.fetchone()['c']
        cur.execute("SELECT COUNT(*) as c FROM jobs");   tj = cur.fetchone()['c']
        cur.execute("SELECT * FROM events ORDER BY event_date DESC LIMIT 3")
        recent_events = cur.fetchall()
        cur.execute("SELECT * FROM jobs ORDER BY posted_date DESC LIMIT 3")
        recent_jobs = cur.fetchall()
    return render_template('student_dashboard.html',
        total_alumni=ta, total_events=te, total_jobs=tj,
        recent_events=recent_events, recent_jobs=recent_jobs)

@app.route('/student/profile', methods=['GET', 'POST'])
@student_required
def student_profile():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM students WHERE user_id=%s", (session['user_id'],))
        student = cur.fetchone()
        if request.method == 'POST':
            d = request.form
            cur.execute(
                "UPDATE students SET phone=%s, bio=%s, skills=%s, linkedin=%s WHERE user_id=%s",
                (d['phone'], d['bio'], d['skills'], d['linkedin'], session['user_id'])
            )
            flash('Profile updated!', 'success')
            return redirect(url_for('student_profile'))
    return render_template('student_profile.html', student=student)

@app.route('/student/allocations', methods=['GET','POST'])
@student_required
def student_allocations():
    with db() as (conn, cur):
        if request.method == 'POST':
            alloc_id = request.form.get('allocation_id')
            if not alloc_id:
                flash('Missing allocation id.', 'danger')
                return redirect(url_for('student_allocations'))
            cur.execute("SELECT * FROM donation_allocations WHERE id=%s AND student_id=%s", (alloc_id, session['user_id']))
            a = cur.fetchone()
            if not a:
                flash('Allocation not found.', 'danger')
                return redirect(url_for('student_allocations'))
            if a.get('claimed'):
                flash('This allocation has already been claimed.', 'warning')
                return redirect(url_for('student_allocations'))
            cur.execute("UPDATE donation_allocations SET claimed=1, claimed_at=CURRENT_TIMESTAMP WHERE id=%s", (alloc_id,))
            flash('Allocation marked as received. Thank you!', 'success')
            return redirect(url_for('student_allocations'))

        cur.execute(
            "SELECT a.*, d.name as donor_name, d.amount as donation_amount "
            "FROM donation_allocations a "
            "JOIN donations d ON a.donation_id=d.id "
            "WHERE a.student_id=%s "
            "ORDER BY a.allocated_at DESC",
            (session['user_id'],)
        )
        allocations = cur.fetchall()
    return render_template('student_allocations.html', allocations=allocations)

# ─── SHARED: Events, Jobs, News ───────────────────────────────────────────────

@app.route('/events')
@login_required
def events():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM events ORDER BY event_date DESC")
        all_events = cur.fetchall()
    return render_template('events.html', events=all_events)

@app.route('/events/add', methods=['GET', 'POST'])
@admin_required
def add_event():
    if request.method == 'POST':
        d = request.form
        with db() as (conn, cur):
            cur.execute(
                "INSERT INTO events (title, description, event_date, location, organizer) VALUES (%s,%s,%s,%s,%s)",
                (d['title'], d['description'], d['event_date'], d['location'], d['organizer'])
            )
        flash('Event added!', 'success')
        return redirect(url_for('events'))
    return render_template('add_event.html')

@app.route('/events/delete/<int:eid>')
@admin_required
def delete_event(eid):
    with db() as (conn, cur):
        cur.execute("DELETE FROM events WHERE id=%s", (eid,))
    flash('Event deleted.', 'success')
    return redirect(url_for('events'))

@app.route('/jobs')
@login_required
def jobs():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM jobs ORDER BY posted_date DESC")
        all_jobs = cur.fetchall()
    return render_template('jobs.html', jobs=all_jobs)

@app.route('/jobs/add', methods=['GET', 'POST'])
@job_poster_required
def add_job():
    if request.method == 'POST':
        d = request.form
        with db() as (conn, cur):
            cur.execute(
                "INSERT INTO jobs (title, company, location, description, contact_email, posted_by) VALUES (%s,%s,%s,%s,%s,%s)",
                (d['title'], d['company'], d['location'], d['description'],
                 d['contact_email'], session['user_id'])
            )
        flash('Job posted!', 'success')
        return redirect(url_for('jobs'))
    return render_template('add_job.html')

@app.route('/jobs/delete/<int:jid>')
@login_required
def delete_job(jid):
    with db() as (conn, cur):
        cur.execute("SELECT posted_by FROM jobs WHERE id=%s", (jid,))
        job = cur.fetchone()
        if job and (job['posted_by'] == session['user_id'] or session['role'] in ('admin', 'staff')):
            cur.execute("DELETE FROM jobs WHERE id=%s", (jid,))
            flash('Job removed.', 'success')
    return redirect(url_for('jobs'))

@app.route('/news')
@login_required
def news():
    with db() as (conn, cur):
        cur.execute("SELECT * FROM news ORDER BY created_at DESC")
        all_news = cur.fetchall()
    return render_template('news.html', news=all_news)

@app.route('/news/add', methods=['GET', 'POST'])
@admin_required
def add_news():
    if request.method == 'POST':
        d = request.form
        with db() as (conn, cur):
            cur.execute(
                "INSERT INTO news (title, content, author) VALUES (%s,%s,%s)",
                (d['title'], d['content'], session['name'])
            )
        flash('News published!', 'success')
        return redirect(url_for('news'))
    return render_template('add_news.html')

@app.route('/news/delete/<int:nid>')
@admin_required
def delete_news(nid):
    with db() as (conn, cur):
        cur.execute("DELETE FROM news WHERE id=%s", (nid,))
    flash('News deleted.', 'success')
    return redirect(url_for('news'))

if __name__ == '__main__':
    app.run(debug=True)
