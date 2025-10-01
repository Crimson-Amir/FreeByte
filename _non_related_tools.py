import logging
import time
import uuid
from datetime import datetime, timezone
import traceback
import asyncio
import pytz
import requests

from API.convert_irt_to_usd import price
from setting import telegram_bot_token
from database_sqlalchemy import SessionLocal
import models_sqlalchemy as model
from crud import vpn_crud, crud
from vpn_service import buy_and_upgrade_service, panel_api
import qrcode, json
from io import BytesIO


TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

NOTIFICATION_MESSAGE = ("""
📣 اطلاعیه

با توجه به ناپایداری‌های اخیر که برخی از کاربران در اتصال به سرویس تجربه کردند، و در راستای حفظ کیفیت خدمات و رضایت شما، موارد زیر به تمامی اشتراک‌ها اضافه شده است:

🎁 ۵ گیگابایت ترافیک هدیه
⏳️ ۱۵ روز زمان 

در حال حاضر، کلیه سرویس‌ها و سرور ها به‌طور کامل فعال هستند و میتونید خریدتون رو مثل سابق انجام بدید.
در صورت بروز مشکل در اتصال، لطفاً اشتراک خود را به‌روزرسانی کنید.

💬 پشتیبانی آنلاین همواره آماده پاسخ‌گویی به سوالات شماست.
از شکیبایی، همراهی و اعتماد شما سپاس‌گزاریم.
"""
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


def send_telegram_photo(photo_bytes: bytes, caption: str, chat_id: int, reply_markup=None):
    try:
        files = {'photo': ('qrcode.png', photo_bytes)}
        data = {
            'chat_id': chat_id,
            'caption': caption[:1024],
            'parse_mode': 'HTML'
        }
        if reply_markup:
            data['reply_markup'] = reply_markup
        response = requests.post(
            url=f"https://api.telegram.org/bot{telegram_bot_token}/sendPhoto",
            data=data,
            files=files
        )
        logging.info(f"Sent photo to user {chat_id} - Status: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending photo to {chat_id}: {e}")

from sqlalchemy.orm import joinedload

async def do_it():
    with SessionLocal() as session:
        purchases = session.query(model.Purchase).options(
            joinedload(model.Purchase.product).joinedload(model.Product.main_server),
            joinedload(model.Purchase.owner)
        ).all()
    target_chat_ids = [248, 1223, 22, 1555, 314]
    for purchase in purchases:
        try:
            if not purchase.username or purchase.purchase_id not in target_chat_ids:
                continue

            main_server_ip = purchase.product.main_server.server_ip

            user_info = await panel_api.marzban_api.get_user(main_server_ip, purchase.username)
            if not user_info: continue

            ten_percent_traffic = 5
            ten_percent_days = 15

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


GIFT_TRAFFIC_GB = 2
GIFT_PERIOD_DAYS = 15
START_DATE = datetime(2025, 6, 15, tzinfo=timezone.utc)
text2 = """
ضمن خوش‌آمدگویی به شما، بابت اختلالات اخیر در سرویس‌ها و مشکلات پیش‌آمده در روند خرید و دریافت اشتراک طی دو هفته گذشته، صمیمانه پوزش می‌طلبیم.
به پاس صبوری و همراهی شما عزیز، هدیه‌ای ویژه برایتان در نظر گرفته‌ایم که شامل موارد زیر است:

🎁 ۲ گیگابایت ترافیک هدیه
⏳ ۱۵ روز زمان استفاده

در حال حاضر کلیه سرویس‌ها و سرورها به‌طور کامل فعال هستند و می‌توانید خرید خود را با استفاده از درگاه های پرداخت انجام دهید

💬 تیم پشتیبانی آنلاین ما همواره آماده پاسخ‌گویی به سوالات و راهنمایی شماست.
از اعتماد، صبوری و همراهی ارزشمندتان بی‌نهایت سپاس‌گزاریم.
با آرزوی تجربه‌ای بهتر و سریع‌تر
"""

async def do_it_2():
    with SessionLocal() as session:
        users = session.query(model.UserDetail).options(
            joinedload(model.UserDetail.services)
        ).filter(model.UserDetail.register_date > START_DATE).all()

    for user in users:
        try:
            if user.services: continue

            with SessionLocal() as session:
                purchase = crud.create_purchase(session, 1, user.chat_id, GIFT_TRAFFIC_GB, GIFT_PERIOD_DAYS)
                get_purchase = await buy_and_upgrade_service.create_service_in_servers(session, purchase.purchase_id)

                main_server = get_purchase.product.main_server
                server_port = f":{main_server.server_port}" if main_server.server_port != 443 else ""
                sub_link = f"{main_server.server_protocol}{main_server.server_ip}{server_port}{get_purchase.subscription_url}"

                qr_code = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                qr_code.add_data(sub_link)
                qr_code.make(fit=True)
                qr_image = qr_code.make_image(fill='black', back_color='white')
                buffer = BytesIO()
                qr_image.save(buffer)
                binary_data = buffer.getvalue()

                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": 'راهنمای اتصال 📚', "callback_data": "vpn_guide_menu_in_new_message"},
                            {"text": '🎛 سرویس‌های من', "callback_data": "vpn_my_services_new__1"}
                        ],
                        [
                            {"text": '↰ برگشت', "callback_data": "start_in_new_message"}
                        ]
                    ]
                }

                service_activated_text = (f"✅ سرویس VPN شما با نام {get_purchase.username} فعال شد!"
                                          "\n\n🔺 لطفاً هر روز اشتراک را از طریق برنامه‌ای که استفاده می‌کنید، آپدیت کنید. (اطلاعات بیشتر در راهنمای اتصال)")

                text = f'{service_activated_text}\n\n<code>{sub_link}</code>'
                await send_telegram_message(text2, user.chat_id)

                send_telegram_photo(
                    photo_bytes=binary_data,
                    caption=text,
                    chat_id=user.chat_id,
                    reply_markup=json.dumps(keyboard)
                )

                session.commit()

            logging.info(f"Gift sent to user {user.chat_id}")
            print(f"Gift sent to user {user.chat_id}")
            time.sleep(1)

        except Exception as e:
            logging.error(f"**** Failed to send gift to chat_id {user.chat_id}: {str(e)}\n{traceback.format_exc()}")
            print(f"**** Failed to send gift to chat_id {user.chat_id}: {str(e)}\n{traceback.format_exc()}")

import hashlib
import setting

async def add_users_to_webapp():
    with SessionLocal() as session:
        users = session.query(model.UserDetail).all()

        for user in users:
            try:
                if not user.config or not user.config.webapp_password:
                    continue

                json_data = {
                    'email': str(user.chat_id),
                    'name': user.first_name or 'unknown',
                    'password': user.config.webapp_password,
                    'active': True,
                    'private_token': hashlib.sha256(setting.webapp_private_token.encode()).hexdigest(),
                }
                a = requests.post(
                    url=f"http://shop.freebyte.shop/sign-up/",
                    json=json_data,
                    timeout=4
                )
                print(a)
                delay(1)

            except Exception as e:
                print(f"**** Failed to send gift to chat_id {user.chat_id}: {str(e)}\n{traceback.format_exc()}")



if __name__ == "__main__":
    asyncio.run(add_users_to_webapp())
