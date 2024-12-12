#utils/date_helpers.py
from datetime import datetime, timedelta
import calendar

def get_month_date_range(year, month):
    """รับช่วงวันที่ของเดือนที่ระบุ"""
    start_date = datetime(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = datetime(year, month, last_day)
    return start_date, end_date

def get_thai_month_name(month):
    """แปลงเลขเดือนเป็นชื่อเดือนภาษาไทย"""
    thai_months = [
        'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
        'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
    ]
    return thai_months[month - 1]

def format_thai_date(date):
    """แปลงวันที่เป็นรูปแบบไทย"""
    thai_months = [
        'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
        'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'
    ]
    return f"{date.day} {thai_months[date.month - 1]} {date.year + 543}"