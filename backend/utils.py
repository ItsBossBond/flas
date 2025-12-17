import os
import smtplib
import threading
import secrets
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(hash_value: str, password: str) -> bool:
    return check_password_hash(hash_value, password)

def admin_emails():
    raw = os.getenv("ADMIN_EMAILS", "").strip()
    if not raw: return set()
    return {e.strip().lower() for e in raw.split(",") if e.strip()}

# --- NEW: MISSING ADDRESS GENERATOR ---
def generate_dev_address(network: str, user_id: int) -> str:
    """
    Generates a fake deterministic address for development/simulation.
    """
    prefix = "T" if network.upper() == "TRC20" else "0x"
    # Create a random-looking but consistent string
    random_part = secrets.token_hex(16)
    return f"{prefix}Dev{user_id}{random_part}"

# --- INTERNAL EMAIL WORKER (Runs in background) ---
def _send_email_thread(subject, body, recipients, smtp_config):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_config['user']
        msg['To'] = ", ".join(recipients)

        print(f"🔌 Connecting to SMTP: {smtp_config['server']}:{smtp_config['port']}...")

        if smtp_config['port'] == 465:
            server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(smtp_config['user'], smtp_config['password'])
        server.sendmail(smtp_config['user'], recipients, msg.as_string())
        server.quit()
        print(f"✅ Background Email Sent to {recipients}")
    except Exception as e:
        print(f"❌ Background Email Failed: {e}")

# --- MAIN NOTIFICATION FUNCTION ---
def send_admin_notification(purchase_data, user_email):
    admin_list = list(admin_emails())
    if not admin_list:
        print("⚠️ Warning: No ADMIN_EMAILS configured in .env")
        return

    raw_password = os.getenv("MAIL_PASSWORD")
    if not raw_password:
        print("❌ Error: MAIL_PASSWORD is missing in .env")
        return

    smtp_config = {
        'server': os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        'port': int(os.getenv("MAIL_PORT", 587)),
        'user': os.getenv("MAIL_USERNAME"),
        'password': raw_password.replace(" ", "") 
    }

    if not smtp_config['user']:
        print("❌ Error: MAIL_USERNAME is missing in .env")
        return

    subject = f"🚀 New Flash Purchase: {purchase_data.get('item_name', 'Unknown Item')}"
    body = f"""
    New Purchase Alert!
    
    User: {user_email}
    Item: {purchase_data.get('item_name', 'N/A')}
    Price: ${purchase_data.get('amount_paid', 0)}
    Payment Coin: {purchase_data.get('coin', 'N/A')}
    Transaction Hash: {purchase_data.get('tx_hash', 'N/A')}
    
    --- IMPORTANT ---
    USER RECEIVING ADDRESS: 
    {purchase_data.get('receiving_address', 'N/A')}
    ------------------
    
    Please verify the transaction hash and send the Flash USDT.
    """

    email_thread = threading.Thread(
        target=_send_email_thread, 
        args=(subject, body, admin_list, smtp_config)
    )
    email_thread.start()