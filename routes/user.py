from flask import Blueprint, render_template
from flask_login import login_required, current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html')

@user_bp.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')