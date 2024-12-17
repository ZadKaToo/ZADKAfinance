from flask import Blueprint, render_template, request, current_app, jsonify, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db

user_bp = Blueprint('user', __name__)

# Config for file uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Handle profile image upload
            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Create uploads directory if it doesn't exist
                    upload_folder = os.path.join(current_app.root_path, 'static/uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    # Save file
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    # Update user profile image path
                    current_user.profile_image = f'/static/uploads/{filename}'
                    db.session.commit()
                    return jsonify({'success': True, 'image_url': current_user.profile_image})

            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

    return render_template('user/profile.html')

@user_bp.route('/settings')
@login_required
def settings():
    return render_template('user/settings.html')