import sys
import os

# 1. Add the 'backend' folder to Python's system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 2. Import directly
from app import create_app
# Add SiteSetting to imports
from models import db, Product, Wallet, User, Comment, SiteSetting
from utils import hash_password

app = create_app()

with app.app_context():
    print("🔄 Connecting to database...")
    db.create_all()  # Ensure tables exist

    # --- 1. SEED WALLETS ---
    if not Wallet.query.first():
        print("Creating Wallets...")
        wallets = [
            Wallet(symbol='USDT', name='USDT (TRC20)', address='T9yB...Your_TRC20_Address...', folder='USDT', qr_image='usdt_bnb.png', is_active=True),
            Wallet(symbol='BTC', name='Bitcoin', address='bc1q...Your_BTC_Address...', folder='BTC', qr_image='btc.png', is_active=True),
            Wallet(symbol='ETH', name='Ethereum', address='0x...Your_ETH_Address...', folder='ETH', qr_image='eth.png', is_active=True),
        ]
        db.session.add_all(wallets)
    else:
        print("✅ Wallets already exist.")

    # --- 2. SEED TOOLS ---
    if not Product.query.filter_by(type='tool').first():
        print("Creating Software Tools...")
        tools = [
            Product(type='tool', title='V1 Flash Sender', price=500, description='Basic License - 30 Days', daily_limit_text='Limit: $1,000/day', is_active=True),
            Product(type='tool', title='V2 Flash Sender', price=1500, description='Standard License - 90 Days', daily_limit_text='Limit: $5,000/day', is_active=True),
            Product(type='tool', title='V3 Flash Sender', price=4800, description='Pro License - 150 Days', daily_limit_text='Limit: $20,000/day', is_active=True),
            Product(type='tool', title='V4 Flash Sender', price=15000, description='Business License - 1 Year', daily_limit_text='Limit: $100,000/day', is_active=True),
            Product(type='tool', title='V5 Flash Sender', price=48000, description='Enterprise License - Lifetime', daily_limit_text='Limit: 10 Million/day', is_active=True),
        ]
        db.session.add_all(tools)
    else:
        print("✅ Tools already exist.")

    # --- 3. SEED FLASH PLANS ---
    if not Product.query.filter_by(type='flash').first():
        print("Creating Flash Plans...")
        plans = [
            Product(type='flash', title='$1,000 Flash USDT', price=150, description='Receive $1,000 USDT (Tradable)', is_active=True),
            Product(type='flash', title='$2,500 Flash USDT', price=350, description='Receive $2,500 USDT (Tradable)', is_active=True),
            Product(type='flash', title='$5,000 Flash USDT', price=600, description='Receive $5,000 USDT (Tradable)', is_active=True),
        ]
        db.session.add_all(plans)
    else:
        print("✅ Flash Plans already exist.")

    # --- 4. CREATE ADMIN & SEED COMMENTS ---
    if not User.query.filter_by(email='admin@gmail.com').first():
        print("Creating Admin User...")
        admin = User(
            email='admin@gmail.com',
            password_hash=hash_password('admin123'),
            is_admin=True,
            balance=10000.00
        )
        db.session.add(admin)
        db.session.commit()
        
        print("Seeding Initial Comments...")
        comments = [
            Comment(user_id=admin.id, author_name='CryptoWhale99', content='The Flash sender tool V2 works perfectly. Got my USDT in like 2 mins.', is_approved=True),
            Comment(user_id=admin.id, author_name='Sarah_Trading', content='Support helped me setup the wallet. 10/10 service.', is_approved=True),
            Comment(user_id=admin.id, author_name='BlockchainDev', content='Checked the hash, valid on tronscan. Good job guys.', is_approved=True),
            Comment(user_id=admin.id, author_name='Michael B.', content='Bought the $1000 Flash plan. It is tradeable on Binance. Will buy again.', is_approved=True),
        ]
        db.session.add_all(comments)
        
    else:
        print("✅ Admin user already exists.")
        
    # --- 5. SEED DEFAULT SITE SETTINGS (New) ---
    if not SiteSetting.query.first():
        print("Seeding Default Site Settings...")
        settings = [
            SiteSetting(key='support_email', value='admin@flashusdt.com'),
            SiteSetting(key='telegram_id', value='@v3rfied')
        ]
        db.session.add_all(settings)
    else:
        print("✅ Site Settings already exist.")

    db.session.commit()
    print("🎉 Database seeded successfully! Restart your Flask app.")