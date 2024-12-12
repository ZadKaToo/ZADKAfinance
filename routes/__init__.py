#routes/_init_.py

def init_routes(app):
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .transactions import transactions_bp
    from .goals import goals_bp
    from .debt import debt_bp
    from .user import user_bp
    
    
    # Register blueprints with proper URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.register_blueprint(goals_bp, url_prefix='/goals')
    app.register_blueprint(debt_bp, url_prefix='/debt')
    app.register_blueprint(user_bp, url_prefix='/user')

