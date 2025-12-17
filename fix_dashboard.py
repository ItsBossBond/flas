import sys
import os

# Ensure backend folder is visible
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from models import db, Product, Wallet

app = create_app()

with app.app_context():
    print("🔧 Checking Database for missing items...")
    
    # --- 1. Fix Wallets ---
    if not Wallet.query.first():
        print("  - Wallets table is empty. Adding Wallets...")
        wallets = [
            Wallet(symbol='USDT', name='USDT (TRC20)', address='T9yB...Your_TRC20_Address...', folder='USDT', qr_image='usdt_bnb.png', is_active=True),
            Wallet(symbol='BTC', name='Bitcoin', address='bc1q...Your_BTC_Address...', folder='BTC', qr_image='btc.png', is_active=True),
            Wallet(symbol='ETH', name='Ethereum', address='0x...Your_ETH_Address...', folder='ETH', qr_image='eth.png', is_active=True),
        ]
        db.session.add_all(wallets)
    else:
        print("  - Wallets already exist. Skipping.")

    # --- 2. Fix Software Tools ---
    if not Product.query.filter_by(type='tool').first():
        print("  - Tools table is empty. Adding Software Tools...")
        tools = [
            Product(type='tool', title='V1 Flash Sender', price=500, description='Basic License - 30 Days', daily_limit_text='Limit: $1,000/day', is_active=True),
            Product(type='tool', title='V2 Flash Sender', price=1500, description='Standard License - 90 Days', daily_limit_text='Limit: $5,000/day', is_active=True),
            Product(type='tool', title='V3 Flash Sender', price=4800, description='Pro License - 150 Days', daily_limit_text='Limit: $20,000/day', is_active=True),
            Product(type='tool', title='V4 Flash Sender', price=15000, description='Business License - 1 Year', daily_limit_text='Limit: $100,000/day', is_active=True),
            Product(type='tool', title='V5 Flash Sender', price=48000, description='Enterprise License - Lifetime', daily_limit_text='Limit: 10 Million/day', is_active=True),
        ]
        db.session.add_all(tools)
    else:
        print("  - Tools already exist. Skipping.")

    # --- 3. Fix Flash Plans ---
    if not Product.query.filter_by(type='flash').first():
        print("  - Plans table is empty. Adding Flash Plans...")
        plans = [
            Product(type='flash', title='$1,000 Flash USDT', price=150, description='Receive $1,000 USDT (Tradable)', is_active=True),
            Product(type='flash', title='$2,500 Flash USDT', price=350, description='Receive $2,500 USDT (Tradable)', is_active=True),
            Product(type='flash', title='$5,000 Flash USDT', price=600, description='Receive $5,000 USDT (Tradable)', is_active=True),
        ]
        db.session.add_all(plans)
    else:
        print("  - Plans already exist. Skipping.")

    db.session.commit()
    print("\n✅ SUCCESS: Dashboard data has been repaired!")
    print("   Please refresh your browser page.")