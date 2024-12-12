#utils/notification.py
from datetime import datetime
from flask import render_template
from flask_mail import Message
from app import mail

def send_goal_reminder(user, goal):
    """ส่งการแจ้งเตือนเป้าหมายการออม"""
    msg = Message(
        'แจ้งเตือนเป้าหมายการออม',
        recipients=[user.email]
    )
    
    remaining_amount = goal.target_amount - goal.current_amount
    days_remaining = (goal.target_date - datetime.now()).days
    daily_saving = remaining_amount / days_remaining if days_remaining > 0 else 0
    
    msg.html = render_template('email/goal_reminder.html',
        user=user,
        goal=goal,
        remaining_amount=remaining_amount,
        days_remaining=days_remaining,
        daily_saving=daily_saving
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_weekly_summary(user, transactions, goals):
    """ส่งสรุปรายสัปดาห์"""
    msg = Message(
        'สรุปการเงินประจำสัปดาห์',
        recipients=[user.email]
    )
    
    # คำนวณสรุปข้อมูล
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    goals_progress = [
        {
            'name': g.name,
            'progress': g.get_progress_percentage(),
            'remaining': g.target_amount - g.current_amount
        }
        for g in goals
    ]
    
    msg.html = render_template('email/weekly_summary.html',
        user=user,
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        goals_progress=goals_progress,
        transactions=transactions[-5:]  # 5 รายการล่าสุด
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False