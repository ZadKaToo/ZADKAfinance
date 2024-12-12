# models/transaction.py
from datetime import datetime
from . import db

class Transaction(db.Model):
    """โมเดลสำหรับธุรกรรมทางการเงิน"""
    
    __tablename__ = 'transactions'
    
    # Primary columns
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                       nullable=False, index=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('financial_goals.id', ondelete='SET NULL'), 
                       nullable=True)
    
    # Transaction details
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    type = db.Column(db.String(20), nullable=False, index=True)  # 'income' หรือ 'expense'
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='transactions')
    goal = db.relationship('FinancialGoal', back_populates='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.type} {self.amount}>'

    @staticmethod
    def get_categories():
        """รายการหมวดหมู่ธุรกรรมทั้งหมด"""
        return {
            'income': [
                'เงินเดือน',
                'ค่าล่วงเวลา',
                'โบนัส',
                'รายได้เสริม',
                'เงินปันผล',
                'อื่นๆ'
            ],
            'expense': [
                'อาหาร/เครื่องดื่ม',
                'ที่พัก',
                'เดินทาง',
                'สาธารณูปโภค',
                'ช้อปปิ้ง',
                'ความบันเทิง',
                'สุขภาพ',
                'การศึกษา',
                'ประกัน',
                'อื่นๆ'
            ]
        }