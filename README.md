# FreeByte

FreeByte is a Python-based Telegram platform for selling and managing **VPN services** and **virtual phone numbers**, with wallet payments, referrals, admin tooling, and webhook-powered automations.

It combines three runtime components:

- **Telegram Bot** (main user/admin interface)
- **FastAPI WebApp** (payment callbacks and service webhooks)
- **Celery Worker** (background payment processing and notifications)

---

## Highlights

- Multi-service Telegram bot built on `python-telegram-bot`
- VPN purchase, upgrade, revoke, and usage/statistics flows
- Virtual number purchase + SMS retrieval workflow
- Wallet and payment integrations (ZarinPal + Cryptomus)
- Admin operations panel flows and ticket/support handling
- SQLAlchemy data layer over PostgreSQL
- Scheduled tasks for notifications and maintenance

---

## Tech Stack

- **Language:** Python
- **Bot framework:** `python-telegram-bot`
- **API framework:** FastAPI + Jinja templates
- **Task queue:** Celery
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Integrations:** Telegram Bot API, ZarinPal, Cryptomus, OnlineSim

---

## Project Structure

```text
FreeByte/
├── main.py                     # Telegram bot entry point
├── WebAppFastApi.py            # FastAPI app (payment + webhook endpoints)
├── tasks.py                    # Celery tasks
├── database_sqlalchemy.py      # Engine/session/base setup
├── models_sqlalchemy.py        # Database models
├── requirements.txt            # Python dependencies
├── templates/                  # Payment result HTML pages
├── admin/                      # Admin handlers and utilities
├── vpn_service/                # VPN domain logic
├── virtual_number/             # Virtual number domain logic
├── dialogues/                  # Localized bot texts
├── crud/                       # Data access layer
└── WebApp/                     # WebApp utilities and dialogues
```

---

## Prerequisites

- Python 3.10+ (recommended)
- PostgreSQL
- A running message broker for Celery (as configured in `CELERY_BROKER_URL`)
- Telegram bot token
- Merchant/API credentials for payment providers you enable

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/AmirHBuilds/FreeByte
cd FreeByte
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

> Note: If `requirements.txt` encoding causes install issues in your environment, convert it to UTF-8 first, then rerun installation.

---

## Configuration

This project expects a `setting.py` module in the repository root (same level as `main.py`).

At minimum, configure values such as:

- `telegram_bot_token`
- `postgres_url`
- `CELERY_BROKER_URL`
- `ADMIN_CHAT_IDs`
- Thread IDs used for admin reporting (e.g. `error_thread_id`, `info_thread_id`, etc.)
- `webapp_url`, `webapp_private_token`
- `zarinpal_merchant_id`, `zarinpal_url_callback`
- `cryptomus_api_key`, `cryptomus_merchant_id`, `cryptomus_url_callback`
- Service pricing/behavior settings (e.g. `PRICE_PER_GB`, `PRICE_PER_DAY`, warning thresholds)
- `onlinesim_api`

Use secure secret management for production (environment variables, vaults, or deployment secrets), and avoid committing real credentials.

---

## Running the System

### 1) Start the Telegram bot

```bash
python main.py
```

### 2) Start the FastAPI service

```bash
uvicorn WebAppFastApi:app --host 0.0.0.0 --port 8000 --reload
```

### 3) Start the Celery worker

```bash
celery -A tasks.celery_app worker --loglevel=info
```

For production, run each component under a process manager (`systemd`, `supervisord`, Docker, Kubernetes, etc.).

---

## Core Flows

- **User onboarding:** `/start` with language selection and optional referral handling
- **Wallet:** credit purchase + transaction tracking
- **VPN services:** buy, view details, revoke/remove, and scheduled notifications
- **Virtual numbers:** buy numbers and receive verification SMS updates
- **Payments:** callback verification through FastAPI endpoints
- **Background jobs:** asynchronous payment handling and notification/report tasks via Celery

---

## API/Webhook Endpoints (FastAPI)

- `GET /` — health check
- `GET /zarinpal_receive_payment_result/` — ZarinPal callback handler
- `POST /cryptomus_receive_payment_result/` — Cryptomus callback handler
- `POST /send_telegram_notification/` — Telegram message relay endpoint
- `GET /onlinesim` — OnlineSim SMS callback receiver

Ensure your provider callback URLs target this service correctly and are reachable from the internet (or via secure tunneling/reverse proxy).

---

## Development Notes

- Logging writes to both console and `freebyte.log`.
- Database tables are created at bot startup (`Base.metadata.create_all(bind=engine)`).
- Keep long-running services isolated and monitored.
- Add migrations (Alembic) for production-grade schema evolution if not already in your deployment workflow.

---

## Security Recommendations

- Never commit `setting.py` with real secrets.
- Restrict webhook endpoints by IP, signature, token, or reverse-proxy access controls.
- Use HTTPS everywhere (especially payment callbacks).
- Rotate API keys and bot tokens periodically.
- Implement structured error tracking/alerting in production.

---

## Troubleshooting

- **Bot won’t start:** verify `setting.py` exists and `telegram_bot_token` is valid.
- **DB errors:** check `postgres_url`, DB reachability, and credentials.
- **Celery tasks not running:** verify broker availability and `CELERY_BROKER_URL`.
- **Payment callbacks failing:** confirm public callback URL, provider credentials, and server logs.
- **Missing messages/notifications:** check admin thread IDs and Telegram permissions.

---

## Contributing

1. Create a feature branch.
2. Keep changes focused and documented.
3. Test impacted flows (bot, API, and worker where applicable).
4. Open a pull request with clear context and validation steps.

---

## License

No explicit license file is currently included in this repository.
If you plan to distribute or open-source this project, add a `LICENSE` file with the desired terms.
