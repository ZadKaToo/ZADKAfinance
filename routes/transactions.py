#routes/transaction.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from models import db, Transaction
from datetime import datetime, timedelta
from sqlalchemy import or_, func
from typing import Optional, Dict, Any

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

def get_date_range(range_type: str, start: Optional[str] = None, end: Optional[str] = None) -> tuple:
    today = datetime.now()
    
    if range_type == 'custom' and start and end:
        return (
            datetime.strptime(start, '%Y-%m-%d'),
            datetime.strptime(end, '%Y-%m-%d')
        )
    
    ranges = {
        '7': timedelta(days=7),
        '30': timedelta(days=30),
        '90': timedelta(days=90),
        '180': timedelta(days=180)
    }
    
    if range_type in ranges:
        return (today - ranges[range_type], today)
    
    return (today - timedelta(days=30), today)  # ค่าเริ่มต้น 30 วัน

def build_transaction_query(user_id: int, filters: Dict[str, Any]):
    query = Transaction.query.filter_by(user_id=user_id)
    
    start_date, end_date = get_date_range(
        filters.get('date_range', '30'),
        filters.get('start_date'),
        filters.get('end_date')
    )
    
    query = query.filter(Transaction.date.between(start_date, end_date))
    
    if filters.get('type'):
        query = query.filter(Transaction.type == filters['type'])
    
    if filters.get('category'):
        query = query.filter(Transaction.category == filters['category'])
    
    if filters.get('amount_min') is not None:
        query = query.filter(Transaction.amount >= filters['amount_min'])
    
    if filters.get('amount_max') is not None:
        query = query.filter(Transaction.amount <= filters['amount_max'])
    
    return query

def get_categories():
    """Returns dict of transaction categories"""
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

def get_transaction_stats(transactions) -> Dict[str, float]:
    return {
        'income': sum(t.amount for t in transactions if t.type == 'income'),
        'expense': sum(t.amount for t in transactions if t.type == 'expense')
    }

@transactions_bp.route('/')
@login_required
def list():
    filters = {
        'date_range': request.args.get('date_range', '30'),
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'type': request.args.get('type'),
        'category': request.args.get('category'),
        'amount_min': request.args.get('amount_min', type=float),
        'amount_max': request.args.get('amount_max', type=float)
    }
    
    sort = request.args.get('sort', 'date')
    order = request.args.get('order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    try:
        query = Transaction.query.filter_by(user_id=current_user.id)
        
        # จัดการการเรียงลำดับ
        if sort == 'date':
            if order == 'asc':
                query = query.order_by(Transaction.date.asc())
            else:
                query = query.order_by(Transaction.date.desc())
        elif sort == 'amount':
            if order == 'asc':
                query = query.order_by(Transaction.amount.asc())
            else:
                query = query.order_by(Transaction.amount.desc())
            
        
        # Pagination
        transactions = query.paginate(page=page, per_page=per_page, error_out=False)
        stats = get_transaction_stats(transactions.items)
        
        return render_template('transactions/list.html',
            transactions=transactions.items,
            total_count=transactions.total,
            transaction_count=len(transactions.items),
            total_income=stats['income'],
            total_expense=stats['expense'],
            categories=Transaction.get_categories(),
            date_range=filters['date_range'],
            start_date=filters['start_date'],
            end_date=filters['end_date'],
            type=filters['type'],
            category=filters['category'],
            amount_min=filters['amount_min'],
            amount_max=filters['amount_max'],
            sort=sort,
            order=order,
            page=page,
            pages=transactions.pages,
            offset=(page - 1) * per_page
        )
    
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))
    

# routes/transactions.py

