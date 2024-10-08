import sys, os, pytz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import setting
from vpn_service import panel_api
from datetime import datetime, timedelta
from crud import crud
from admin import partner

async def calculate_price(traffic, period, chat_id):
    price_per_gigabyte = setting.PRICE_PER_GB
    price_per_day = setting.PRICE_PER_DAY

    if chat_id in partner.partners.list_of_partner:
        price_per_gigabyte = partner.partners.list_of_partner[chat_id].vpn_price_per_gigabyte_irt
        price_per_day = partner.partners.list_of_partner[chat_id].vpn_price_per_period_time_irt

    price = (int(traffic) * price_per_gigabyte) + (int(period) * price_per_day)
    return int(price)


async def format_traffic_from_megabyte(ft_instance, traffic_in_megabyte):
    if traffic_in_megabyte == 0:
        return await ft_instance.find_text('without_usage')
    elif int(traffic_in_megabyte) < 1000:
        return f"{int(traffic_in_megabyte)} {await ft_instance.find_text('megabyte')}"
    else:
        return f"{round(traffic_in_megabyte / 1000, 2)} {await ft_instance.find_text('gigabyte')}"


async def remove_service_in_server(session, purchase):
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