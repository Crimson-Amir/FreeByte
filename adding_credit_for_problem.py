import logging
import time
import uuid
from datetime import datetime
import traceback
import asyncio
import pytz
import requests
from setting import telegram_bot_token
from database_sqlalchemy import SessionLocal
import models_sqlalchemy as model
from crud import vpn_crud
from vpn_service import buy_and_upgrade_service, panel_api

TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

NOTIFICATION_MESSAGE = (
    "با درود و احترام،\n\n"
    "ضمن پوزش بابت قطعی دو ساعته سرویس‌ها و قطعی یک‌روزه سرور اصلی (دوم مه)، به اطلاع می‌رساند که "
    "این اختلال به‌دلیل خطای انسانی و قطع ارتباط کارت شبکه رخ داده بود.\n\n"
    "در راستای جبران این اختلال، 10 درصد به مشخصات کلی سرویس‌های شما افزوده شده است."
)

chat_ids_sent = set()


async def send_telegram_message(message: str, chat_id: int):
    try:
        response = requests.post(
            url=TELEGRAM_API_URL.format(telegram_bot_token),
            json={'chat_id': chat_id, 'text': message[:4096]}
        )
        logging.info(f"Sent message to user {chat_id} - Status: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending message to {chat_id}: {e}")


from sqlalchemy.orm import joinedload

async def do_it():
    with SessionLocal() as session:
        purchases = session.query(model.Purchase).options(
            joinedload(model.Purchase.product).joinedload(model.Product.main_server),
            joinedload(model.Purchase.owner)
        ).all()

    for purchase in purchases:
        try:
            if purchase.status != "active" or not purchase.username:
                continue

            main_server_ip = purchase.product.main_server.server_ip

            user_info = await panel_api.marzban_api.get_user(main_server_ip, purchase.username)
            if user_info.get("status") != "active":
                continue

            ten_percent_traffic = int(purchase.traffic * 0.1)
            ten_percent_days = int(purchase.period * 0.1)

            updated_traffic_bytes = (ten_percent_traffic * (1024 ** 3)) + user_info.get("data_limit", 0)

            new_traffic = purchase.traffic + ten_percent_traffic
            new_period = purchase.period + ten_percent_days

            json_config = await buy_and_upgrade_service.create_json_config(
                purchase.username,
                new_period,
                updated_traffic_bytes,
                org_traffic=97636764160,
                service_uuid=purchase.service_uuid or uuid.uuid4().hex
            )

            await panel_api.marzban_api.modify_user(main_server_ip, purchase.username, json_config)

            success_msg = (
                f"🟢 سرویس شما با آیدی {purchase.purchase_id} با موفقیت ارتقاء یافت.\n"
                f"مشخصات اضافه شده به سرویس:\n"
                f"ترافیک: {ten_percent_traffic} گیگابایت\n"
                f"دوره زمانی: {ten_percent_days} روز"
            )

            # New session per operation
            with SessionLocal() as update_session:
                vpn_crud.update_purchase(
                    update_session,
                    purchase.purchase_id,
                    traffic=new_traffic,
                    period=new_period,
                    upgrade_traffic=0,
                    upgrade_period=0,
                    status='active',
                    register_date=datetime.now(TEHRAN_TZ),
                    expired_at=None,
                    day_notification_status=False,
                    traffic_notification_status=False,
                    traffic_notification_status_2=False
                )
                update_session.commit()

            chat_id = purchase.chat_id or purchase.owner.chat_id

            if chat_id not in chat_ids_sent:
                await send_telegram_message(NOTIFICATION_MESSAGE, chat_id)
                chat_ids_sent.add(chat_id)

            await send_telegram_message(success_msg, chat_id)
            logging.error(f"successfully add {ten_percent_traffic} GB and {ten_percent_days} day to service {purchase.purchase_id}")
            time.sleep(2)

        except Exception as e:
            logging.error(f"**** Purchase ID {purchase.purchase_id} failed: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(do_it())