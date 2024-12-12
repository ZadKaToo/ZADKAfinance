# routes/dashboard.py
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from models import db, Transaction, FinancialGoal
import calendar

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_date_range(period='month'):
    """คำนวณช่วงวันที่ตามที่ต้องการ"""
    today = datetime.now()
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today.replace(day=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    elif period == 'all':
        return None, today
    else:
        start_date = today - timedelta(days=int(period))
    return start_date, today

def calculate_trends(transactions, period_days=30):
    """คำนวณแนวโน้มรายรับ-รายจ่าย"""
    today = datetime.now()
    start_date = today - timedelta(days=period_days)
    
    # จัดกลุ่มธุรกรรมตามวัน
    daily_totals = {}
    for transaction in transactions:
        date_key = transaction.date.strftime('%Y-%m-%d')
        if date_key not in daily_totals:
            daily_totals[date_key] = {'income': 0, 'expense': 0}
        if transaction.type == 'income':
            daily_totals[date_key]['income'] += transaction.amount
        else:
            daily_totals[date_key]['expense'] += transaction.amount

    return daily_totals

def calculate_category_distribution(transactions):
    """คำนวณสัดส่วนค่าใช้จ่ายตามหมวดหมู่"""
    categories = {}
    total_expense = 0

    for transaction in transactions:
        if transaction.type == 'expense':
            if transaction.category not in categories:
                categories[transaction.category] = 0
            categories[transaction.category] += transaction.amount
            total_expense += transaction.amount

        # คำนวณเป็นเปอร์เซ็นต์
    distribution = {}
    if total_expense > 0:
        for category, amount in categories.items():
            distribution[category] = round((amount / total_expense) * 100, 1)

    return distribution

@dashboard_bp.route('/')
@login_required
def index():
    period = request.args.get('period', 'month')
    start_date, end_date = get_date_range(period)

    # Get all transactions
    query = Transaction.query.filter_by(user_id=current_user.id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    transactions = query.filter(Transaction.date <= end_date).all()

    # Calculate totals with savings
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    regular_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    savings_amount = sum(t.amount for t in transactions if t.type == 'saving')
    total_expense = regular_expenses + savings_amount

    # Get goals data
    goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()
    goals_balance = sum(goal.current_amount for goal in goals)
    active_goals = [g for g in goals if g.status == 'in_progress']

    # Calculate balances
    available_balance = total_income - total_expense
    total_balance = available_balance + goals_balance

    # Base month comparison
    first_month = query.filter(Transaction.date < start_date).order_by(Transaction.date.asc()).first()
    if first_month:
        first_month_start = first_month.date.replace(day=1)
        first_month_end = (first_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        first_month_transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .filter(Transaction.date.between(first_month_start, first_month_end)).all()
        
        base_income = sum(t.amount for t in first_month_transactions if t.type == 'income')
        base_expense = sum(t.amount for t in first_month_transactions if t.type in ['expense', 'saving'])
        
        income_change = ((total_income - base_income) / base_income * 100) if base_income > 0 else 0
        expense_change = ((total_expense - base_expense) / base_expense * 100) if base_expense > 0 else 0
    else:
        income_change = expense_change = 0

    # Prepare trend data
    trend_data = {'labels': [], 'income': [], 'expense': [], 'savings': []}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        day_transactions = [t for t in transactions if t.date.strftime('%Y-%m-%d') == date_str]
        
        trend_data['labels'].append(current_date.strftime('%d %b'))
        trend_data['income'].append(sum(t.amount for t in day_transactions if t.type == 'income'))
        trend_data['expense'].append(sum(t.amount for t in day_transactions if t.type == 'expense'))
        trend_data['savings'].append(sum(t.amount for t in day_transactions if t.type == 'saving'))
        
        current_date += timedelta(days=1)

    # Category distribution
    category_data = {'labels': [], 'amounts': []}
    category_totals = {}
    for t in transactions:
        if t.type == 'expense':
            category_totals[t.category] = category_totals.get(t.category, 0) + t.amount
    
    for category, amount in category_totals.items():
        category_data['labels'].append(category)
        category_data['amounts'].append(amount)

    return render_template('dashboard/index.html',
        transactions=transactions[:5],
        total_income=total_income,
        total_expense=regular_expenses,
        total_savings=savings_amount,
        balance=available_balance,
        total_balance=total_balance,
        goals_balance=goals_balance,
        income_change=income_change,
        expense_change=expense_change,
        trend_data=trend_data,
        category_data=category_data,
        financial_goals=active_goals,
        today=datetime.now()
    )
    
    
@dashboard_bp.route('/overview')
@login_required
def overview():
    # รับพารามิเตอร์จาก URL
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))

    # สร้างช่วงวันที่สำหรับเดือนที่เลือก
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])

    # ดึงธุรกรรมทั้งหมดในเดือนที่เลือก
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .filter(Transaction.date >= start_date)\
        .filter(Transaction.date <= end_date)\
        .order_by(Transaction.date.desc())\
        .all()

    # คำนวณสรุปรายเดือน
    monthly_summary = {
        'income': sum(t.amount for t in transactions if t.type == 'income'),
        'expense': sum(t.amount for t in transactions if t.type == 'expense'),
    }
    monthly_summary['balance'] = monthly_summary['income'] - monthly_summary['expense']

    # คำนวณประสิทธิภาพการใช้จ่าย
    efficiency_metrics = {
        'savings_rate': (monthly_summary['income'] - monthly_summary['expense']) / monthly_summary['income'] * 100 if monthly_summary['income'] > 0 else 0,
        'necessary_expense_rate': 0,  # ต้องเพิ่มการระบุค่าใช้จ่ายจำเป็น
        'expense_to_income_ratio': monthly_summary['expense'] / monthly_summary['income'] * 100 if monthly_summary['income'] > 0 else 0
    }

    # ดึงเป้าหมายการออม
    savings_goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()

    # เตรียมข้อมูลกราฟ
    expense_categories = calculate_category_distribution(transactions)

    # สร้างรายการปีและเดือนสำหรับตัวเลือก
    years = range(2020, datetime.now().year + 1)
    thai_months = [
        'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
        'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
    ]

    return render_template('dashboard/overview.html',
        transactions=transactions,
        monthly_summary=monthly_summary,
        efficiency_metrics=efficiency_metrics,
        savings_goals=savings_goals,
        expense_categories=expense_categories,
        years=years,
        thai_months=thai_months,
        selected_year=year,
        selected_month=month,
        today=datetime.now()
    )

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    # รับพารามิเตอร์จาก URL
    period = int(request.args.get('period', '12'))  # Default 12 เดือน

    # คำนวณช่วงวันที่
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period * 30)  # ประมาณ

    # ดึงธุรกรรมทั้งหมด
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .filter(Transaction.date >= start_date)\
        .filter(Transaction.date <= end_date)\
        .order_by(Transaction.date.asc())\
        .all()

    # คำนวณค่าเฉลี่ยต่อเดือน
    total_months = period
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    
    avg_monthly_income = total_income / total_months if total_months > 0 else 0
    avg_monthly_expense = total_expense / total_months if total_months > 0 else 0

    # คำนวณการเปลี่ยนแปลง
    if len(transactions) >= 2:
        first_month_income = sum(t.amount for t in transactions[:30] if t.type == 'income')
        last_month_income = sum(t.amount for t in transactions[-30:] if t.type == 'income')
        first_month_expense = sum(t.amount for t in transactions[:30] if t.type == 'expense')
        last_month_expense = sum(t.amount for t in transactions[-30:] if t.type == 'expense')
        
        income_growth = ((last_month_income - first_month_income) / first_month_income * 100) if first_month_income > 0 else 0
        expense_growth = ((last_month_expense - first_month_expense) / first_month_expense * 100) if first_month_expense > 0 else 0
    else:
        income_growth = 0
        expense_growth = 0

    # คำนวณอัตราการออม
    total_saving = total_income - total_expense
    savings_rate = (total_saving / total_income * 100) if total_income > 0 else 0

    # คำนวณคะแนนสุขภาพทางการเงิน (0-100)
    financial_health_score = min(100, 
        (savings_rate * 0.4) +  # อัตราการออม 40%
        (min(100, (avg_monthly_income / 30000) * 100) * 0.3) +  # รายได้ต่อเดือน 30%
        (min(100, (100 - (avg_monthly_expense / avg_monthly_income * 100) if avg_monthly_income > 0 else 0)) * 0.3)  # สัดส่วนค่าใช้จ่าย 30%
    )

    # กำหนดสถานะสุขภาพทางการเงิน
    if financial_health_score >= 80:
        financial_health_status = 'ดีมาก'
    elif financial_health_score >= 60:
        financial_health_status = 'ดี'
    elif financial_health_score >= 40:
        financial_health_status = 'พอใช้'
    else:
        financial_health_status = 'ควรปรับปรุง'

    # วิเคราะห์และให้คำแนะนำ
    financial_analysis = [
        {
            'title': 'การออม',
            'description': f'อัตราการออมของคุณอยู่ที่ {savings_rate:.1f}% ของรายได้',
            'recommendations': [
                'พยายามออมอย่างน้อย 20% ของรายได้',
                'ตั้งเป้าหมายการออมที่ชัดเจน',
                'จัดสรรเงินออมก่อนใช้จ่าย'
            ] if savings_rate < 20 else [
                'ยอดเยี่ยม! พิจารณาการลงทุนเพื่อเพิ่มผลตอบแทน',
                'วางแผนการออมระยะยาว',
                'แบ่งเงินออมเป็นหมวดหมู่ตามเป้าหมาย'
            ]
        },
        {
            'title': 'รายจ่าย',
            'description': f'ค่าใช้จ่ายเฉลี่ยต่อเดือน ฿{avg_monthly_expense:,.2f}',
            'recommendations': [
                'ตรวจสอบและตัดค่าใช้จ่ายที่ไม่จำเป็น',
                'ทำงบประมาณรายเดือน',
                'ติดตามค่าใช้จ่ายอย่างสม่ำเสมอ'
            ] if avg_monthly_expense > avg_monthly_income * 0.8 else [
                'บริหารค่าใช้จ่ายได้ดี',
                'พิจารณาการลงทุนส่วนที่เหลือ',
                'วางแผนการใช้จ่ายล่วงหน้า'
            ]
        }
    ]

