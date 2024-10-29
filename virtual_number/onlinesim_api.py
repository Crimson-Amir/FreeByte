import os, sys, requests
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import setting
import asyncio

class OnlineSim:
    def __init__(self, api_key):
        self._api_key = api_key
        self.session = requests.session()

    def make_request(self, method, endpoint, **kwargs):
        """Make an HTTP request and return JSON response."""
        url = f'https://onlinesim.io/api/{endpoint}'
        response = self.session.request(method, url, **kwargs, timeout=10)
        response.raise_for_status()
        return response.json()

    def init_requests(self, endpoint: str, **queris):
        queris.setdefault('lang', 'en')
        queris.update({'apikey': self._api_key})
        parsed_url = urlparse(endpoint)
        url_queris = dict(parse_qsl(parsed_url.query))
        url_queris.update(queris)
        new_queris = urlencode(url_queris)
        new_url = urlunparse(parsed_url._replace(query=new_queris))
        return new_url

    async def get_tariffs(self, **params):
        endpoint = self.init_requests(f"getTariffs.php", **params)
        return self.make_request('get', endpoint)

    async def get_number(self, service_name, country_code, number=True, **params):
        endpoint = self.init_requests(
            "getNum.php", service=service_name, country=country_code, number=number, **params
        )
        return self.make_request('get', endpoint)

    async def get_state(self, **params):
        endpoint = self.init_requests(f"getState.php", **params)
        return self.make_request('get', endpoint)

    async def set_operation_ok(self, **params):
        endpoint = self.init_requests(f"setOperationOk.php", **params)
        return self.make_request('get', endpoint)

    async def get_free_list(self, **params):
        endpoint = self.init_requests(f"getFreeList", **params)
        return self.make_request('get', endpoint)


    async def get_rent_tariffs(self, **params):
        endpoint = self.init_requests(f"tariffsRent.php", **params)
        return self.make_request('get', endpoint)

    async def get_rent_number(self, country_code, days, **params):
        endpoint = self.init_requests(
            "getRentNum.php", country=country_code, days=days, **params
        )
        return self.make_request('get', endpoint)

    async def get_rent_state(self, tzid, **params):
        endpoint = self.init_requests(
            "getRentState.php", tzid=tzid, **params
        )
        return self.make_request('get', endpoint)

    async def extend_rent_state(self, tzid, days, **params):
        endpoint = self.init_requests(
            "extendRentState.php", tzid=tzid, days=days, **params
        )
        return self.make_request('get', endpoint)

    async def close_rent_number(self, tzid, **params):
        endpoint = self.init_requests(
            "closeRentNum.php", tzid=tzid, **params
        )
        return self.make_request('get', endpoint)

    async def get_balance(self, **params):
        endpoint = self.init_requests(
            "getBalance.php", **params
        )
        return self.make_request('get', endpoint)

onlinesim = OnlineSim(setting.onlinesim_api)
