#routes/goals.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, FinancialGoal, Transaction
from datetime import datetime, timedelta
from sqlalchemy import desc
import math
import traceback

goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

@goals_bp.route('/')
@login_required
def list():
    # รับพารามิเตอร์การกรองและการเรียงลำดับ
    status = request.args.get('status')
    category = request.args.get('category')
    sort = request.args.get('sort', 'deadline')

    # สร้าง query สำหรับเป้าหมาย
    query = FinancialGoal.query.filter_by(user_id=current_user.id)

    # กรองตามสถานะ
    if status:
        query = query.filter_by(status=status)

    # กรองตามหมวดหมู่
    if category:
        query = query.filter_by(category=category)

    # เรียงลำดับ
    if sort == 'deadline':
        query = query.order_by(FinancialGoal.target_date)
    elif sort == 'progress':
        query = query.order_by(FinancialGoal.current_amount / FinancialGoal.target_amount)
    elif sort == 'amount':
        query = query.order_by(desc(FinancialGoal.target_amount))
    elif sort == 'created':
        query = query.order_by(desc(FinancialGoal.created_at))

    goals = query.all()

    # คำนวณสรุปเป้าหมาย
    active_goals = [goal for goal in goals if goal.status == 'in_progress']
    total_goals = len(goals)  
    total_savings = sum(goal.current_amount for goal in goals)  
    average_progress = sum(goal.get_progress_percentage() for goal in active_goals) / len(active_goals) if len(active_goals) > 0 else 0

    # คำนวณสถิติการเงิน
    now = datetime.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    # ดึงธุรกรรมเดือนปัจจุบัน
    current_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .filter(Transaction.date >= current_month_start)\
        .filter(Transaction.date <= now)\
        .all()

    # ดึงธุรกรรมเดือนก่อน
    previous_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .filter(Transaction.date >= prev_month_start)\
        .filter(Transaction.date < current_month_start)\
        .all()

    # คำนวณยอดรวมเดือนปัจจุบัน
    total_income = sum(t.amount for t in current_transactions if t.type == 'income')
    total_expense = sum(t.amount for t in current_transactions if t.type == 'expense')
    balance = total_income - total_expense

    # คำนวณยอดรวมเดือนก่อน
    prev_income = sum(t.amount for t in previous_transactions if t.type == 'income')
    prev_expense = sum(t.amount for t in previous_transactions if t.type == 'expense')

    # คำนวณการเปลี่ยนแปลง
    income_change = ((total_income - prev_income) / prev_income * 100) if prev_income > 0 else 0
    expense_change = ((total_expense - prev_expense) / prev_expense * 100) if prev_expense > 0 else 0

    # รายการหมวดหมู่เป้าหมาย
    goal_categories = [
        'short_term', 'medium_term', 'long_term', 'emergency',
        'retirement', 'education', 'property', 'other'
    ]

    return render_template('goals/list.html',
        goals=goals,
        total_goals=total_goals,
        total_savings=total_savings,
        average_progress=average_progress,
        goal_categories=goal_categories,
        status=status,
        category=category,
        sort=sort,
        # เพิ่มข้อมูลการเงิน
        balance=balance,
        total_income=total_income,
        total_expense=total_expense,
        income_change=income_change,
        expense_change=expense_change
    )

@goals_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            # ตรวจสอบข้อมูล
            target_amount = float(request.form['target_amount'])
            initial_amount = float(request.form.get('initial_amount', 0))
            if target_amount <= 0:
                raise ValueError('จำนวนเงินเป้าหมายต้องมากกว่า 0')
            if initial_amount < 0:
                raise ValueError('จำนวนเงินเริ่มต้นต้องไม่น้อยกว่า 0')
            if initial_amount > target_amount:
                raise ValueError('จำนวนเงินเริ่มต้นต้องไม่มากกว่าเป้าหมาย')

            # สร้างเป้าหมายใหม่
            goal = FinancialGoal(
                user_id=current_user.id,
                name=request.form['name'],
                description=request.form['description'],
                target_amount=target_amount,
                current_amount=initial_amount,
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d'),
                target_date=datetime.strptime(request.form['target_date'], '%Y-%m-%d'),
                category=request.form['category'],
                status='in_progress',
                reminder_enabled=bool(request.form.get('reminder_enabled')),
                reminder_frequency=request.form.get('reminder_frequency', 'weekly')
            )

            db.session.add(goal)
            db.session.commit()

            flash('เพิ่มเป้าหมายสำเร็จ', 'success')
            return redirect(url_for('goals.list'))

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return render_template('goals/add.html', today=datetime.now())

