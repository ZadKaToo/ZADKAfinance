# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from models import db, User

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('ชื่อผู้ใช้', validators=[DataRequired(message='กรุณากรอกชื่อผู้ใช้')])
    password = PasswordField('รหัสผ่าน', validators=[DataRequired(message='กรุณากรอกรหัสผ่าน')])
    remember_me = BooleanField('จดจำการเข้าสู่ระบบ')

class RegisterForm(FlaskForm):
    username = StringField('ชื่อผู้ใช้', validators=[
        DataRequired(message='กรุณากรอกชื่อผู้ใช้'),
        Length(min=3, max=80, message='ชื่อผู้ใช้ต้องมีความยาว 3-80 ตัวอักษร')
    ])
    email = EmailField('อีเมล', validators=[
        DataRequired(message='กรุณากรอกอีเมล'),
        Email(message='รูปแบบอีเมลไม่ถูกต้อง'),
        Length(max=120, message='อีเมลต้องไม่เกิน 120 ตัวอักษร')
    ])
    password = PasswordField('รหัสผ่าน', validators=[
        DataRequired(message='กรุณากรอกรหัสผ่าน'),
        Length(min=8, message='รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร'),
        EqualTo('password_confirm', message='รหัสผ่านไม่ตรงกัน')
    ])
    password_confirm = PasswordField('ยืนยันรหัสผ่าน')

class ResetPasswordRequestForm(FlaskForm):
    email = EmailField('อีเมล', validators=[
        DataRequired(message='กรุณากรอกอีเมล'),
        Email(message='รูปแบบอีเมลไม่ถูกต้อง')
    ])

class ResetPasswordForm(FlaskForm):
    password = PasswordField('รหัสผ่านใหม่', validators=[
        DataRequired(message='กรุณากรอกรหัสผ่าน'),
        Length(min=8, message='รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร')
    ])
    password_confirm = PasswordField('ยืนยันรหัสผ่านใหม่', validators=[
        DataRequired(message='กรุณายืนยันรหัสผ่าน'),
        EqualTo('password', message='รหัสผ่านไม่ตรงกัน')
    ])

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('ชื่อผู้ใช้นี้ถูกใช้งานแล้ว', 'error')
        elif User.query.filter_by(email=form.email.data).first():
            flash('อีเมลนี้ถูกใช้งานแล้ว', 'error')
        else:
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                is_active=True
            )
            new_user.set_password(form.password.data)

            try:
                db.session.add(new_user)
                db.session.commit()
                flash('ลงทะเบียนสำเร็จ กรุณาเข้าสู่ระบบ', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash('เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง', 'error')

    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ออกจากระบบสำเร็จ', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('dashboard.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('รหัสผ่านของคุณถูกเปลี่ยนแล้ว', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

# Social login routes
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

# Error handlers
@auth_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@auth_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500