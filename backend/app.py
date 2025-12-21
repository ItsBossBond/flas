from dotenv import load_dotenv
import os
import sys

# --- FIX IMPORTS FOR RENDER ---
# Add the current folder to Python path so it can find 'models.py'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# ------------------------------

from flask import Flask
load_dotenv()
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth

# Imports
from models import db, User, Product, Wallet, SiteSetting, Comment, DepositAddress
from routes import bp as core_bp
from utils import hash_password
import config

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    
    # --- DATABASE CONNECTION LOGIC ---
    # 1. Look for the Render Database URL
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Fix for SQLAlchemy (Postgres requires 'postgresql://', not 'postgres://')
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print("✅ CONNECTED TO PERMANENT CLOUD DATABASE (Postgres)")
    else:
        # Fallback to Local SQLite (Only for testing on your laptop)
        basedir = os.path.abspath(os.path.dirname(__file__))
        instance_path = os.path.join(basedir, 'instance')
        if not os.path.exists(instance_path): os.makedirs(instance_path)
        db_path = os.path.join(instance_path, 'final_shop.db')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
        print(f"⚠️ NO DATABASE_URL FOUND. Using temporary local DB: {db_path}")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # -------------------------------------
    
    app.config['GOOGLE_CLIENT_ID'] = config.GOOGLE_CLIENT_ID
    app.config['GOOGLE_CLIENT_SECRET'] = config.GOOGLE_CLIENT_SECRET
    
    db.init_app(app)
    Migrate(app, db)

    # --- Global Site Settings ---
    @app.context_processor
    def inject_site_settings():
        settings = {'support_email': 'admin@flashusdt.com', 'telegram_id': '@v3rfied'}
        try:
            email_setting = SiteSetting.query.filter_by(key='support_email').first()
            telegram_setting = SiteSetting.query.filter_by(key='telegram_id').first()
            if email_setting: settings['support_email'] = email_setting.value
            if telegram_setting: settings['telegram_id'] = telegram_setting.value
        except: pass
        return dict(site_settings=settings)

    oauth = OAuth(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    login_manager = LoginManager()
    login_manager.login_view = 'core.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(core_bp)

    with app.app_context():
        # Create Tables in Postgres
        db.create_all()
        
        # --- AUTO-SEEDER ---
        # If the database is empty, fill it with default data
        if Product.query.count() == 0:
            print("🚀 New Database Detected! Seeding default data...")
            seed_database()
        else:
            print("✅ Database is ready and has data.")

    return app

def seed_database():
    """Refills the database with default Products, Wallets, and Admin."""
    
    # 1. Wallets
    wallets = [
        Wallet(symbol='USDT', name='USDT (TRC20)', address='T9yB...Your_TRC20_Address...', folder='USDT', qr_image='usdt_bnb.png', is_active=True),
        Wallet(symbol='BTC', name='Bitcoin', address='bc1q...Your_BTC_Address...', folder='BTC', qr_image='btc.png', is_active=True),
        Wallet(symbol='ETH', name='Ethereum', address='0x...Your_ETH_Address...', folder='ETH', qr_image='eth.png', is_active=True),
    ]
    db.session.add_all(wallets)

    # 2. Tools
    tools = [
        Product(type='tool', title='V1 Flash Sender', price=500, description='Basic License - 30 Days', daily_limit_text='Limit: $1,000/day', is_active=True),
        Product(type='tool', title='V2 Flash Sender', price=1500, description='Standard License - 90 Days', daily_limit_text='Limit: $5,000/day', is_active=True),
        Product(type='tool', title='V3 Flash Sender', price=4800, description='Pro License - 150 Days', daily_limit_text='Limit: $20,000/day', is_active=True),
        Product(type='tool', title='V4 Flash Sender', price=15000, description='Business License - 1 Year', daily_limit_text='Limit: $100,000/day', is_active=True),
        Product(type='tool', title='V5 Flash Sender', price=48000, description='Enterprise License - Lifetime', daily_limit_text='Limit: 10 Million/day', is_active=True),
    ]
    db.session.add_all(tools)

    # 3. Plans
    plans = [
        Product(type='flash', title='$1,000 Flash USDT', price=150, description='Receive $1,000 USDT (Tradable)', is_active=True),
        Product(type='flash', title='$2,500 Flash USDT', price=350, description='Receive $2,500 USDT (Tradable)', is_active=True),
        Product(type='flash', title='$5,000 Flash USDT', price=600, description='Receive $5,000 USDT (Tradable)', is_active=True),
    ]
    db.session.add_all(plans)

    # 4. Admin User
    if not User.query.filter_by(email='admin@gmail.com').first():
        admin = User(email='admin@gmail.com', password_hash=hash_password('admin123'), is_admin=True, balance=10000.0)
        db.session.add(admin)

    # 5. Site Settings
    if not SiteSetting.query.first():
        db.session.add(SiteSetting(key='support_email', value='admin@flashusdt.com'))
        db.session.add(SiteSetting(key='telegram_id', value='@v3rfied'))

    db.session.commit()
    print("🎉 Data seeded successfully!")

app = create_app()

@app.route("/ping")
def ping():
    return "OK", 200



if __name__ == '__main__':
    app.run()