@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        try:
            transaction = Transaction(
                user_id=current_user.id,
                type=request.form['type'],
                category=request.form['category'],
                amount=float(request.form['amount']),
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                note=request.form.get('note', '')
            )
            db.session.add(transaction)
            db.session.commit()
            flash('เพิ่มธุรกรรมสำเร็จ', 'success')
            return redirect(url_for('transactions.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    # Get categories and include today's date for the form
    categories = Transaction.get_categories()
    return render_template('transactions/add.html',
        today=datetime.now(),                    # Add this line for today's date
        income_categories=categories['income'],
        expense_categories=categories['expense']
    )
    

@transactions_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Get transaction
    transaction = Transaction.query.get_or_404(id)
    
    # Verify ownership
    if transaction.user_id != current_user.id:
        flash('ไม่มีสิทธิ์เข้าถึงธุรกรรมนี้', 'error')
        return redirect(url_for('transactions.list'))

    if request.method == 'POST':
        try:
            # Update transaction
            transaction.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            transaction.type = request.form['type']
            transaction.category = request.form['category']
            transaction.amount = float(request.form['amount'])
            transaction.note = request.form.get('note', '')

            db.session.commit()
            flash('แก้ไขธุรกรรมสำเร็จ', 'success')
            return redirect(url_for('transactions.molist'))

        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    # Get categories for form
    categories = Transaction.get_categories()
    
    return render_template('transactions/edit.html',
        transaction=transaction,
        income_categories=categories['income'],
        expense_categories=categories['expense']
    )

@transactions_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    transaction = Transaction.query.get_or_404(id)
    
    # Verify ownership
    if transaction.user_id != current_user.id:
        flash('ไม่มีสิทธิ์เข้าถึงธุรกรรมนี้', 'error')
        return redirect(url_for('transactions.list'))

    try:
        db.session.delete(transaction)
        db.session.commit()
        flash('ลบธุรกรรมสำเร็จ', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาด: {str(e)}', 'error')

    return redirect(url_for('transactions.molist'))

# Add for viewing all transactions
@transactions_bp.route('/molist')
@login_required
def molist():
    # Get all transactions without pagination
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc())\
        .all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expense
    
    return render_template('transactions/molist.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )
    

# In routes/transactions.py
@transactions_bp.route('/update_amount/<int:id>', methods=['POST'])
@login_required
def update_amount(id):
    if request.method == 'POST':
        try:
            transaction = Transaction.query.get_or_404(id)
            
            if transaction.user_id != current_user.id:
                return jsonify({
                    'success': False, 
                    'error': 'ไม่มีสิทธิ์เข้าถึงธุรกรรมนี้'
                }), 403

            amount = float(request.form['amount'])
            transaction_type = request.form['transaction_type']
            note = request.form.get('note', '')

            # Validate amount
            if amount <= 0:
                return jsonify({
                    'success': False,
                    'error': 'จำนวนเงินต้องมากกว่า 0'
                }), 400

            # Check withdrawal limit
            if transaction_type == 'withdraw' and amount > transaction.amount:
                return jsonify({
                    'success': False,
                    'error': 'ยอดเงินไม่เพียงพอสำหรับการถอน'
                }), 400

            # Create opposite transaction
            new_transaction = Transaction(
                user_id=current_user.id,
                type='income' if transaction_type == 'withdraw' else 'expense',
                category='เพิ่มเงินในเป้าหมาย' if transaction_type == 'deposit' else 'ถอนเงินจากเป้าหมาย',
                amount=amount,
                date=datetime.now(),
                note=note
            )

            # Update goal amount
            if transaction_type == 'deposit':
                transaction.amount += amount
            else:
                transaction.amount -= amount

            db.session.add(new_transaction)
            db.session.commit()

            # Calculate totals
            transactions = Transaction.query.filter_by(user_id=current_user.id).all()
            total_income = sum(t.amount for t in transactions if t.type == 'income')
            total_expense = sum(t.amount for t in transactions if t.type == 'expense')
            balance = total_income - total_expense

            return jsonify({
                'success': True,
                'transaction_amount': transaction.amount,
                'total_income': total_income,
                'total_expense': total_expense,
                'balance': balance,
                'message': 'อัพเดทยอดเงินสำเร็จ'
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return jsonify({
        'success': False,
        'error': 'Invalid request'
    }), 400