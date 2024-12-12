#utils/auth.py
import jwt
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

def generate_reset_token(user_id, expires_in=3600):
    """สร้าง token สำหรับรีเซ็ตรหัสผ่าน"""
    return jwt.encode(
        {
            'reset_password': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_reset_token(token):
    """ตรวจสอบ token สำหรับรีเซ็ตรหัสผ่าน"""
    try:
        data = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return data['reset_password']
    except:
        return None

def hash_password(password):
    """เข้ารหัสรหัสผ่าน"""
    return generate_password_hash(password)

def check_password(password_hash, password):
    """ตรวจสอบรหัสผ่าน"""
    return check_password_hash(password_hash, password)
