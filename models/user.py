# models/user.py
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from . import db
from .transaction import Transaction

class User(UserMixin, db.Model):
    """โมเดลสำหรับผู้ใช้งานระบบ"""
    
    __tablename__ = 'users'
    
    # Primary columns
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(200))
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    profile_image = db.Column(db.String(200))
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    
    # Preferences
    notification_preferences = db.Column(db.JSON, default={
        'email_notifications': True,
        'transaction_alerts': True,
        'goal_reminders': True,
        'weekly_summary': True
    })
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', 
                                 back_populates='user',
                                 lazy='dynamic',
                                 cascade='all, delete-orphan')
                                 
    financial_goals = db.relationship('FinancialGoal', 
                                    back_populates='user',
                                    lazy='dynamic',
                                    cascade='all, delete-orphan')
    
    debts = db.relationship('Debt', backref=db.backref('user', lazy=True), lazy='dynamic', cascade='all, delete-orphan')
    
    # Hybrid properties
    @hybrid_property
    def full_name(self):
        """คืนค่าชื่อเต็มของผู้ใช้"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    # Password handling
    def set_password(self, password):
        """เข้ารหัสและบันทึกรหัสผ่าน"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """ตรวจสอบรหัสผ่าน"""
        return check_password_hash(self.password_hash, password)
    
    # Financial calculations
    def get_total_balance(self):
        """คำนวณยอดเงินคงเหลือทั้งหมด"""
        income = sum(t.amount for t in self.transactions.filter_by(type='income'))
        expense = sum(t.amount for t in self.transactions.filter_by(type='expense'))
        return income - expense
    
    def get_monthly_summary(self, year, month):
        """คำนวณสรุปรายรับ-รายจ่ายรายเดือน"""
        transactions = self.transactions.filter(
            db.extract('year', Transaction.date) == year,
            db.extract('month', Transaction.date) == month
        ).all()
        
        income = sum(t.amount for t in transactions if t.type == 'income')
        expense = sum(t.amount for t in transactions if t.type == 'expense')
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense,
            'transaction_count': len(transactions)
        }

    def get_category_summary(self, year, month):
        """คำนวณสรุปค่าใช้จ่ายแยกตามหมวดหมู่"""
        transactions = self.transactions.filter(
            db.extract('year', Transaction.date) == year,
            db.extract('month', Transaction.date) == month,
            Transaction.type == 'expense'
        ).all()
        
        categories = {}
        for transaction in transactions:
            categories[transaction.category] = categories.get(transaction.category, 0) + transaction.amount
                
        return categories
        
    def get_savings_progress(self):
        """คำนวณความคืบหน้าการออมเงิน"""
        active_goals = self.financial_goals.filter_by(status='in_progress')
        total_saved = sum(g.current_amount for g in active_goals)
        total_goals = sum(g.target_amount for g in active_goals)
        
        if total_goals == 0:
            return 0
            
        return (total_saved / total_goals) * 100

    def __repr__(self):
        return f'<User {self.username}>'