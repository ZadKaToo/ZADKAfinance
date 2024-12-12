# models/financialGoal.py
from datetime import datetime
from . import db

class FinancialGoal(db.Model):
    """โมเดลสำหรับเป้าหมายทางการเงิน"""
    
    __tablename__ = 'financial_goals'
    
    # Primary columns
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys - สร้างความสัมพันธ์กับตาราง users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                       nullable=False, index=True)
    
    # Goal details
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    target_date = db.Column(db.DateTime, nullable=False)
    
    # Goal metadata
    category = db.Column(db.String(50))  # เช่น 'ระยะสั้น', 'ระยะกลาง', 'ระยะยาว'
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed', 'cancelled'
    
    # Notification settings
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_frequency = db.Column(db.String(20), default='weekly')  # 'daily', 'weekly', 'monthly'
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Goal tracking history
    history = db.Column(db.JSON, default=[])  # เก็บประวัติการปรับปรุงเป้าหมาย
    
    # Relationships
    user = db.relationship('User', back_populates='financial_goals')
    transactions = db.relationship('Transaction', back_populates='goal', lazy='dynamic',
                                cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<FinancialGoal {self.name}>'
        
    def get_progress_percentage(self):
        """คำนวณความคืบหน้าเป็นเปอร์เซ็นต์"""
        if self.target_amount == 0:
            return 0
        return (self.current_amount / self.target_amount) * 100
        
    def get_remaining_amount(self):
        """คำนวณจำนวนเงินที่ต้องออมเพิ่ม"""
        return max(0, self.target_amount - self.current_amount)
        
    def get_daily_saving_needed(self):
        """คำนวณจำนวนเงินที่ต้องออมต่อวันเพื่อให้ถึงเป้าหมาย"""
        if self.status != 'in_progress':
            return 0
            
        remaining_days = (self.target_date - datetime.utcnow()).days
        if remaining_days <= 0:
            return 0
            
        return self.get_remaining_amount() / remaining_days
        
    def is_achievable(self):
        """ตรวจสอบความเป็นไปได้ในการบรรลุเป้าหมาย"""
        daily_saving = self.get_daily_saving_needed()
        return daily_saving <= (self.target_amount * 0.5)
        
    def add_to_history(self, amount, note=None):
        """เพิ่มประวัติการปรับปรุงเป้าหมาย"""
        if self.history is None:
            self.history = []
            
        self.history.append({
            'date': datetime.utcnow().isoformat(),
            'amount': amount,
            'note': note,
            'total': self.current_amount
        })