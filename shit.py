import requests
from bs4 import BeautifulSoup
import re
import models_sqlalchemy as model
from database_sqlalchemy import SessionLocal
from crud import crud, admin_crud, vpn_crud

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}

with SessionLocal() as session:
    with session.begin():
        all_purchase = session.query(model.Purchase).filter(model.Purchase.subscription_url.isnot(None)).all()
        for purchase in all_purchase:
            url = 'https://api.freebyte.click' + purchase.subscription_url if 'https://api.freebyte.click' not in purchase.subscription_url else purchase.subscription_url

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                html_content = response.text

                soup = BeautifulSoup(html_content, "html.parser")

                first_config_input = soup.find("input", {"value": re.compile(r"vless://.*")})
                if first_config_input:
                    config_link = first_config_input['value']

                    match = re.search(r"vless://([a-f0-9\-]+)@", config_link)
                    if match:
                        uuid = match.group(1)
                        if uuid == '2':
                            continue
                        vpn_crud.update_purchase(session, purchase.purchase_id, service_uuid = uuid)
                    else:
                        print("1")
                else:
                    print("2")
            else:
                print("3")