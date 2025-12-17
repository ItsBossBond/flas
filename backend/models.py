from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, default=0.0)
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Referral fields
    referral_code = db.Column(db.String(10), unique=True, nullable=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    referral_balance = db.Column(db.Float, default=0.0)
    
    # Relationships
    deposits = db.relationship('Deposit', backref='user', lazy=True)
    purchases = db.relationship('Purchase', backref='user', lazy=True)
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[id]), lazy=True)
    redeemed_codes = db.relationship('GiftCodeRedemption', backref='user', lazy=True)

    def get_id(self):
        return str(self.id)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20)) 
    title = db.Column(db.String(100))
    price = db.Column(db.Float)
    description = db.Column(db.String(255))
    daily_limit_text = db.Column(db.String(100), nullable=True) 
    validity_days = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class Wallet(db.Model):
    __tablename__ = 'wallets'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10)) 
    name = db.Column(db.String(50))
    address = db.Column(db.String(255))
    qr_image = db.Column(db.String(100))
    folder = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=True)
    amount_paid = db.Column(db.Float, nullable=True)
    coin = db.Column(db.String(20), nullable=True)
    tx_hash = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='Pending') 
    access_code = db.Column(db.String(100), nullable=True)
    receiving_address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Deposit(db.Model):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tx_id = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    tx_network = db.Column(db.String(20), nullable=True)
    to_address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmations = db.Column(db.Integer, default=0)
    required_confs = db.Column(db.Integer, default=1)
    last_checked_at = db.Column(db.DateTime, nullable=True)

class DepositAddress(db.Model):
    __tablename__ = 'deposit_addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    network = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), unique=True, nullable=False)
    label = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author_name = db.Column(db.String(50), nullable=False) 
    content = db.Column(db.String(500), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- NEW: GIFT CODE MODELS ---
class GiftCode(db.Model):
    __tablename__ = 'gift_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    max_uses = db.Column(db.Integer, default=1) # How many people can use it
    current_uses = db.Column(db.Integer, default=0) # How many have used it
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    redemptions = db.relationship('GiftCodeRedemption', backref='gift_code', lazy=True)

class GiftCodeRedemption(db.Model):
    __tablename__ = 'gift_code_redemptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gift_code_id = db.Column(db.Integer, db.ForeignKey('gift_codes.id'), nullable=False)
    amount_redeemed = db.Column(db.Float, nullable=False)
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)

# --- NEW: SITE SETTINGS MODEL (For editable Email/Telegram) ---
class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False) # e.g., 'support_email'
    value = db.Column(db.String(255), nullable=True) # e.g., 'admin@flashusdt.com'