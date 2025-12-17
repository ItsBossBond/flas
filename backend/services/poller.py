import os, datetime
from models import db, Deposit, User
from services.gateway import EthGateway, TronGateway

def required_confs_for(network: str) -> int:
    n = (network or '').upper()
    return int(os.getenv('REQUIRED_CONFS_ETH' if n=='ERC20' else 'REQUIRED_CONFS_TRON', '12' if n=='ERC20' else '20'))

def poll_pending(app) -> int:
    with app.app_context():
        q = Deposit.query.filter(Deposit.status.in_(['pending','confirming']))
        processed = 0
        egw, tgw = EthGateway(), TronGateway()
        now = datetime.datetime.utcnow()
        for dep in q.limit(500):
            gw = tgw if (dep.tx_network or '').upper()=='TRC20' else egw
            try:
                st = gw.tx_status(dep.tx_id)
            except Exception:
                continue
            dep.confirmations = int(st.get('confirmations') or dep.confirmations or 0)
            dep.to_address = dep.to_address or st.get('to') or dep.to_address
            dep.last_checked_at = now
            req = dep.required_confs or required_confs_for(dep.tx_network)
            status = st.get('status') or 'pending'
            if status == 'failed':
                dep.status = 'failed'
            elif dep.confirmations >= req and status in ('pending','confirming','confirmed'):
                dep.status = 'confirmed'
                user = User.query.get(dep.user_id)
                if user:
                    user.balance += float(dep.amount)
            else:
                dep.status = 'confirming'
            db.session.commit()
            processed += 1
        return processed
