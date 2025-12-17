from dotenv import load_dotenv
import os
from flask import Flask
load_dotenv()
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
# Added new models to import
from models import db, User, Product, Wallet, SiteSetting
from routes import bp as core_bp
import config

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.wsgi_app = ProxyFix(app.wsgi_app)

    app.config['SECRET_KEY'] = 'dev-secret-change-me'
    
    # --- FORCE ABSOLUTE DATABASE PATH ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'final_shop.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print(f"✅ FORCING DATABASE CONNECTION TO: {db_path}") 
    # --------------------------------------------------

    # Load Google Keys
    app.config['GOOGLE_CLIENT_ID'] = config.GOOGLE_CLIENT_ID
    app.config['GOOGLE_CLIENT_SECRET'] = config.GOOGLE_CLIENT_SECRET
    
    db.init_app(app)
    Migrate(app, db)

    # --- NEW: Context Processor for Global Site Settings ---
    # This makes 'site_settings' available in EVERY HTML template automatically.
    @app.context_processor
    def inject_site_settings():
        settings = {}
        try:
            # Fetch settings if DB is ready
            email_setting = SiteSetting.query.filter_by(key='support_email').first()
            telegram_setting = SiteSetting.query.filter_by(key='telegram_id').first()
            
            settings['support_email'] = email_setting.value if email_setting else 'admin@example.com'
            settings['telegram_id'] = telegram_setting.value if telegram_setting else '@support'
        except:
            # Fallback if table doesn't exist yet during setup
            settings['support_email'] = 'admin@example.com'
            settings['telegram_id'] = '@support'
            
        return dict(site_settings=settings)
    # -------------------------------------------------------

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
        db.create_all()
        # --- DEBUG CHECKS ---
        p_count = Product.query.count()
        w_count = Wallet.query.count()
        print(f"👀 DATABASE STATUS: Found {p_count} Products and {w_count} Wallets.")

    return app

app = create_app()

if __name__ == '__main__':
    app.run()