import requests, logging
from datetime import datetime, timedelta
usd_default_price = 60_000

price = {}

def get_from_api():
    url = 'https://api.nobitex.ir/market/stats'
    headers = {'UserAgent': 'TraderBot/FreeByte'}
    response = requests.post(url, headers=headers, data={'srcCurrency': "usdt", 'dstCurrency': "rls"})
    response.raise_for_status()
    response_json = response.json()
    return int(response_json.get('stats', {}).get('usdt-rls', {}).get('bestSell', usd_default_price * 10)) / 10

def get_tether_price():
    if price.get('tether_price'):
        register_date = price.get('tether_price').get('register_date')
        if register_date + timedelta(hours=12) < datetime.now():
            get_price = get_from_api()
            price['tether_price'] = {'price': get_price, 'register_date': datetime.now()}
        return price['tether_price']['price']
    else:
        get_price = get_from_api()
        price['tether_price'] = {'price': get_price, 'register_date': datetime.now()}
        return price['tether_price']['price']

def convert_irt_to_usd(irt_value: int):
    try:
        usd_in_irt = get_tether_price()
        return int(irt_value / usd_in_irt)

    except Exception as e:
        logging.error(f'Error in get teter price.\n{e}')
        return int(irt_value / usd_default_price)


def convert_usd_to_irt(usd_value: float):
    try:
        usd_in_irt = get_tether_price()
        return int(usd_value * usd_in_irt)

    except Exception as e:
        logging.error(f'Error in get teter price.\n{e}')
        return int(usd_value * usd_default_price)

