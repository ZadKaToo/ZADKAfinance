#utils/calculate.py
from datetime import datetime, timedelta
from calendar import monthrange

def calculate_daily_saving(target_amount, current_amount, target_date):
    """คำนวณจำนวนเงินที่ต้องออมต่อวัน"""
    days_remaining = (target_date - datetime.now()).days
    if days_remaining <= 0:
        return 0
    remaining_amount = target_amount - current_amount
    return remaining_amount / days_remaining if remaining_amount > 0 else 0

def calculate_monthly_saving(target_amount, current_amount, target_date):
    """คำนวณจำนวนเงินที่ต้องออมต่อเดือน"""
    today = datetime.now()
    months_remaining = (target_date.year - today.year) * 12 + target_date.month - today.month
    if months_remaining <= 0:
        return 0
    remaining_amount = target_amount - current_amount
    return remaining_amount / months_remaining if remaining_amount > 0 else 0

def calculate_financial_health_score(income, expense, savings, debt=0):
    """คำนวณคะแนนสุขภาพทางการเงิน (0-100)"""
    score = 0
    
    # อัตราส่วนค่าใช้จ่ายต่อรายได้ (30 คะแนน)
    expense_ratio = expense / income if income > 0 else 1
    if expense_ratio <= 0.5:
        score += 30
    elif expense_ratio <= 0.7:
        score += 20
    elif expense_ratio <= 0.9:
        score += 10
        
    # อัตราการออม (40 คะแนน)
    savings_ratio = savings / income if income > 0 else 0
    if savings_ratio >= 0.2:
        score += 40
    elif savings_ratio >= 0.1:
        score += 30
    elif savings_ratio >= 0.05:
        score += 20
    elif savings_ratio > 0:
        score += 10
        
    # ภาระหนี้ (30 คะแนน)
    debt_ratio = debt / income if income > 0 else 0
    if debt_ratio == 0:
        score += 30
    elif debt_ratio <= 0.3:
        score += 20
    elif debt_ratio <= 0.5:
        score += 10
        
    return score

def analyze_spending_pattern(transactions, period_days=30):
    """วิเคราะห์รูปแบบการใช้จ่าย"""
    # จัดกลุ่มธุรกรรมตามหมวดหมู่
    categories = {}
    total_expense = 0
    
    for transaction in transactions:
        if transaction.type == 'expense':
            if transaction.category not in categories:
                categories[transaction.category] = 0
            categories[transaction.category] += transaction.amount
            total_expense += transaction.amount
    
    # คำนวณสัดส่วนและแนวโน้ม
    insights = []
    for category, amount in categories.items():
        percentage = (amount / total_expense * 100) if total_expense > 0 else 0
        
        # วิเคราะห์และให้คำแนะนำ
        if percentage > 50:
            insights.append({
                'category': category,
                'message': f'ค่าใช้จ่ายใน {category} คิดเป็น {percentage:.1f}% ของค่าใช้จ่ายทั้งหมด ซึ่งค่อนข้างสูง',
                'type': 'warning'
            })
        elif percentage > 30:
            insights.append({
                'category': category,
                'message': f'ค่าใช้จ่ายใน {category} อยู่ในระดับที่ควรติดตาม',
                'type': 'info'
            })
    
    return insights