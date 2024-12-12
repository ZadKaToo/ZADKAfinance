from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Debt, DebtPayment
from sqlalchemy import extract

debt_bp = Blueprint('debt', __name__, url_prefix='/debt')

@debt_bp.route('/')
@login_required
def debtmain():
    """หน้าหลักการจัดการหนี้สิน"""
    # Get all debts for current user
    debts = Debt.query.filter_by(user_id=current_user.id).all()
    
    # Calculate summary statistics
    total_debt = sum(debt.remaining_amount for debt in debts)
    monthly_payment = sum(debt.monthly_payment for debt in debts)
    monthly_interest = sum(debt.calculate_monthly_interest() for debt in debts)
    total_count = len(debts)
    
    return render_template('debt/debtmain.html',
        debts=debts,
        total_debt=total_debt,
        monthly_payment=monthly_payment,
        monthly_interest=monthly_interest,
        total_count=total_count
    )

@debt_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    """Add new debt record"""
    try:
        if request.method == 'POST':
            # Get form data
            type = request.form.get('type')
            amount = float(request.form.get('amount', 0))
            interest_rate = float(request.form.get('interest_rate', 0))
            term_months = int(request.form.get('term_months', 0))
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            payment_date = int(request.form.get('payment_date', 1))

            # Validate required fields
            if not all([type, amount, interest_rate, term_months, start_date, end_date, payment_date]):
                flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'error')
                return render_template('debt/add.html')

            # Calculate monthly payment
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = amount * monthly_rate * pow(1 + monthly_rate, term_months)
            monthly_payment = monthly_payment / (pow(1 + monthly_rate, term_months) - 1)

            # Create new debt record
            debt = Debt(
                user_id=current_user.id,
                type=type,
                amount=amount,
                interest_rate=interest_rate,
                term_months=term_months,
                monthly_payment=monthly_payment,
                remaining_amount=amount,
                start_date=start_date,
                end_date=end_date,
                payment_date=payment_date,
                status='active'
            )

            db.session.add(debt)
            db.session.commit()

            flash('เพิ่มรายการหนี้สำเร็จ', 'success')
            return redirect(url_for('debt.debtmain'))

        # GET request - show form
        return render_template('debt/add.html', today=datetime.now())

    except ValueError as e:
        flash('ข้อมูลไม่ถูกต้อง กรุณาตรวจสอบอีกครั้ง', 'error')
        return render_template('debt/add.html')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return render_template('debt/add.html')

@debt_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """ลบรายการหนี้"""
    try:
        debt = Debt.query.get_or_404(id)
        if debt.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        db.session.delete(debt)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    
@debt_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit debt record"""
    # Get the debt record
    debt = Debt.query.get_or_404(id)
    
    # Check if user owns this debt record
    if debt.user_id != current_user.id:
        flash('ไม่มีสิทธิ์เข้าถึงรายการนี้', 'error')
        return redirect(url_for('debt.debtmain'))
    
    try:
        if request.method == 'POST':
            # Update debt details
            debt.type = request.form.get('type')
            debt.amount = float(request.form.get('amount', 0))
            debt.interest_rate = float(request.form.get('interest_rate', 0))
            debt.term_months = int(request.form.get('term_months', 0))
            debt.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
            debt.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
            debt.payment_date = int(request.form.get('payment_date', 1))

            # Recalculate monthly payment
            monthly_rate = debt.interest_rate / 100 / 12
            monthly_payment = debt.amount * monthly_rate * pow(1 + monthly_rate, debt.term_months)
            debt.monthly_payment = monthly_payment / (pow(1 + monthly_rate, debt.term_months) - 1)

            db.session.commit()
            flash('แก้ไขรายการหนี้สำเร็จ', 'success')
            return redirect(url_for('debt.debtmain'))

        return render_template('debt/edit.html', debt=debt)

    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')
        return render_template('debt/edit.html', debt=debt)
    