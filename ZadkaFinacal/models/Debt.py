from . import db
from datetime import datetime

class Debt(db.Model):
    """โมเดลสำหรับการจัดการหนี้สิน"""
    
    __tablename__ = 'debts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Debt details
    type = db.Column(db.String(50), nullable=False)  # ประเภทหนี้ (เช่น บ้าน, รถ, บัตรเครดิต)
    amount = db.Column(db.Float, nullable=False)  # ยอดเงินกู้
    interest_rate = db.Column(db.Float, nullable=False)  # อัตราดอกเบี้ย
    term_months = db.Column(db.Integer, nullable=False)  # ระยะเวลา (เดือน)
    monthly_payment = db.Column(db.Float, nullable=False)  # ค่างวดต่อเดือน
    remaining_amount = db.Column(db.Float, nullable=False)  # ยอดคงเหลือ
    
    # Dates
    start_date = db.Column(db.DateTime, nullable=False)  # วันที่เริ่มต้น
    end_date = db.Column(db.DateTime, nullable=False)  # วันที่สิ้นสุด
    payment_date = db.Column(db.Integer, nullable=False)  # วันที่ชำระในแต่ละเดือน
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, overdue, completed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = db.relationship('DebtPayment', backref='debt', lazy='dynamic', cascade='all, delete-orphan')
    
    # Remove the user relationship from here since it's defined in User model

    def __repr__(self):
        return f'<Debt {self.type} {self.amount}>'

    @property
    def status_display(self):
        """แสดงสถานะเป็นภาษาไทย"""
        status_map = {
            'active': 'กำลังผ่อนชำระ',
            'overdue': 'ค้างชำระ',
            'completed': 'ชำระครบแล้ว'
        }
        return status_map.get(self.status, self.status)

    def calculate_monthly_interest(self):
        """คำนวณดอกเบี้ยต่อเดือน"""
        return (self.remaining_amount * self.interest_rate) / 100 / 12

    def is_overdue(self):
        """ตรวจสอบว่าเกินกำหนดชำระหรือไม่"""
        today = datetime.utcnow()
        return today.day > self.payment_date and not self.payments.filter(
            db.extract('month', DebtPayment.payment_date) == today.month,
            db.extract('year', DebtPayment.payment_date) == today.year
        ).first()

class DebtPayment(db.Model):
    """โมเดลสำหรับประวัติการชำระหนี้"""
    
    __tablename__ = 'debt_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    debt_id = db.Column(db.Integer, db.ForeignKey('debts.id', ondelete='CASCADE'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)  # จำนวนเงินที่ชำระ
    payment_date = db.Column(db.DateTime, nullable=False)  # วันที่ชำระ
    note = db.Column(db.String(200))  # บันทึกเพิ่มเติม
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DebtPayment {self.amount} on {self.payment_date}>'