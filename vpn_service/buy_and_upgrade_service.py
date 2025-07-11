import logging, copy, uuid
import random
from _datetime import datetime, timedelta
import pytz, sys, os, qrcode, string
from io import BytesIO
import requests.exceptions
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import utilities_reFactore
from WebApp.WebAppDialogue import transaction
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, message_token, handle_error, report_to_admin
from crud import vpn_crud, crud
from vpn_service import panel_api, vpn_utilities
from database_sqlalchemy import SessionLocal
from setting import tenth_servers_limit_gb


@handle_error.handle_functions_error
@message_token.check_token
async def buy_custom_service(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    period_callback, traffic_callback, product_id = query.data.replace('vpn_set_period_traffic__', '').split('_')
    user_detail = update.effective_chat

    traffic = max(min(int(traffic_callback), 150), 5) or 40
    period = max(min(int(period_callback), 60), 5) or 30

    with SessionLocal() as session:

        limits = [(30, 40), (60, 60), (90, 90)]
        if any(traffic >= gb and period <= days for gb, days in limits):
            tenth_servers = f"\n\n{(await ft_instance.find_text('vpn_tenth_server_info'))}"
        else:
            traffic_require = next(
                (gb for gb, days in limits if period <= days), 30
            )
            tenth_servers = f"\n\n{(await ft_instance.find_text('vpn_tenth_require')).format(traffic_require)}"

        price = await vpn_utilities.calculate_price(traffic, period, user_detail.id, session)
        text = (f"{await ft_instance.find_text('vpn_buy_service_title')}"
                f"{tenth_servers}"
                f"\n\n{await ft_instance.find_text('price')} {price:,} {await ft_instance.find_text('irt')}")

        keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_traffic_lable'), callback_data="just_for_show")],
            [InlineKeyboardButton("➖", callback_data=f"vpn_set_period_traffic__{period}_{traffic - 5}_{product_id}"),
             InlineKeyboardButton(f"{traffic} {await ft_instance.find_keyboard('gb_lable')}", callback_data="just_for_show"),
             InlineKeyboardButton("➕", callback_data=f"vpn_set_period_traffic__{period}_{traffic + 10}_{product_id}")],
            [InlineKeyboardButton(await ft_instance.find_keyboard('period_traffic_lable'), callback_data="just_for_show")],
            [InlineKeyboardButton("➖", callback_data=f"vpn_set_period_traffic__{period - 5}_{traffic}_{product_id}"),
             InlineKeyboardButton(f"{period} {await ft_instance.find_keyboard('day_lable')}", callback_data="just_for_show"),
             InlineKeyboardButton("➕", callback_data=f"vpn_set_period_traffic__{period + 10}_{traffic}_{product_id}")],
            [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='menu_services'),
             InlineKeyboardButton(await ft_instance.find_keyboard('confirm'), callback_data=f"create_invoice__buy_vpn_service__{period}__{traffic}__{product_id}")]
        ]

        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def upgrade_service(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    period_callback, traffic_callback, purchase_id = query.data.replace('vpn_upgrade_service__', '').split('__')
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():

            purchase = vpn_crud.get_purchase(session, purchase_id)
            if not purchase:
                return await query.answer(await ft_instance.find_text('this_service_is_not_available'), show_alert=True)

            traffic = max(min(int(traffic_callback), 150), 5) or 40
            period = max(min(int(period_callback), 60), 5) or 30

            price = await vpn_utilities.calculate_price(traffic, period, user_detail.id, session)

            limits = [(30, 40), (60, 60), (90, 90)]
            if any(traffic >= gb and period <= days for gb, days in limits):
                tenth_servers = f"\n\n{(await ft_instance.find_text('vpn_tenth_server_info'))}"
            else:
                traffic_require = next(
                    (gb for gb, days in limits if period <= days), 30
                )
                tenth_servers = f"\n\n{(await ft_instance.find_text('vpn_tenth_require')).format(traffic_require)}"

            text = (f"{await ft_instance.find_text('vpn_upgrade_service_title')}"
                    f"{tenth_servers}"
                    f"\n\n{await ft_instance.find_text('price')} {price:,} {await ft_instance.find_text('irt')}")

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_traffic_lable'), callback_data="just_for_show")],
                [InlineKeyboardButton("➖", callback_data=f"vpn_upgrade_service__{period}__{traffic - 5}__{purchase_id}"),
                 InlineKeyboardButton(f"{traffic} {await ft_instance.find_keyboard('gb_lable')}", callback_data="just_for_show"),
                 InlineKeyboardButton("➕", callback_data=f"vpn_upgrade_service__{period}__{traffic + 10}__{purchase_id}")],
                [InlineKeyboardButton(await ft_instance.find_keyboard('period_traffic_lable'), callback_data="just_for_show")],
                [InlineKeyboardButton("➖", callback_data=f"vpn_upgrade_service__{period - 5}__{traffic}__{purchase_id}"),
                 InlineKeyboardButton(f"{period} {await ft_instance.find_keyboard('day_lable')}", callback_data="just_for_show"),
                 InlineKeyboardButton("➕", callback_data=f"vpn_upgrade_service__{period + 10}__{traffic}__{purchase_id}")],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vpn_my_service_detail__{purchase_id}'),
                 InlineKeyboardButton(await ft_instance.find_keyboard('confirm'), callback_data=f"create_invoice__upgrade_vpn_service__{period}__{traffic}__{purchase_id}")]
            ]

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

