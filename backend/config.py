import os

# --- 1. Google Configuration ---
# Hardcoded for stability.
GOOGLE_CLIENT_ID = '221338528459-4j08bn4vcu3h69inpsibttvp4nlhi6dp.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'

# --- 2. Admin & Contact Configuration ---
ADMIN_EMAIL = os.getenv('ADMIN_EMAILS')
# NEW: Load Telegram ID
SUPPORT_TELEGRAM_ID = os.getenv('SUPPORT_TELEGRAM_ID', 'v3rfied')

# --- 3. Payment Configuration ---
# Images must be in: backend/static/qr/{FOLDER}/{IMAGE}
PAYMENT_METHODS = {
    'USDT': {'name': 'USDT (TRC20)', 'address': 'T9yB...Your_TRC20_Address...', 'folder': 'USDT', 'qr_image': 'usdt.png'},
    'BTC':  {'name': 'Bitcoin',      'address': 'bc1q...Your_BTC_Address...',   'folder': 'BTC',  'qr_image': 'btc.png'},
    'ETH':  {'name': 'Ethereum',     'address': '0x...Your_ETH_Address...',     'folder': 'ETH',  'qr_image': 'eth.png'},
    'SOL':  {'name': 'Solana',       'address': 'Sol...Your_SOL_Address...',    'folder': 'SOL',  'qr_image': 'sol.png'},
    'TRX':  {'name': 'Tron',         'address': 'T...Your_TRX_Address...',      'folder': 'TRX',  'qr_image': 'trx.png'},
    'USDC': {'name': 'USDC',         'address': '0x...Your_USDC_Address...',    'folder': 'USDC', 'qr_image': 'usdc.png'}
}

# --- 4. Flash Plans ---
FLASH_PLANS = [
    {'id': 'plan_1000', 'title': '$1000 Flash USDT', 'price': 200, 'desc': 'Get $1000 USDT value'},
    {'id': 'plan_2000', 'title': '$2000 Flash USDT', 'price': 350, 'desc': 'Get $2000 USDT value'},
    {'id': 'plan_3000', 'title': '$3000 Flash USDT', 'price': 450, 'desc': 'Get $3000 USDT value'},
]

# --- 5. Sander Tools ---
SANDER_TOOLS = [
    {'id': 'tool_x1', 'model': 'Sander Model X1', 'price': 120, 'desc': 'Pro edition, high speed'},
    {'id': 'tool_z5', 'model': 'Sander Model Z5', 'price': 250, 'desc': 'Industrial grade, low noise'},
]