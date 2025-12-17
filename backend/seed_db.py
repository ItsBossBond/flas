from app import create_app
from models import db, Product, Wallet

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database Reset: Tables dropped and recreated.")

    # 1. Seed Wallets (Corrected Paths)
    # Ensure you have the images in:
    # backend/static/qr/USDT/usdt.png
    # backend/static/qr/BTC/btc.png
    # backend/static/qr/ETH/eth.png
    wallets = [
        Wallet(symbol='USDT', name='USDT (TRC20)', address='T9yB...Your_TRC20_Address...', folder='USDT', qr_image='usdt.png'),
        Wallet(symbol='BTC', name='Bitcoin', address='bc1q...Your_BTC_Address...', folder='BTC', qr_image='btc.png'),
        Wallet(symbol='ETH', name='Ethereum', address='0x...Your_ETH_Address...', folder='ETH', qr_image='eth.png'),
    ]
    db.session.add_all(wallets)

    # 2. Seed Software Tools (V1-V5 as requested)
    tools = [
        Product(type='tool', title='V1 Flash Sender', price=500, description='150 Days Validity', daily_limit_text='Limit: $1,000/day'),
        Product(type='tool', title='V2 Flash Sender', price=1500, description='150 Days Validity', daily_limit_text='Limit: $5,000/day'),
        Product(type='tool', title='V3 Flash Sender', price=4800, description='150 Days Validity', daily_limit_text='Limit: $20,000/day'),
        Product(type='tool', title='V4 Flash Sender', price=15000, description='150 Days Validity', daily_limit_text='Limit: $100,000/day'),
        Product(type='tool', title='V5 Flash Sender', price=48000, description='150 Days Validity', daily_limit_text='Limit: 10 Million/day'),
    ]
    db.session.add_all(tools)

    # 3. Seed Flash Plans
    plans = [
        Product(type='flash', title='$1000 Flash USDT', price=200, description='Get $1000 USDT value'),
        Product(type='flash', title='$2000 Flash USDT', price=350, description='Get $2000 USDT value'),
    ]
    db.session.add_all(plans)
    
    db.session.commit()
    print("Database Seeded Successfully! You can now log in.")