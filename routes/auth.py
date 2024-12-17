#routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ถ้าล็อกอินอยู่แล้วให้ไปหน้า dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember_me' in request.form

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            
            # ถ้ามีการเก็บหน้าที่ต้องการเข้าถึงก่อนล็อกอิน
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # ตรวจสอบข้อมูล
        error = None
        if not username or not email or not password:
            error = 'กรุณากรอกข้อมูลให้ครบถ้วน'
        elif password != password_confirm:
            error = 'รหัสผ่านไม่ตรงกัน'
        elif User.query.filter_by(username=username).first():
            error = 'ชื่อผู้ใช้นี้ถูกใช้งานแล้ว'
        elif User.query.filter_by(email=email).first():
            error = 'อีเมลนี้ถูกใช้งานแล้ว'
        elif len(password) < 8:
            error = 'รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร'

        if error:
            flash(error, 'error')
        else:
            # สร้างผู้ใช้ใหม่
            new_user = User(
                username=username,
                email=email,
                is_active=True
            )
            new_user.set_password(password)

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('ลงทะเบียนสำเร็จ กรุณาเข้าสู่ระบบ', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง', 'error')

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ออกจากระบบสำเร็จ', 'success')
    return redirect(url_for('auth.login'))

# Utility function for password reset (ถ้าต้องการเพิ่มในอนาคต)
def send_password_reset_email(user):
    """ส่งอีเมลรีเซ็ตรหัสผ่าน"""
    token = user.get_reset_password_token()
    # ส่งอีเมลพร้อม token
    pass

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
        flash('ระบบได้ส่งคำแนะนำในการรีเซ็ตรหัสผ่านไปยังอีเมลของคุณแล้ว', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        password = request.form.get('password')
        user.set_password(password)
        db.session.commit()
        flash('รหัสผ่านของคุณถูกเปลี่ยนแล้ว', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')

# Error handlers
@auth_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@auth_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# เพิ่มต่อจากโค้ดเดิม

@auth_bp.route('/facebook-login')
def facebook_login():
    flash('ระบบ Facebook Login อยู่ระหว่างการพัฒนา', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/google-login')
def google_login():
    flash('ระบบ Google Login อยู่ระหว่างการพัฒนา', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/line-login')
def line_login():
    flash('ระบบ Line Login อยู่ระหว่างการพัฒนา', 'info')
    return redirect(url_for('auth.login'))