@goals_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    goal = FinancialGoal.query.get_or_404(id)
    
    # ตรวจสอบว่าเป็นเป้าหมายของผู้ใช้นี้
    if goal.user_id != current_user.id:
        flash('ไม่มีสิทธิ์เข้าถึงเป้าหมายนี้', 'error')
        return redirect(url_for('goals.list'))

    if request.method == 'POST':
        try:
            # ตรวจสอบข้อมูล
            target_amount = float(request.form['target_amount'])
            current_amount = float(request.form['current_amount'])
            if target_amount <= 0:
                raise ValueError('จำนวนเงินเป้าหมายต้องมากกว่า 0')
            if current_amount < 0:
                raise ValueError('จำนวนเงินปัจจุบันต้องไม่น้อยกว่า 0')

            # อัพเดทข้อมูล
            goal.name = request.form['name']
            goal.description = request.form['description']
            goal.target_amount = target_amount
            goal.current_amount = current_amount
            goal.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            goal.target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d')
            goal.category = request.form['category']
            goal.status = request.form['status']
            goal.reminder_enabled = bool(request.form.get('reminder_enabled'))
            goal.reminder_frequency = request.form.get('reminder_frequency', 'weekly')

            db.session.commit()
            flash('แก้ไขเป้าหมายสำเร็จ', 'success')
            return redirect(url_for('goals.list'))

        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return render_template('goals/edit.html', goal=goal)

@goals_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    goal = FinancialGoal.query.get_or_404(id)
    
    # ตรวจสอบว่าเป็นเป้าหมายของผู้ใช้นี้
    if goal.user_id != current_user.id:
        flash('ไม่มีสิทธิ์เข้าถึงเป้าหมายนี้', 'error')
        return redirect(url_for('goals.list'))

    try:
        db.session.delete(goal)
        db.session.commit()
        flash('ลบเป้าหมายสำเร็จ', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('goals.list'))


@goals_bp.route('/<int:id>/update', methods=['POST'])
@login_required
def update_amount(id):
    goal = FinancialGoal.query.get_or_404(id)

    if goal.user_id != current_user.id:
        return jsonify({
            'success': False, 
            'error': 'ไม่มีสิทธิ์เข้าถึงเป้าหมายนี้'
        }), 403

    try:
        data = request.form
        if not all(k in data for k in ['amount', 'transaction_type']):
            return jsonify({
                'success': False,
                'error': 'ข้อมูลไม่ครบถ้วน'
            }), 400

        amount = float(data['amount'])
        transaction_type = data['transaction_type']
        note = data.get('note', '')

        if amount <= 0:
            return jsonify({
                'success': False,
                'error': 'จำนวนเงินต้องมากกว่า 0'
            }), 400

        if transaction_type == 'withdraw':
            if amount > goal.current_amount:
                return jsonify({
                    'success': False,
                    'error': 'ยอดเงินไม่เพียงพอสำหรับการถอน'
                }), 400

            transaction = Transaction(
                user_id=current_user.id,
                type='income',
                category='ถอนเงินจากออม',
                amount=amount,
                date=datetime.now(),
                note=f'ถอนเงินจากออม: {goal.name} - {note}' if note else f'ถอนเงินจากออม: {goal.name}',
                goal_id=goal.id
            )
            goal.current_amount -= amount

        elif transaction_type == 'deposit':
            transaction = Transaction(
                user_id=current_user.id,
                type='expense',
                category='เพิ่มเงินออม',
                amount=amount,
                date=datetime.now(),
                note=f'เพิ่มเงินออม: {goal.name} - {note}' if note else f'เพิ่มเงินออม: {goal.name}',
                goal_id=goal.id
            )
            goal.current_amount += amount

        db.session.add(transaction)

        if goal.history is None:
            goal.history = []
        
        goal.history.append({
            'date': datetime.now().isoformat(),
            'type': transaction_type,
            'amount': amount,
            'note': note,
            'transaction_id': transaction.id
        })

        if goal.current_amount >= goal.target_amount and goal.status != 'completed':
            goal.status = 'completed'

        # Calculate totals - Corrected query
        total_income = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income'
        ).scalar() or 0

        total_expense = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense'
        ).scalar() or 0

        db.session.commit()

        balance = total_income - total_expense

        return jsonify({
            'success': True,
            'message': 'ถอนเงินสำเร็จ' if transaction_type == 'withdraw' else 'เพิ่มเงินสำเร็จ',
            'goal_amount': float(goal.current_amount),
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'balance': float(balance),
            'completed': goal.status == 'completed'
        })

    except ValueError:
        return jsonify({
            'success': False,
            'error': 'รูปแบบข้อมูลไม่ถูกต้อง'
        }), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating goal: {str(e)}")  # Add this for debugging
        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 500
        
