#models/category.py
from . import db
from datetime import datetime

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' หรือ 'expense'
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # ชื่อไอคอนหรือคลาส CSS
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Category {self.name}>'