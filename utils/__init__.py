#utils/_init_.py
from datetime import datetime, timedelta

def format_currency(amount):
    """แปลงจำนวนเงินเป็นรูปแบบสกุลเงินบาท"""
    return f"฿{amount:,.2f}"

def format_percentage(value):
    """แปลงจำนวนเป็นเปอร์เซ็นต์"""
    return f"{value:.1f}%"