@goals_bp.route('/<int:id>')
@login_required
def detail(id):
    goal = FinancialGoal.query.get_or_404(id)
    
    # ตรวจสอบว่าเป็นเป้าหมายของผู้ใช้นี้
    if goal.user_id != current_user.id:
        flash('ไม่มีสิทธิ์เข้าถึงเป้าหมายนี้', 'error')
        return redirect(url_for('goals.list'))

    # คำนวณข้อมูลเพิ่มเติม
    days_remaining = (goal.target_date - datetime.now()).days
    daily_saving_needed = goal.get_daily_saving_needed()
    is_achievable = goal.is_achievable()

    progress_data = {
        'percentage': goal.get_progress_percentage(),
        'current_amount': goal.current_amount,
        'remaining_amount': goal.get_remaining_amount(),
        'days_remaining': days_remaining,
        'daily_saving': daily_saving_needed,
        'is_achievable': is_achievable
    }

    return render_template('goals/detail.html',
        goal=goal,
        progress_data=progress_data
    )
    
[{
	"resource": "/c:/Users/User/Desktop/ZadkaFinacal/routes/goals.py",
	"owner": "python",
	"code": {
		"value": "reportUndefinedVariable",
		"target": {
			"$mid": 1,
			"path": "/microsoft/pyright/blob/main/docs/configuration.md",
			"scheme": "https",
			"authority": "github.com",
			"fragment": "reportUndefinedVariable"
		}
	},
	"severity": 4,
	"message": "\"goals_analytics\" is not defined",
	"source": "Pylance",
	"startLineNumber": 467,
	"startColumn": 29,
	"endLineNumber": 467,
	"endColumn": 44
}]

