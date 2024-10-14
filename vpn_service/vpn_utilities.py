import sys, os, pytz, functools, logging, traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import setting
from vpn_service import panel_api
from datetime import datetime
from crud import crud
from admin import partner
from utilities_reFactore import find_user
from database_sqlalchemy import SessionLocal

class DiscountPerLevel:
    descount = {
        1: 0,
        2: 4,
        3: 7,
        4: 10,
        5: 15,
        6: 20,
        7: 25,
        8: 30,
        9: 35,
        10: 40
    }

async def calculate_price(traffic, period, chat_id):
    price_per_gigabyte = setting.PRICE_PER_GB
    price_per_day = setting.PRICE_PER_DAY

    with SessionLocal() as session:
        if chat_id in partner.partners.list_of_partner:
            price_per_gigabyte = partner.partners.list_of_partner[chat_id].vpn_price_per_gigabyte_irt
            price_per_day = partner.partners.list_of_partner[chat_id].vpn_price_per_period_time_irt

        service_price = (int(traffic) * price_per_gigabyte) + (int(period) * price_per_day)
        user = await find_user(session, chat_id)
        discount = (service_price * DiscountPerLevel.descount.get(user.config.user_level, 1)) / 100
        price = service_price - discount
        return int(price)


async def format_traffic_from_megabyte(ft_instance, traffic_in_megabyte):
    if traffic_in_megabyte == 0:
        return await ft_instance.find_text('without_usage')
    elif int(traffic_in_megabyte) < 1000:
        return f"{int(traffic_in_megabyte)} {await ft_instance.find_text('megabyte')}"
    else:
        return f"{round(traffic_in_megabyte / 1000, 2)} {await ft_instance.find_text('gigabyte')}"


async def remove_service_in_server(session, purchase, context=None):
    main_server_ip = purchase.product.main_server.server_ip
    user = await panel_api.marzban_api.get_user(main_server_ip, purchase.username)
    returnable_amount = 0

    if user['status'] == 'active':

        usage_traffic_in_gigabyte = round(user['used_traffic'] / (1024 ** 3), 2)
        data_limit_in_gigabyte = round(user['data_limit'] / (1024 ** 3), 2)
        traffic_left_in_gigabyte = data_limit_in_gigabyte - usage_traffic_in_gigabyte

        expiry = datetime.fromtimestamp(user['expire'])
        now = datetime.now(pytz.timezone('Asia/Tehran')).replace(tzinfo=None)
        days_left = (expiry - now).days

        returnable_amount = await calculate_price(traffic_left_in_gigabyte, days_left, purchase.chat_id)

        finacial_report = crud.create_financial_report(
            session, 'recive',
            chat_id=purchase.chat_id,
            amount=returnable_amount,
            action='remove_vpn_service',
            service_id=purchase.purchase_id,
            payment_status='not paid',
            payment_getway='wallet',
            currency='IRT'
        )

        crud.add_credit_to_wallet(session, finacial_report)

    await panel_api.marzban_api.remove_user(main_server_ip, purchase.username)
    return returnable_amount


def handle_functions_error(func):
    @functools.wraps(func)
    async def wrapper(update, context, **kwargs):
        user_detail = update.effective_chat
        try:
            return await func(update, context, **kwargs)
        except Exception as e:
            if 'Message is not modified' in str(e): return await update.callback_query.answer()
            logging.error(f'error in {func.__name__}: {str(e)}')
            tb = traceback.format_exc()
            err = (
                f"🔴 An error occurred in {func.__name__}:"
                f"\n\nerror type:{type(e)}"
                f"\nerror reason: {str(e)}"
                f"\n\nTraceback: \n{tb}"
            )
            await context.bot.send_message(chat_id=user_detail.id, text=err)
    return wrapper