# เตรียมข้อมูลเปรียบเทียบ
    comparison_metrics = [
        {
            'name': 'อัตราการออม',
            'value': f'{savings_rate:.1f}',
            'unit': '%',
            'comparison': 'สูงกว่าค่าเฉลี่ย 5%' if savings_rate > 15 else 'ต่ำกว่าค่าเฉลี่ย 5%',
            'status': 'good' if savings_rate > 15 else 'warning',
            'description': 'เทียบกับค่าเฉลี่ยการออมของคนไทยที่ 15%'
        },
        {
            'name': 'ค่าใช้จ่ายต่อรายได้',
            'value': f'{(avg_monthly_expense/avg_monthly_income*100 if avg_monthly_income > 0 else 0):.1f}',
            'unit': '%',
            'comparison': 'ดีกว่าค่าเฉลี่ย' if avg_monthly_expense < avg_monthly_income * 0.7 else 'สูงกว่าค่าเฉลี่ย',
            'status': 'good' if avg_monthly_expense < avg_monthly_income * 0.7 else 'warning',
            'description': 'ค่าเฉลี่ยทั่วไปอยู่ที่ 70% ของรายได้'
        },
        {
            'name': 'การเติบโตของรายได้',
            'value': f'{income_growth:.1f}',
            'unit': '%',
            'comparison': 'เติบโตดี' if income_growth > 5 else 'ควรหารายได้เพิ่ม',
            'status': 'good' if income_growth > 5 else 'warning',
            'description': 'เทียบกับอัตราเงินเฟ้อที่ 3-5% ต่อปี'
        }
    ]

    # เตรียมข้อมูลแนวโน้ม
    trend_data = {
        'labels': [],
        'income': [],
        'expense': [],
        'savings': []
    }

    # สร้างข้อมูลแนวโน้มรายเดือน
    for i in range(period):
        month_start = end_date - timedelta(days=(period-i)*30)
        month_end = end_date - timedelta(days=(period-i-1)*30)
        
        month_transactions = [t for t in transactions 
                            if month_start <= t.date < month_end]
        
        month_income = sum(t.amount for t in month_transactions if t.type == 'income')
        month_expense = sum(t.amount for t in month_transactions if t.type == 'expense')
        month_saving = month_income - month_expense

        trend_data['labels'].append(month_start.strftime('%Y-%m'))
        trend_data['income'].append(month_income)
        trend_data['expense'].append(month_expense)
        trend_data['savings'].append(month_saving)

    # เตรียมข้อมูลการกระจายค่าใช้จ่าย
    expense_distribution = calculate_category_distribution(transactions)

    # คำนวณค่าเฉลี่ยการใช้จ่ายทั่วไป (ตัวอย่าง)
    avg_expense_distribution = {
        'อาหาร/เครื่องดื่ม': 30,
        'ที่พัก': 25,
        'เดินทาง': 15,
        'สาธารณูปโภค': 10,
        'ความบันเทิง': 10,
        'อื่นๆ': 10
    }

    return render_template('dashboard/analytics.html',
        avg_monthly_income=avg_monthly_income,
        avg_monthly_expense=avg_monthly_expense,
        income_growth=income_growth,
        expense_growth=expense_growth,
        savings_rate=savings_rate,
        financial_health_score=financial_health_score,
        financial_health_status=financial_health_status,
        financial_analysis=financial_analysis,
        comparison_metrics=comparison_metrics,
        trend_data=trend_data,
        expense_distribution=expense_distribution,
        avg_expense_distribution=avg_expense_distribution,
    )