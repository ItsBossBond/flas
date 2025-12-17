# Flash USDT Sale Website — Starter (Base)

Features:
- Email/password auth, dashboard, flash sales, purchases
- Simulated deposit webhook `/api/deposit/webhook` (credits balance on status=confirmed)
- Premium dark UI
- SQLite by default; switch to MySQL/Postgres via `DATABASE_URL`

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask --app backend/app.py db-init
flask --app backend/app.py 
flask --app backend/app.py --debug run
```


---
## Added in this build
- Google OAuth login (Authlib)
- Real provider webhook `/api/deposit/provider/<provider>` with HMAC (X-Signature)

See `.env.example` for required variables.


---
## Full implementation extras
- Deposit addresses (TRC20 / ERC-20) per user
- Address allocator service (DEV_FAKE / GATEWAY_HTTP / XPUB placeholder)
- Provider webhook can credit by `to_address`
- On-chain poller + confirmations (ETH/TRON gateway placeholders)
- Alembic migrations (pre-seeded)
- Flask-Migrate integration & CLI `poll-onchain`