async def create_json_config(username, expiration_in_day, traffic_in_byte, service_uuid, org_traffic, status="active"):
    now = datetime.now(pytz.timezone('Asia/Tehran'))
    date_time_stamp = (now + timedelta(days=expiration_in_day)).timestamp()

    config = {
        "username": username,
        "proxies": {
            "vless": {
                "id": service_uuid
            },
            "vmess": {
                "id": service_uuid
            },
            "trojan": {
                "password": service_uuid
            },
            "shadowsocks": {
                "password": service_uuid
            },
        },
        "inbounds": {
            "vless": [
                "VLESS TCP",
                "VLESS TCP REALITY",
                "VLESS GRPC REALITY"
            ],
            "vmess": [
                "VMess TCP",
                "VMess Websocket",
            ],
            "trojan": [
                "Trojan Websocket TLS",
            ],
            "shadowsocks": [
                "Shadowsocks TCP 2"
            ],
        },
        "expire": int(date_time_stamp),
        "data_limit": traffic_in_byte,
        "data_limit_reset_strategy": "no_reset",
        "status": status,
        "note": "",
        "on_hold_timeout": "2023-11-03T20:30:00",
        "on_hold_expire_duration": 0
    }

    limits = [(30, 40), (60, 60), (90, 90)]
    if any(org_traffic >= gb * 1024 ** 3 and expiration_in_day <= days for gb, days in limits) or org_traffic >= 90 * 1024 ** 3:
        config["inbounds"]["shadowsocks"].append("Shadowsocks TCP")

    return config

async def create_service_in_servers(session, purchase_id: int):
    get_purchase = vpn_crud.get_purchase(session, purchase_id)

    if not get_purchase:
        raise ValueError('Purchase is empty!')

    username = (
        f"{get_purchase.purchase_id}_"
        f"{''.join(random.choices(string.ascii_lowercase, k=3))}"
    )

    traffic_to_byte = int(get_purchase.traffic * 1024 ** 3)
    service_uuid = uuid.uuid4().hex

    json_config = await create_json_config(username, get_purchase.period, traffic_to_byte, service_uuid=service_uuid, org_traffic=traffic_to_byte)
    create_user = await panel_api.marzban_api.add_user(get_purchase.product.main_server.server_ip, json_config)

    vpn_crud.update_purchase(
        session, purchase_id,
        username=username,
        subscription_url=create_user['subscription_url'],
        status='active',
        register_date=datetime.now(pytz.timezone('Asia/Tehran')),
        service_uuid=service_uuid
    )
    session.refresh(get_purchase)
    return get_purchase

async def create_service_for_user(context, session, purchase_id: int):
    get_purchase = await create_service_in_servers(session, purchase_id)

    ft_instance = FindText(None, None)
    main_server = get_purchase.product.main_server

    server_port = f":{main_server.server_port}" if main_server.server_port != 443 else ""
    sub_link = f"{main_server.server_protocol}{main_server.server_ip}{server_port}{get_purchase.subscription_url}"

    qr_code = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr_code.add_data(sub_link)
    qr_code.make(fit=True)
    qr_image = qr_code.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    qr_image.save(buffer)
    binary_data = buffer.getvalue()

    keyboard = [[InlineKeyboardButton(await ft_instance.find_from_database(get_purchase.chat_id, 'vpn_guide_button_label', 'keyboard'), callback_data=f"vpn_guide_menu_in_new_message"),
                 InlineKeyboardButton(await ft_instance.find_from_database(get_purchase.chat_id, 'my_services', 'keyboard'), callback_data=f"vpn_my_services_new__1")],
                [InlineKeyboardButton(await ft_instance.find_from_database(get_purchase.chat_id,'bot_main_menu', 'keyboard'), callback_data=f"start_in_new_message")]]

    service_activated_text = (await ft_instance.find_from_database(get_purchase.chat_id, 'vpn_service_activated')).format(get_purchase.username)

    if get_purchase.traffic >= tenth_servers_limit_gb:
        service_activated_text += await ft_instance.find_from_database(get_purchase.chat_id, 'vpn_service_activated_unlimited_server')

    text = (f'{service_activated_text}'
            f'\n\n<code>{sub_link}</code>')

    await context.bot.send_photo(photo=binary_data,
                                 caption= text,
                                 chat_id=get_purchase.chat_id, reply_markup=InlineKeyboardMarkup(keyboard),
                                 parse_mode='html')
    return get_purchase