@goals_bp.route('/analytics')
@login_required
def analytics():
    print("Analytics route accessed")  # Debug print
    try:
        # Get all active goals
        goals = FinancialGoal.query.filter_by(
            user_id=current_user.id,
            status='in_progress'
        ).all()
        print(f"Found {len(goals)} active goals")  # Debug print

        today = datetime.now()
        print(f"Current date: {today}")  # Debug print
        
        try:
            year = request.args.get('year', today.year, type=int)
            month = request.args.get('month', today.month, type=int)
            print(f"Requested year: {year}, month: {month}")  # Debug print
        except Exception as date_error:
            print(f"Error getting date parameters: {str(date_error)}")  # Debug print
            year = today.year
            month = today.month

        # Calculate analytics for each goal
        goals_analytics = []
        for goal in goals:
            try:
                days_remaining = (goal.target_date - today).days
                remaining_amount = goal.target_amount - goal.current_amount
                
                months_remaining = math.ceil(days_remaining / 30)
                monthly_recommendation = remaining_amount / months_remaining if months_remaining > 0 else 0
                optimal_pace = remaining_amount / days_remaining if days_remaining > 0 else 0
                progress = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0

                goals_analytics.append({
                    'goal': goal,
                    'monthly_recommendation': monthly_recommendation,
                    'optimal_pace': optimal_pace,
                    'days_remaining': days_remaining,
                    'months_remaining': months_remaining,
                    'progress': progress
                })
                print(f"Processed goal: {goal.name}")  # Debug print
            except Exception as goal_error:
                print(f"Error processing goal {goal.id}: {str(goal_error)}")  # Debug print
                continue

        print(f"Processed {len(goals_analytics)} goals")  # Debug print

        # Create calendar date from request or default to today
        calendar_date = datetime(year, month, 1)
        print(f"Calendar date: {calendar_date}")  # Debug print
        
        # Get previous and next month for navigation
        prev_month = calendar_date.replace(day=1) - timedelta(days=1)
        next_month = (calendar_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        # Calculate calendar data
        first_day = calendar_date.replace(day=1)
        
        if calendar_date.month == 12:
            last_day = calendar_date.replace(year=calendar_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = calendar_date.replace(month=calendar_date.month + 1, day=1) - timedelta(days=1)

        first_weekday = first_day.weekday()
        print(f"First weekday: {first_weekday}")  # Debug print
        
        # Previous month days
        prev_month_days = []
        if first_weekday > 0:
            for i in range(first_weekday):
                day = first_day - timedelta(days=i+1)
                goals_on_day = [
                    {
                        'goal': goal,
                        'type': 'deadline' if goal.target_date.date() == day.date() else 'milestone',
                        'color': 'red' if goal.target_date.date() == day.date() else 'yellow'
                    }
                    for goal in goals if goal.target_date.date() == day.date()
                ]
                prev_month_days.insert(0, {
                    'day': day.day,
                    'month': 'prev',
                    'date': day,
                    'goals': goals_on_day,
                    'is_past': day.date() < today.date()
                })

        # Current month days
        current_month_days = []
        for i in range(1, last_day.day + 1):
            day = first_day.replace(day=i)
            goals_on_day = [
                {
                    'goal': goal,
                    'type': 'deadline' if goal.target_date.date() == day.date() else 'milestone',
                    'color': 'red' if goal.target_date.date() == day.date() else 'yellow'
                }
                for goal in goals if goal.target_date.date() == day.date()
            ]
            
            current_month_days.append({
                'day': i,
                'month': 'current',
                'date': day,
                'goals': goals_on_day,
                'is_today': day.date() == today.date(),
                'is_past': day.date() < today.date()
            })

        # Next month days
        total_days = len(prev_month_days) + len(current_month_days)
        remaining_days = 42 - total_days
        
        next_month_days = []
        if remaining_days > 0:
            next_month_start = last_day + timedelta(days=1)
            for i in range(remaining_days):
                day = next_month_start + timedelta(days=i)
                goals_on_day = [
                    {
                        'goal': goal,
                        'type': 'deadline' if goal.target_date.date() == day.date() else 'milestone',
                        'color': 'red' if goal.target_date.date() == day.date() else 'yellow'
                    }
                    for goal in goals if goal.target_date.date() == day.date()
                ]
                next_month_days.append({
                    'day': day.day,
                    'month': 'next',
                    'date': day,
                    'goals': goals_on_day,
                    'is_past': day.date() < today.date()
                })

        calendar_days = prev_month_days + current_month_days + next_month_days
        print(f"Calendar days generated: {len(calendar_days)}")  # Debug print

        # Thai month names
        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]

        print("Rendering template")  # Debug print
        return render_template(
            'goals/analytics.html',
            goals_analytics=goals_analytics,
            calendar_days=calendar_days,
            weekdays=['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา'],
            current_month=thai_months[calendar_date.month - 1],
            current_year=calendar_date.year + 543,
            today=today,
            prev_month=prev_month,
            next_month=next_month
        )

    except Exception as e:
        print(f"Global error in analytics: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        flash(str(e), 'error')
        return redirect(url_for('goals.list'))