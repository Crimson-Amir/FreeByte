import asyncio
import traceback, pytz, sys, os, logging
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vpn_service import panel_api, vpn_utilities, statistics
from crud import vpn_crud
from utilities_reFactore import FindText, report_to_admin, human_readable
from database_sqlalchemy import SessionLocal
import setting
from threading import Lock

class OnlineUsers:
    def __init__(self):
        self.lock = Lock()
        self.online_users = []
    def add_user(self, user_info):
        with self.lock:
            self.online_users.append(user_info)

    def clear_list(self):
        with self.lock:
            self.online_users.clear()

online_users_instance = OnlineUsers()

async def format_traffic_from_megabyte(ft_instance, traffic_in_megabyte, chat_id):
    if traffic_in_megabyte == 0:
        return await ft_instance.find_from_database(chat_id, 'without_usage')
    elif int(traffic_in_megabyte) < 1000:
        return f"{int(traffic_in_megabyte)} {await ft_instance.find_from_database(chat_id, 'megabyte')}"
    else:
        return f"{round(traffic_in_megabyte / 1000, 2)} {await ft_instance.find_from_database(chat_id,'gigabyte')}"

async def send_message_to_user(context, purchase, text, keyboard):
    try:
        await context.bot.send_message(purchase.chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
    except Exception as e:
        logging.error(f'error in send notification to user:\n{e}')

async def report_service_termination_to_user(context, purchase, ft_instance):
    text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_service_termination_notification')
    text = text.format(f"<code>{purchase.username}</code>")
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id, 'vpn_upgrade_service', 'keyboard'), callback_data=f'vpn_upgrade_service__30__40__{purchase.purchase_id}'),
         InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id, 'vpn_buy_vpn', 'keyboard'), callback_data=f'vpn_set_period_traffic__30_40_{purchase.product_id}')]
    ]
    await send_message_to_user(context, purchase, text, keyboard)


async def report_service_expired_in_days(context, purchase, ft_instance, days_left):
    text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_service_days_notification')
    text = text.format(f"<code>{purchase.username}</code>", days_left)
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id,'vpn_upgrade_service','keyboard'), callback_data=f'vpn_upgrade_service__30__40__{purchase.purchase_id}'),
         InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id,'vpn_view_service_detail','keyboard'), callback_data=f'vpn_my_service_detail__{purchase.purchase_id}')]
    ]
    await send_message_to_user(context, purchase, text, keyboard)


async def report_service_expired_in_gigabyte(context, purchase, ft_instance, percentage_traffic_consumed:int, left_traffic_in_gigabyte):
    left_traffic = await format_traffic_from_megabyte(ft_instance, int(left_traffic_in_gigabyte * 1024), purchase.chat_id)
    text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_service_gigabyte_percent_notification')
    text = text.format(percentage_traffic_consumed, f"<code>{purchase.username}</code>", left_traffic)
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id, 'vpn_upgrade_service', 'keyboard'), callback_data=f'vpn_upgrade_service__30__40__{purchase.purchase_id}'),
         InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id, 'vpn_view_service_detail', 'keyboard'), callback_data=f'vpn_my_service_detail__{purchase.purchase_id}')]
    ]
    await send_message_to_user(context, purchase, text, keyboard)


async def report_service_termination_to_admin(purchase):
    text = ('User service has been terminated'
            f'\n\nservice iD: {purchase.purchase_id}'
            f'\nService Username: {purchase.username}'
            f'\nService Product Name: {purchase.purchase_id}'
            f'\nService Traffic: {purchase.traffic}'
            f'\nService Period Time: {purchase.period}'
            f'\nRegister Date: {human_readable(purchase.register_date, "en")}')
    await report_to_admin('info', 'report_termination', text, purchase.owner)