async def upgrade_service_for_user(context, session, purchase_id: int):
    purchase = vpn_crud.get_purchase(session, purchase_id)
    traffic_for_upgrade = copy.deepcopy(purchase.upgrade_traffic)
    period_for_upgrade = copy.deepcopy(purchase.upgrade_period)

    if not purchase.upgrade_traffic or not purchase.upgrade_period:
        raise ValueError('upgrade_traffic or upgrade_period is empty')

    ft_instance = FindText(None, None)
    main_server_ip = purchase.product.main_server.server_ip
    try:

        await panel_api.marzban_api.reset_user_data_usage(main_server_ip, purchase.username)
        traffic_to_byte = int(purchase.upgrade_traffic * (1024 ** 3))
        new_period, new_traffic = purchase.upgrade_period, purchase.upgrade_traffic

        json_config = await create_json_config(
            purchase.username, purchase.upgrade_period, traffic_to_byte,
            org_traffic= int(purchase.upgrade_traffic * 1024 ** 3),
            service_uuid=purchase.service_uuid if purchase.service_uuid else uuid.uuid4().hex
        )
        await panel_api.marzban_api.modify_user(main_server_ip, purchase.username, json_config)

        success_text = await ft_instance.find_from_database(purchase.chat_id, 'upgrade_service_successfuly')
        success_text = success_text.format(purchase.purchase_id, purchase.upgrade_traffic, purchase.upgrade_period)

        vpn_crud.update_purchase(
            session,
            purchase_id,
            traffic=new_traffic,
            period=new_period,
            upgrade_traffic=0,
            upgrade_period=0,
            status='active',
            register_date=datetime.now(pytz.timezone('Asia/Tehran')),
            expired_at=None,
            day_notification_status=False,
            traffic_notification_status=False,
            traffic_notification_status_2=False
        )

        session.refresh(purchase)
        await context.bot.send_message(text=success_text, chat_id=purchase.chat_id)
        return purchase, traffic_for_upgrade, period_for_upgrade

    except Exception as e:
        await handle_http_error(purchase, main_server_ip, purchase_id, e)


async def handle_http_error(purchase, main_server_ip, purchase_id, original_error):
    """
    Handles HTTP errors during the upgrade process and attempts to deactivate the user's service.
    """
    try:
        traffic_to_byte = int(purchase.traffic * (1024 ** 3))
        expire_date = purchase.register_date + timedelta(days=purchase.period)
        now = datetime.now(pytz.timezone('Asia/Tehran'))
        days_since_expiration = (now - expire_date).days
        json_config = await create_json_config(purchase.username, days_since_expiration, traffic_to_byte, org_traffic=traffic_to_byte, service_uuid=purchase.service_uuid)
        await panel_api.marzban_api.modify_user(main_server_ip, purchase.username, json_config)

        logging.error(f'rollback user service!\n{str(e)}\nid: {purchase_id}')
        error_message = (
            f'rollback user service after HTTP error in upgrade!'
            f'\nService username: {purchase.username}'
            f'\nService ID: {purchase_id}'
        )
        await report_to_admin('error', 'handle_http_error', error_message, purchase.owner)
    except requests.exceptions.HTTPError as e:
        logging.error(f'failed to rollback user service!\n{str(e)}\nid: {purchase_id}')
        error_message = (
            f'Failed to rollback user service after HTTP error in upgrade!'
            f'\nService username: {purchase.username}'
            f'\nService ID: {purchase_id}'
        )
        await report_to_admin('error', 'upgrade_service_for_user', error_message, purchase.owner)
        raise e from original_error

    raise original_error


@handle_error.handle_functions_error
@message_token.check_token
async def recive_test_service_info(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    traffic, period, product_id = 1, 7, 1
    user = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            config = crud.get_user_config(session, user.id)

            if config.get_vpn_free_service:
                text = f"{await ft_instance.find_text('vpn_you_already_recive_this_service')}"
                return await query.answer(text=text)

            text = f"{await ft_instance.find_text('vpn_ask_user_for_revoke_service')}"
            # text = text.format(traffic, period)

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('recive_service'), callback_data=f'vpn_recive_test__{traffic}__{period}__{product_id}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='menu_services')]
            ]

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def recive_test_service(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user = update.effective_chat
    traffic, period, product_id = query.data.replace('vpn_recive_test__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            config = crud.get_user_config(session, user.id)

            if config.get_vpn_free_service:
                text = f"{await ft_instance.find_text('vpn_you_already_recive_this_service')}"
                return await query.answer(text=text)

            purchase = crud.create_purchase(session, product_id, user.id, traffic, period)
            service_id = purchase.purchase_id
            await create_service_for_user(context, session, service_id)
            crud.update_user_config(session, user.id, get_vpn_free_service=True)

            admin_msg = ('User Received Test Service.'
                         f'\nService ID: {purchase.purchase_id}'
                         f'\nService Username: {purchase.username}')

            await report_to_admin('info', 'recive_test_service', admin_msg, purchase.owner)

    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='menu_services')]]
    await query.edit_message_text(text=await ft_instance.find_text('operation_successful'), reply_markup=InlineKeyboardMarkup(keyboard))