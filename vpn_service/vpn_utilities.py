import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import vpn_setting_menu

async def calculate_price(traffic, period):
    price = (traffic * setting.PRICE_PER_GB) + (period * setting.PRICE_PER_DAY)
    return price