import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import setting
from vpn_service import panel_api
from datetime import datetime, timedelta

async def calculate_price(traffic, period):
    price = (traffic * setting.PRICE_PER_GB) + (period * setting.PRICE_PER_DAY)
    return price


async def get_purchase_info_from_server(context, purchase):
    current_time = datetime.now()
    key = f'service_detail_{purchase.purchase_id}'
    get_from_memory = context.user_data.get(key)

    if get_from_memory is None or 'exp' not in get_from_memory or 'info_from_server' not in get_from_memory:
        get_from_memory = None

    if get_from_memory is None or current_time > datetime.fromtimestamp(get_from_memory['exp']):
        get_from_server = await panel_api.marzban_api.get_user(purchase.product.main_server.server_ip, purchase.username)
        exp = (current_time + timedelta(minutes=10)).timestamp()
        context.user_data[key] = {'info_from_server': get_from_server, 'exp': exp}

    return get_from_memory['info_from_server']
