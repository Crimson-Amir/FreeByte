import traceback
from datetime import datetime
import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vpn_service import panel_api, vpn_utilities
from crud import vpn_crud, crud
from utilities_reFactore import FindText, report_to_admin, human_readable
from database_sqlalchemy import SessionLocal

async def report_service_termination_to_user(context, purchase, ft_instance):
    text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_service_termination_notification')
    text = text.format(f"<code>{purchase.username}</code>")
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_upgrade_service'), callback_data=f'vpn_upgrade_service__30__40__{purchase.purchase_id}'),
         InlineKeyboardButton(await ft_instance.find_keyboard('vpn_buy_vpn'), callback_data='vpn_set_period_traffic__30_40')]
    ]
    await context.bot.send_message(purchase.chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


async def report_service_expired_in_days(context, purchase, ft_instance, days_left):
    text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_service_days_notification')
    text = text.format(f"<code>{purchase.username}</code>", days_left)
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id,'vpn_upgrade_service','keyboard'), callback_data=f'vpn_upgrade_service__30__40__{purchase.purchase_id}'),
         InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id,'vpn_view_service_detail','keyboard'), callback_data=f'vpn_my_service_detail__{purchase.purchase_id}')]
    ]
    await context.bot.send_message(purchase.chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


async def report_service_expired_in_gigabyte(context, purchase, ft_instance, percentage_traffic_consumed, left_traffic_in_gigabyte):
    left_traffic = vpn_utilities.format_traffic_from_megabyte(ft_instance, int(left_traffic_in_gigabyte * 1024))
    text = await ft_instance.find_from_database(purchase.chat_id, 'vpn_service_gigabyte_percent_notification')
    text = text.format(percentage_traffic_consumed, f"<code>{purchase.username}</code>", left_traffic)
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id,'vpn_upgrade_service','keyboard'), callback_data=f'vpn_upgrade_service__30__40__{purchase.purchase_id}'),
         InlineKeyboardButton(await ft_instance.find_from_database(purchase.chat_id,'vpn_view_service_detail','keyboard'), callback_data=f'vpn_my_service_detail__{purchase.purchase_id}')]
    ]
    await context.bot.send_message(purchase.chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


async def report_service_termination_to_admin(purchase):
    text = ('User service has been terminated'
            f'\nservice iD: {purchase.purchase_id}'
            f'\nService Username: {purchase.username}'
            f'\nService Product Name: {purchase.purchase_id}'
            f'\nService Traffic: {purchase.traffic}'
            f'\nService Period Time: {purchase.period}'
            f'\nRegister Date: {human_readable(purchase.register_date, "en")}')
    await report_to_admin('info', 'report_termination', text, purchase.owner)

async def notification_timer(context):
    try:
        with SessionLocal() as session:
            with session.begin():
                all_product = vpn_crud.get_all_product(session)
                ft_instanc = FindText(None, None)

                for product in all_product:
                    get_users_usage = await panel_api.marzban_api.get_users(product.main_server.server_ip)
                    for purchase in product.purchase:
                        for user in get_users_usage['users']:
                            if user['username'] == purchase.username:
                                usage_traffic_in_gigabyte = round(user['used_traffic'] / (1024 ** 3), 2)
                                data_limit_in_gigabyte = round(user['data_limit'] / (1024 ** 3), 2)
                                traffic_left_in_gigabyte = data_limit_in_gigabyte - usage_traffic_in_gigabyte
                                traffic_percent = (usage_traffic_in_gigabyte / data_limit_in_gigabyte) * 100
                                service_stauts = user['status']

                                expiry = datetime.fromtimestamp(user['expire'])
                                now = datetime.now(pytz.timezone('Asia/Tehran')).replace(tzinfo=None)
                                days_left = (expiry - now).days

                                if service_stauts == 'limited' and purchase.status == 'active':
                                    await report_service_termination_to_user(context, purchase, ft_instanc)
                                    await report_service_termination_to_admin(purchase)
                                    vpn_crud.update_purchase(session, purchase.purchase_id, active='limited')

                                elif days_left <= purchase.owner.config.period_notification_day:
                                    await report_service_expired_in_days(context, purchase, ft_instanc, days_left)
                                    crud.update_user_config(session, purchase.chat_id, period_notification_day=True)


                                elif traffic_percent >= purchase.owner.config.traffic_notification_percent:
                                    await report_service_expired_in_gigabyte(
                                        context,
                                        purchase,
                                        ft_instanc,
                                        traffic_percent,
                                        traffic_left_in_gigabyte
                                    )
                                    crud.update_user_config(session, purchase.chat_id, traffic_notification_percent=True)


    except Exception as e:
        tb = traceback.format_exc()
        msg = ('error in statistics-timer!'
               f'\n\nerror type: {type(e)}'
               f'\nTraceBack:\n{tb}')
        await report_to_admin('error', 'statistics_timer', msg)