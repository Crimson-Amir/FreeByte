import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import setting
from vpn_service import panel_api
from datetime import datetime, timedelta

async def calculate_price(traffic, period):
    price = (traffic * setting.PRICE_PER_GB) + (period * setting.PRICE_PER_DAY)
    return int(price)


async def format_traffic_from_megabyte(ft_instance, traffic_in_megabyte):
    if traffic_in_megabyte == 0:
        return await ft_instance.find_text('without_usage')
    elif int(traffic_in_megabyte) < 1000:
        return f"{int(traffic_in_megabyte)} {await ft_instance.find_text('megabyte')}"
    else:
        return f"{round(traffic_in_megabyte / 1000, 2)} {await ft_instance.find_text('gigabyte')}"