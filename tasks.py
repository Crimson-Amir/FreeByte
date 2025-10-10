import requests
from celery import Celery
import functools
import traceback
from uuid import uuid4
from contextlib import contextmanager
import setting
import logging
from database_sqlalchemy import SessionLocal
from crud import crud
from WebApp import WebAppUtilities
from WebApp.WebAppDialogue import transaction
import asyncio

celery_app = Celery(
    "tasks",
    broker=setting.CELERY_BROKER_URL,
    backend=None
)


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def report_to_admin_api(msg, message_thread_id=setting.error_thread_id):
    json_data = {'chat_id': setting.ADMIN_CHAT_IDs[0], 'text': msg[:4096], 'message_thread_id': message_thread_id}
    requests.post(
        url=f"https://api.telegram.org/bot{setting.telegram_bot_token}/sendMessage",
        json=json_data,
        timeout=10
    )

@celery_app.task(autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5})
def report_to_user_api(chat_id, msg):
    json_data = {'chat_id': chat_id, 'text': msg[:4096]}
    requests.post(
        url=f"https://api.telegram.org/bot{setting.telegram_bot_token}/sendMessage",
        json=json_data,
        timeout=10
    )

def handle_task_errors(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            retries = getattr(self.request, "retries", None)
            max_retries = getattr(self, "max_retries", None)
            error_id = uuid4().hex
            tb = traceback.format_exc()

            logging.error(f"Celery task {func.__name__} failed\nerror: {str(e)}, traceback: {tb}")

            err_msg = (
                f"[🔴 ERROR] Celery task: {func.__name__}"
                f"\n\nType: {type(e)}"
                f"\nReason: {str(e)}"
                f"\nRetries: {retries}/{max_retries}"
                f"\nError ID: {error_id}"
            )

            report_to_admin_api.delay(err_msg)
            raise
    return wrapper

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 5}, max_retries=3)
@handle_task_errors
def handle_payment(self, financial_id, ref_id):
    with session_scope() as db:
        financial = crud.get_financial_report_by_id(db, financial_id)
        if financial.payment_status not in ['paid', 'refund']:
            dialogues = transaction.get(financial.owner.language, transaction.get('fa'))
            if getattr(self.request, "retries", 0) == 0:
                message = f"🟢 {dialogues.get('successful_pay', 'success {0}').format(ref_id)}"
                report_to_user_api.delay(financial.chat_id, message)
            try:
                asyncio.run(WebAppUtilities.handle_successful_payment(db, financial, financial.authority, 'ZarinPalWebApp'))
            except Exception as e:
                if getattr(self.request, "retries", 0) >= getattr(self, "max_retries", 0):
                    asyncio.run(WebAppUtilities.handle_failed_payment(db, financial, e, dialogues, financial.authority, 'ZarinPalWebApp'))
                raise e