async def notification_timer(context):
    try:
        with SessionLocal() as session:
            online_users_instance.clear_list()
            all_product = vpn_crud.get_all_product(session)
            ft_instanc = FindText(None, None)

            for product in all_product:
                get_users_usage = await panel_api.marzban_api.get_users(product.main_server.server_ip)
                for purchase in product.purchase:
                    if purchase.status != 'active': continue
                    for user in get_users_usage['users']:
                        if user['username'] == purchase.username:
                            usage_traffic_in_gigabyte = round(user['used_traffic'] / (1024 ** 3), 2)
                            data_limit_in_gigabyte = round(user['data_limit'] / (1024 ** 3), 2)
                            traffic_left_in_gigabyte = data_limit_in_gigabyte - usage_traffic_in_gigabyte
                            traffic_percent = int((usage_traffic_in_gigabyte / data_limit_in_gigabyte) * 100)
                            service_stauts = user['status']

                            expiry = datetime.fromtimestamp(user['expire'])
                            now = datetime.now(pytz.timezone('Asia/Tehran')).replace(tzinfo=None)
                            days_left = (expiry - now).days

                            if service_stauts in ['limited', 'expired'] and purchase.status == 'active':
                                vpn_crud.update_purchase(session, purchase.purchase_id, status=service_stauts)
                                session.commit()
                                await report_service_termination_to_user(context, purchase, ft_instanc)
                                await report_service_termination_to_admin(purchase)

                            elif days_left <= purchase.owner.config.period_notification_day and not purchase.day_notification_status:
                                vpn_crud.update_purchase(session, purchase.purchase_id, day_notification_status=True)
                                session.commit()
                                await report_service_expired_in_days(context, purchase, ft_instanc, days_left)

                            elif traffic_percent >= purchase.owner.config.traffic_notification_percent and not purchase.traffic_notification_status:
                                vpn_crud.update_purchase(
                                    session, purchase.purchase_id,
                                    traffic_notification_status=True,
                                    expired_at=datetime.now()
                                )
                                await report_service_expired_in_gigabyte(
                                    context,
                                    purchase,
                                    ft_instanc,
                                    traffic_percent,
                                    traffic_left_in_gigabyte
                                )

                            if user.get('online_at'):
                                online_at = datetime.fromisoformat(user.get('online_at')).replace(microsecond=0)
                                now = datetime.now()
                                if (now - online_at).total_seconds() < 60:
                                    online_users_instance.add_user([user['username'], purchase.purchase_id])
            session.commit()

    except Exception as e:
        tb = traceback.format_exc()
        msg = ('error in statistics-timer!'
               f'\n\nerror type: {type(e)}'
               f'\nTraceBack:\n{tb}')
        await report_to_admin('error', 'statistics_timer', msg)


async def remove_inactive_purchase(context, session):
    inactive_purchases = vpn_crud.get_all_inactive_purchase(session)
    for purchase in inactive_purchases:
        try:
            expired_at = purchase.expired_at or datetime(year=2000, month=2, day=1)
            days_past_after_expired = (datetime.now() - expired_at).days

            if days_past_after_expired >= setting.delete_purchase_after_days:
                remove_purchase = vpn_crud.remove_purchase(session, purchase.purchase_id, purchase.chat_id)
                session.commit()
                await vpn_utilities.remove_service_in_server(session, remove_purchase)
                ft_instance = FindText(None, None)
                text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_expired_service_deleted')
                text = text.format(purchase.purchase_id)
                await context.bot.send_message(chat_id=purchase.chat_id, text=text)

        except Exception as e:
            tb = traceback.format_exc()
            msg = ('Failed to remove user expired service!'
                   f'\nService ID: {purchase.purchase_id}'
                   f'\nService username: {purchase.username}'
                   f'\n\nerror:\n{str(e)}'
                   f'\nTraceBack:\n{tb}')
            await report_to_admin('error', 'tasks_schedule', msg, purchase.owner)


async def tasks_schedule(context):
    with SessionLocal() as session:
        panel_api.marzban_api.refresh_connection()
        await statistics.aggregate_daily_usage()
        await remove_inactive_purchase(context, session)