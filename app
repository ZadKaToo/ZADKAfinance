# app.py
from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from models import init_models, User
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
import socket
import netifaces  # pip install netifaces

def get_network_info():
    """Get all available network interfaces and IPs"""
    network_info = []
    try:
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        
        for iface in interfaces:
            try:
                # Get IPv4 addresses for this interface
                addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
                for addr in addrs:
                    ip = addr['addr']
                    # Skip localhost
                    if ip != '127.0.0.1':
                        network_info.append({
                            'interface': iface,
                            'ip': ip
                        })
            except Exception:
                continue
                
        return network_info
    except Exception:
        # Fallback to simple IP detection
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return [{'interface': 'default', 'ip': ip}]
        except Exception:
            return [{'interface': 'localhost', 'ip': '127.0.0.1'}]

# Initialize extensions
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
    
    
    # Initialize database
    db = init_models(app)
    
    # Initialize other extensions
    login_manager.init_app(app)
    mail.init_app(app)

    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'กรุณาเข้าสู่ระบบเพื่อเข้าถึงหน้านี้'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from routes import init_routes
    init_routes(app)

    # Context processors
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now()
        }

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    port = 5000
    
    # Get network information
    network_info = get_network_info()
    
    # Print server information
    print("\n✨ Server is running!")
    print("\n🏠 Local access:")
    print(f"   http://localhost:{port}")
    print(f"   http://127.0.0.1:{port}")
    
    if network_info:
        print("\n🌐 Network access:")
        for info in network_info:
            print(f"   http://{info['ip']}:{port} ({info['interface']})")
    
    print("\n⚠️  Security Notes:")
    print("   - Make sure your firewall allows connections on port 5000")
    print("   - Only share access with trusted users on secure networks")
    print("   - The server is running in debug mode (not recommended for production)")
    
    print("\n⌨️  CTRL + C to stop the server\n")
    
    # Run the app with network access
    app.run(
        host='0.0.0.0',  # Makes the server accessible from other computers
        port=port,
        debug=True
    )
