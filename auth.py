from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import connect_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            school_name = request.form.get('school_name')
            username = request.form.get('username')
            password = request.form.get('password')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            lecture_duration = request.form.get('lecture_duration')
            break_start_time = request.form.get('break_start')
            break_duration = request.form.get('break_duration')

            if not username or not password or not school_name:
                flash('Please fill required fields', 'error')
                return redirect(url_for('auth.register'))

            hashed_password = generate_password_hash(password)

            db = connect_db()
            cursor = db.cursor()
            
            # Check unique username
            cursor.execute("SELECT school_id FROM schools WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists', 'error')
                db.close()
                return redirect(url_for('auth.register'))

            sql = """
                INSERT INTO schools (school_name, username, password_hash, start_time, end_time, lecture_duration, break_start_time, break_duration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (school_name, username, hashed_password, start_time, end_time, lecture_duration, break_start_time, break_duration))
            db.commit()
            db.close()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = connect_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM schools WHERE username = %s", (username,))
        school = cursor.fetchone()
        db.close()

        if school and check_password_hash(school['password_hash'], password):
            session['school_id'] = school['school_id']
            session['school_name'] = school['school_name']
            
            # Store time config in session for easy access
            session['time_config'] = {
                'start_time': school['start_time'],
                'end_time': school['end_time'],
                'lecture_duration': school['lecture_duration'],
                'break_start': school['break_start_time'],
                'break_duration': school['break_duration']
            }
            
            return redirect(url_for('main.dashboard')) # Assuming dashboard route exists
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth.login'))
