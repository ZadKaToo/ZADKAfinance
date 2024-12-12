#models/_init_.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_models(app):
    db.init_app(app)
    
    # Import models here to avoid circular imports
    from .user import User
    from .transaction import Transaction
    from .financialGoal import FinancialGoal
    from .category import Category
    from .Debt import Debt, DebtPayment
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create default categories
        default_categories = {
            'income': ['เงินเดือน', 'ค่าล่วงเวลา', 'โบนัส', 'รายได้เสริม', 'เงินปันผล', 'อื่นๆ'],
            'expense': ['อาหาร/เครื่องดื่ม', 'ที่พัก', 'เดินทาง', 'สาธารณูปโภค', 'ช้อปปิ้ง', 'ความบันเทิง', 
                       'สุขภาพ', 'การศึกษา', 'ประกัน', 'อื่นๆ']
        }
        
        try:
            for type_, names in default_categories.items():
                for name in names:
                    if not Category.query.filter_by(name=name, type=type_).first():
                        category = Category(name=name, type=type_)
                        db.session.add(category)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default categories: {str(e)}")
            
    return db

# Make models available at package level
from .user import User
from .transaction import Transaction
from .financialGoal import FinancialGoal
from .category import Category
from .Debt import Debt, DebtPayment

__all__ = ['db', 'User', 'Transaction', 'FinancialGoal', 'Category', 'Debt', 'DebtPayment']