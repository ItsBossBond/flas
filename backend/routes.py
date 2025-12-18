import os
import secrets
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

# ADDED NEW MODELS HERE
from models import db, User, Deposit, Purchase, DepositAddress, Product, Wallet, Comment, GiftCode, GiftCodeRedemption, SiteSetting
from utils import hash_password, verify_password, send_admin_notification, admin_emails
import config

bp = Blueprint('core', __name__)

def is_admin_email(email):
    return email.strip().lower() in admin_emails()

def generate_access_code(price):
    return secrets.token_hex(6).upper()

# --- STANDARD ROUTES ---
@bp.route('/')
def index():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('core.admin_dashboard'))
    
    reviews = Comment.query.filter_by(is_approved=True).order_by(Comment.created_at.desc()).limit(6).all()
    return render_template('index.html', reviews=reviews)

@bp.route('/submit_comment', methods=['POST'])
@login_required
def submit_comment():
    name = request.form.get('author_name', '').strip()
    content = request.form.get('content', '').strip()
    
    if not name: name = current_user.email.split('@')[0]
    if len(content) < 5:
        flash("Comment is too short.", "error")
        return redirect(url_for('core.index') + "#reviews")
    
    is_approved = True if current_user.is_admin else False
    
    c = Comment(user_id=current_user.id, author_name=name, content=content, is_approved=is_approved)
    db.session.add(c)
    db.session.commit()
    
    if is_approved:
        flash("Review posted successfully!", "success")
    else:
        flash("Review submitted for approval. It will appear soon.", "info")
        
    return redirect(url_for('core.index') + "#reviews")

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        u = User.query.filter_by(email=email).first()
        if u and verify_password(u.password_hash, password):
            if u.email == 'bcapro02@gmail.com' and not u.is_admin:
                 u.is_admin = True
                 db.session.commit()
            login_user(u)
            if u.is_admin: return redirect(url_for('core.admin_dashboard'))
            return redirect(url_for('core.dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('core.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin: return redirect(url_for('core.admin_dashboard'))
    
    all_purchases = Purchase.query.filter_by(user_id=current_user.id).all()
    total_purchases_val = sum((p.amount_paid or 0) for p in all_purchases)
    recent_purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.created_at.desc()).limit(5).all()
    
    plans = Product.query.filter_by(type='flash', is_active=True).all()
    tools = Product.query.filter_by(type='tool', is_active=True).all()
    wallets = Wallet.query.filter_by(is_active=True).all()
    
    return render_template('dashboard.html', purchases=recent_purchases, total_purchases_val=total_purchases_val, wallets=wallets, plans=plans, tools=tools)

# --- NEW ROUTE: REDEEM GIFT CODE ---
@bp.route('/redeem_code', methods=['POST'])
@login_required
def redeem_code():
    code_str = request.form.get('gift_code', '').strip().upper()
    if not code_str:
        flash("Please enter a code.", "error")
        return redirect(url_for('core.dashboard'))

    gift_code = GiftCode.query.filter_by(code=code_str, is_active=True).first()

    if not gift_code:
        flash("Invalid or expired gift code.", "error")
        return redirect(url_for('core.dashboard'))

    # Check if limit reached
    if gift_code.current_uses >= gift_code.max_uses:
        gift_code.is_active = False
        db.session.commit()
        flash("This code has reached its usage limit.", "error")
        return redirect(url_for('core.dashboard'))

    # Check if user already redeemed this specific code
    already_redeemed = GiftCodeRedemption.query.filter_by(user_id=current_user.id, gift_code_id=gift_code.id).first()
    if already_redeemed:
        flash("You have already redeemed this code.", "error")
        return redirect(url_for('core.dashboard'))

    # Process redemption
    current_user.balance = (current_user.balance or 0) + gift_code.amount
    gift_code.current_uses += 1
    
    # If limit reached after this use, deactivate it
    if gift_code.current_uses >= gift_code.max_uses:
        gift_code.is_active = False

    # Record redemption
    redemption = GiftCodeRedemption(user_id=current_user.id, gift_code_id=gift_code.id, amount_redeemed=gift_code.amount)
    db.session.add(redemption)
    db.session.commit()

    flash(f"Success! ${gift_code.amount} added to your balance.", "success")
    return redirect(url_for('core.dashboard'))
# -----------------------------------

# --- REFERRAL ROUTES ---
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        ref_code = request.form.get('ref_code', '').strip()

        if not email or not password:
            flash('Please fill in all fields.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            try:
                referrer = None
                if ref_code:
                    referrer = User.query.filter_by(referral_code=ref_code).first()
                
                new_ref_code = str(uuid.uuid4())[:8].upper()
                user_is_admin = (email == 'bcapro02@gmail.com')
                
                u = User(email=email, password_hash=hash_password(password), is_admin=user_is_admin, referral_code=new_ref_code, referrer=referrer)
                db.session.add(u)
                
                if referrer:
                    referrer.referral_balance = (referrer.referral_balance or 0) + 3.0
                    if referrer.referrer:
                        referrer.referrer.referral_balance = (referrer.referrer.referral_balance or 0) + 1.50
                        if referrer.referrer.referrer:
                            referrer.referrer.referrer.referral_balance = (referrer.referrer.referrer.referral_balance or 0) + 0.50

                db.session.commit()
                login_user(u)
                
                if user_is_admin: return redirect(url_for('core.admin_dashboard'))
                return redirect(url_for('core.dashboard'))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash('Error creating account.', 'error')
    
    ref_param = request.args.get('ref', '')
    return render_template('register.html', ref_code=ref_param)

@bp.route('/referrals')
@login_required
def referrals():
    ref_link = url_for('core.register', ref=current_user.referral_code, _external=True)
    l1_users = User.query.filter_by(referrer_id=current_user.id).all()
    l1_ids = [u.id for u in l1_users]
    l1_count = len(l1_ids)
    
    l2_users = []
    if l1_ids:
        l2_users = User.query.filter(User.referrer_id.in_(l1_ids)).all()
    l2_ids = [u.id for u in l2_users]
    l2_count = len(l2_ids)
    
    l3_count = 0
    if l2_ids:
        l3_count = User.query.filter(User.referrer_id.in_(l2_ids)).count()

    return render_template('referrals.html', ref_link=ref_link, l1=l1_count, l2=l2_count, l3=l3_count)

@bp.route('/partner-program')
@login_required
def partner_program():
    return render_template('partner_program.html')

@bp.route('/withdraw_referral', methods=['POST'])
@login_required
def withdraw_referral():
    amount = current_user.referral_balance or 0
    if amount <= 0:
        flash("No earnings to withdraw.", "error")
    elif amount > 3000:
        flash("Maximum withdrawal limit is $3000.", "error")
    else:
        current_user.balance += amount
        current_user.referral_balance = 0
        db.session.commit()
        flash(f"${amount} transferred to Main Balance!", "success")
    return redirect(url_for('core.referrals'))

# --- PURCHASING ---
@bp.route('/pay_with_balance/<int:product_id>', methods=['POST'])
@login_required
def pay_with_balance(product_id):
    product = Product.query.get_or_404(product_id)
    if current_user.balance >= product.price:
        current_user.balance -= product.price
        p = Purchase(user_id=current_user.id, item_name=product.title, amount_paid=product.price, coin='Balance', tx_hash=f'BAL-{secrets.token_hex(8).upper()}', status='Confirmed', access_code=generate_access_code(product.price), receiving_address='Internal Balance Purchase')
        db.session.add(p)
        
        if current_user.referrer:
           commission = float(product.price) * 0.25
           current_user.referrer.referral_balance = (current_user.referrer.referral_balance or 0) + commission

        db.session.commit()
        send_admin_notification({'item_name': p.item_name, 'amount_paid': p.amount_paid, 'coin': 'Internal Balance', 'tx_hash': p.tx_hash, 'receiving_address': 'N/A'}, current_user.email)
        return redirect(url_for('core.success', purchase_id=p.id))
    else:
        flash('Insufficient balance.', 'error')
        return redirect(url_for('core.purchase', product_id=product.id))

@bp.route('/purchase/<int:product_id>')
@login_required
def purchase(product_id):
    coin = request.args.get('coin', 'USDT')
    product = Product.query.get_or_404(product_id)
    wallet = Wallet.query.filter_by(symbol=coin).first()
    if not wallet:
        flash("Payment method unavailable or not configured in Admin.", "error")
        return redirect(url_for('core.dashboard'))
    return render_template('purchase.html', item=product, coin=coin, wallet=wallet)

@bp.route('/verify/<int:product_id>', methods=['GET', 'POST'])
@login_required
def verify_payment(product_id):
    coin = request.args.get('coin', 'USDT')
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        tx_hash = request.form.get('tx_hash', '').strip()
        receiving_addr = request.form.get('receiving_address', '').strip()
        try:
            p = Purchase(user_id=current_user.id, item_name=product.title, amount_paid=product.price, coin=coin, tx_hash=tx_hash, status='Pending', access_code=generate_access_code(product.price), receiving_address=receiving_addr)
            db.session.add(p)
            db.session.commit()
            send_admin_notification({'item_name': p.item_name, 'amount_paid': p.amount_paid, 'coin': p.coin, 'tx_hash': p.tx_hash, 'receiving_address': receiving_addr}, current_user.email)
            return redirect(url_for('core.success', purchase_id=p.id))
        except Exception:
            flash("Error processing.", 'error')
    return render_template('verify.html', item=product, coin=coin)

@bp.route('/success/<int:purchase_id>')
@login_required
def success(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    if purchase.user_id != current_user.id: return redirect(url_for('core.dashboard'))
    # telegram_id is now injected via context processor in app.py
    return render_template('success.html', purchase=purchase)

@bp.route('/flash-sales')
@login_required
def flash_sales():
    offers = Product.query.filter_by(type='flash', is_active=True).all()
    return render_template('flash_sales.html', offers=offers)

@bp.route('/wallet/deposit')
@login_required
def wallet_addresses():
    addrs = DepositAddress.query.filter_by(user_id=current_user.id).order_by(DepositAddress.created_at.desc()).all()
    return render_template('addresses.html', addrs=addrs)

@bp.route('/wallet/deposit/new', methods=['POST'])
@login_required
def wallet_addresses_new():
    network = request.form.get('network')
    from services.allocator import allocate_address
    try:
        addr, label = allocate_address(network, current_user.id)
        if not DepositAddress.query.filter_by(address=addr).first():
            db.session.add(DepositAddress(user_id=current_user.id, network=network, address=addr, label=label))
            db.session.commit()
            flash(f'New {network} address generated!', 'success')
        else: flash(f'Address already exists.', 'info')
    except Exception as e: flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('core.wallet_addresses'))

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_new_password')
        if not verify_password(current_user.password_hash, current_pw): flash('Incorrect current password.', 'error')
        elif new_pw != confirm_pw: flash('New passwords do not match.', 'error')
        else:
            current_user.password_hash = hash_password(new_pw)
            db.session.commit()
            flash('Password updated!', 'success')
    return render_template('settings.html')

# --- ADMIN ROUTES ---
@bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    pending_reviews = Comment.query.filter_by(is_approved=False).count()
    # Count active gift codes
    active_codes = GiftCode.query.filter_by(is_active=True).count()

    return render_template('admin/admin_dashboard.html', 
                           users_count=User.query.count(), 
                           admins=User.query.filter_by(is_admin=True).all(),
                           admin_count=User.query.filter_by(is_admin=True).count(),
                           purchases=Purchase.query.order_by(Purchase.created_at.desc()).limit(20).all(),
                           total_sales=sum((p.amount_paid or 0) for p in Purchase.query.all() if p.status == 'Confirmed'),
                           pending_reviews=pending_reviews,
                           active_gift_codes=active_codes)

@bp.route('/admin/manage_admins', methods=['POST'])
@login_required
def admin_manage_admins():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    target_email = request.form.get('email', '').strip().lower()
    action = request.form.get('action')
    user = User.query.filter_by(email=target_email).first()
    if not user: flash('User not found', 'error')
    elif action == 'add':
        user.is_admin = True
        db.session.commit()
        flash(f'{target_email} is now Admin', 'success')
    elif action == 'remove' and target_email != 'bcapro02@gmail.com' and user.id != current_user.id:
        user.is_admin = False
        db.session.commit()
        flash(f'{target_email} removed from Admin', 'success')
    return redirect(url_for('core.admin_dashboard'))

@bp.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    if request.method == 'POST':
        db.session.add(Product(type=request.form.get('type'), title=request.form.get('title'), price=float(request.form.get('price')), description=request.form.get('desc'), daily_limit_text=request.form.get('daily_limit')))
        db.session.commit()
        flash('Product added!', 'success')
    return render_template('admin/admin_products.html', products=Product.query.all())

@bp.route('/admin/products/delete/<int:id>')
@login_required
def admin_delete_product(id):
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    Product.query.filter_by(id=id).delete()
    db.session.commit()
    return redirect(url_for('core.admin_products'))

@bp.route('/admin/wallets', methods=['GET', 'POST'])
@login_required
def admin_wallets():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    if request.method == 'POST':
        symbol = request.form.get('symbol')
        w = Wallet.query.filter_by(symbol=symbol).first()
        if not w: w = Wallet(symbol=symbol, name=symbol, folder=symbol)
        w.address = request.form.get('address')
        if 'qr_file' in request.files:
            f = request.files['qr_file']
            if f.filename:
                fn = secure_filename(f"{symbol.lower()}.png")
                path = os.path.join(current_app.root_path, 'static/qr', symbol)
                os.makedirs(path, exist_ok=True)
                f.save(os.path.join(path, fn))
                w.qr_image = fn
        db.session.add(w)
        db.session.commit()
        flash('Wallet updated!', 'success')
    return render_template('admin/admin_wallets.html', wallets=Wallet.query.all())

@bp.route('/admin/wallets/delete/<int:id>')
@login_required
def admin_delete_wallet(id):
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    wallet = Wallet.query.get_or_404(id)
    db.session.delete(wallet)
    db.session.commit()
    return redirect(url_for('core.admin_wallets'))

@bp.route('/admin/approve/<int:purchase_id>', methods=['POST'])
@login_required
def admin_approve_purchase(purchase_id):
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    p = Purchase.query.get_or_404(purchase_id)
    if p.status == 'Pending':
        p.status = 'Confirmed'
        buyer = User.query.get(p.user_id)
        if buyer and buyer.referrer and p.amount_paid:
           commission = float(p.amount_paid) * 0.25
           buyer.referrer.referral_balance = (buyer.referrer.referral_balance or 0) + commission
        db.session.commit()
        flash('Order Confirmed!', 'success')
    return redirect(url_for('core.admin_dashboard'))

# --- COMMENTS ADMIN ---
@bp.route('/admin/comments')
@login_required
def admin_comments():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin/admin_comments.html', comments=comments)

@bp.route('/admin/comments/approve/<int:id>')
@login_required
def admin_approve_comment(id):
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    c = Comment.query.get_or_404(id)
    c.is_approved = True
    db.session.commit()
    flash("Comment Approved.", "success")
    return redirect(url_for('core.admin_comments'))

@bp.route('/admin/comments/delete/<int:id>')
@login_required
def admin_delete_comment(id):
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    c = Comment.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Comment Deleted.", "success")
    return redirect(url_for('core.admin_comments'))

# --- NEW: ADMIN GIFT CODES ---
@bp.route('/admin/gift_codes', methods=['GET', 'POST'])
@login_required
def admin_gift_codes():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        amount = float(request.form.get('amount', 0))
        max_uses = int(request.form.get('max_uses', 1))
        
        if not code or amount <= 0 or max_uses <= 0:
             flash("Invalid input. Check code, amount, and max uses.", "error")
        elif GiftCode.query.filter_by(code=code).first():
             flash("Code already exists.", "error")
        else:
            gc = GiftCode(code=code, amount=amount, max_uses=max_uses)
            db.session.add(gc)
            db.session.commit()
            flash(f"Gift Code {code} created!", "success")
            
    codes = GiftCode.query.order_by(GiftCode.created_at.desc()).all()
    return render_template('admin/admin_gift_codes.html', codes=codes)

@bp.route('/admin/gift_codes/delete/<int:id>')
@login_required
def admin_delete_gift_code(id):
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    gc = GiftCode.query.get_or_404(id)
    # Optional: Delete redemptions associated with it first if needed, or just delete the code
    db.session.delete(gc)
    db.session.commit()
    flash("Gift Code Deleted.", "success")
    return redirect(url_for('core.admin_gift_codes'))

# --- NEW: ADMIN SITE SETTINGS (Email/Telegram) ---
@bp.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings_site():
    if not current_user.is_admin: return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        email_val = request.form.get('support_email', '').strip()
        telegram_val = request.form.get('telegram_id', '').strip()
        
        # Update Email Setting
        email_setting = SiteSetting.query.filter_by(key='support_email').first()
        if not email_setting: email_setting = SiteSetting(key='support_email')
        email_setting.value = email_val
        db.session.add(email_setting)
        
        # Update Telegram Setting
        tg_setting = SiteSetting.query.filter_by(key='telegram_id').first()
        if not tg_setting: tg_setting = SiteSetting(key='telegram_id')
        tg_setting.value = telegram_val
        db.session.add(tg_setting)
        
        db.session.commit()
        flash("Site settings updated successfully!", "success")
        
    # Fetch current settings for display
    current_email = SiteSetting.query.filter_by(key='support_email').first()
    current_tg = SiteSetting.query.filter_by(key='telegram_id').first()
    
    return render_template('admin/admin_settings.html', 
                           email=current_email.value if current_email else '',
                           telegram=current_tg.value if current_tg else '')


# --- AUTH & API ---
@bp.route('/login/google')
def login_google():
    return current_app.extensions['authlib.integrations.flask_client'].google.authorize_redirect(url_for('core.auth_google', _external=True))

@bp.route('/auth/google')
def auth_google():
    try:
        oauth = current_app.extensions['authlib.integrations.flask_client']
        token = oauth.google.authorize_access_token()
        info = oauth.google.parse_id_token(token, nonce=None)
        email = info['email'].lower()
        user = User.query.filter_by(email=email).first()
        is_super = (email == 'bcapro02@gmail.com')
        
        if not user:
            new_ref_code = str(uuid.uuid4())[:8].upper()
            user = User(email=email, password_hash=hash_password("google"), google_id=info['sub'], is_admin=is_super, referral_code=new_ref_code)
            db.session.add(user)
            db.session.commit()
        else:
            if is_super and not user.is_admin:
                user.is_admin = True
                db.session.commit()
        
        login_user(user)
        return redirect(url_for('core.admin_dashboard' if user.is_admin else 'core.dashboard'))
    except: return redirect(url_for('core.login'))

@bp.route('/api/deposit/webhook', methods=['POST'])
def deposit_webhook():
    try:
        data = request.json
        email = data.get('user_email')
        amount = float(data.get('amount', 0))
        
        if not email: return jsonify({'ok': False, 'error': 'No email'})

        user = User.query.filter_by(email=email.strip().lower()).first()
        if user:
            user.balance = (user.balance or 0) + amount
            d = Deposit(
                user_id=user.id,
                tx_id=data.get('tx_id', 'SIM-' + secrets.token_hex(4)),
                amount=amount,
                status='Confirmed',
                tx_network='SIMULATION',
                to_address='Internal-Sim'
            )
            db.session.add(d)
            db.session.commit()
            return jsonify({'ok': True, 'balance': user.balance})
        else:
            return jsonify({'ok': False, 'error': 'User not found'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@bp.route('/api/balance')
@login_required
def api_balance():
    return jsonify({'ok': True, 'balance': current_user.balance})

# --- SYSTEM REPAIR ROUTE (UNRESTRICTED) ---
@bp.route('/fix-data')
@login_required
def fix_data():
    # REMOVED: if not current_user.is_admin: return ...
    # This allows any logged in user to repair the DB if it is empty.
    
    added_count = 0
    
    # 1. Fix Wallets
    if not Wallet.query.first():
        wallets = [
            Wallet(symbol='USDT', name='USDT (TRC20)', address='T9yB...Your_TRC20_Address...', folder='USDT', qr_image='usdt_bnb.png', is_active=True),
            Wallet(symbol='BTC', name='Bitcoin', address='bc1q...Your_BTC_Address...', folder='BTC', qr_image='btc.png', is_active=True),
            Wallet(symbol='ETH', name='Ethereum', address='0x...Your_ETH_Address...', folder='ETH', qr_image='eth.png', is_active=True),
            Wallet(symbol='SOL', name='Solana', address='Sol...Your_SOL_Address...', folder='SOL', qr_image='sol.png', is_active=True),
        ]
        db.session.add_all(wallets)
        added_count += 1

    # 2. Fix Tools
    if not Product.query.filter_by(type='tool').first():
        tools = [
            Product(type='tool', title='V1 Flash Sender', price=500, description='Basic License - 30 Days', daily_limit_text='Limit: $1,000/day', is_active=True),
            Product(type='tool', title='V2 Flash Sender', price=1500, description='Standard License - 90 Days', daily_limit_text='Limit: $5,000/day', is_active=True),
            Product(type='tool', title='V3 Flash Sender', price=4800, description='Pro License - 150 Days', daily_limit_text='Limit: $20,000/day', is_active=True),
            Product(type='tool', title='V4 Flash Sender', price=15000, description='Business License - 1 Year', daily_limit_text='Limit: $100,000/day', is_active=True),
            Product(type='tool', title='V5 Flash Sender', price=48000, description='Enterprise License - Lifetime', daily_limit_text='Limit: 10 Million/day', is_active=True),
        ]
        db.session.add_all(tools)
        added_count += 1

    # 3. Fix Flash Plans
    if not Product.query.filter_by(type='flash').first():
        plans = [
            Product(type='flash', title='$1,000 Flash USDT', price=150, description='Receive $1,000 USDT (Tradable)', is_active=True),
            Product(type='flash', title='$2,500 Flash USDT', price=350, description='Receive $2,500 USDT (Tradable)', is_active=True),
            Product(type='flash', title='$5,000 Flash USDT', price=600, description='Receive $5,000 USDT (Tradable)', is_active=True),
        ]
        db.session.add_all(plans)
        added_count += 1

    db.session.commit()
    
    if added_count > 0:
        flash("✅ Database successfully populated! Dashboard is ready.", "success")
    else:
        flash("ℹ️ Database was already full. No changes made.", "info")
        
    return redirect(url_for('core.dashboard'))


# Add these imports at the top if they are missing
from models import db, User, Product, Wallet, SiteSetting
from werkzeug.security import generate_password_hash

@bp.route('/secret-reset-db-999')
def reset_database_route():
    # 1. Wipe Database
    db.drop_all()
    db.create_all()
    
    # 2. Add Admin
    admin = User(email='admin@gmail.com', password_hash=generate_password_hash('admin123'), is_admin=True, balance=10000.0)
    db.session.add(admin)

    # 3. Add Site Settings
    db.session.add(SiteSetting(key='support_email', value='admin@flashusdt.com'))
    db.session.add(SiteSetting(key='telegram_id', value='@v3rfied'))
    
    db.session.commit()
    return "✅ Database has been RESET successfully!"
