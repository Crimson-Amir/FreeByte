import logging
from _datetime import datetime, timedelta
import pytz, uuid, sys, os, hashlib, qrcode
from io import BytesIO
import requests.exceptions
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import utilities_reFactore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, message_token, handle_error, report_to_admin
from crud import vpn_crud, crud
from vpn_service import panel_api, vpn_utilities
from database_sqlalchemy import SessionLocal


@handle_error.handle_functions_error
@message_token.check_token
async def buy_custom_service(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    period_callback, traffic_callback = query.data.replace('vpn_set_period_traffic__', '').split('_')

    traffic = max(min(int(traffic_callback), 150), 5) or 40
    period = max(min(int(period_callback), 60), 5) or 30

    price = await vpn_utilities.calculate_price(traffic, period)
    text = (f"{await ft_instance.find_text('vpn_buy_service_title')}"
            f"\n\n{await ft_instance.find_text('price')} {price:,} {await ft_instance.find_text('irt')}")

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_traffic_lable'), callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"vpn_set_period_traffic__{period}_{traffic - 5}"),
         InlineKeyboardButton(f"{traffic} {await ft_instance.find_keyboard('gb_lable')}", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"vpn_set_period_traffic__{period}_{traffic + 10}")],
        [InlineKeyboardButton(await ft_instance.find_keyboard('period_traffic_lable'), callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"vpn_set_period_traffic__{period - 5}_{traffic}"),
         InlineKeyboardButton(f"{period} {await ft_instance.find_keyboard('day_lable')}", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"vpn_set_period_traffic__{period + 10}_{traffic}")],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='menu_services'),
         InlineKeyboardButton(await ft_instance.find_keyboard('confirm'), callback_data=f"create_invoice__buy_vpn_service__{period}__{traffic}")]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def upgrade_service(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    period_callback, traffic_callback, purchase_id = query.data.replace('vpn_upgrade_service__', '').split('__')

    with SessionLocal() as session:
        with session.begin():

            traffic = max(min(int(traffic_callback), 150), 5) or 40
            period = max(min(int(period_callback), 60), 5) or 30

            price = await vpn_utilities.calculate_price(traffic, period)

            text = (f"{await ft_instance.find_text('vpn_upgrade_service_title')}"
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

async def create_json_config(username, expiration_in_day, traffic_in_byte, status="active"):
    return {
        "username": username,
        "proxies": {
            "vless": {}
        },
        "inbounds": {
            "vless": [
                "VLESS TCP"
            ]
        },
        "expire": expiration_in_day,
        "data_limit": traffic_in_byte,
        "data_limit_reset_strategy": "no_reset",
        "status": status,
        "note": "",
        "on_hold_timeout": "2023-11-03T20:30:00",
        "on_hold_expire_duration": 0
    }


async def create_service_in_servers(session, purchase_id: int):
    get_purchase = vpn_crud.get_purchase(session, purchase_id)

    if not get_purchase:
        raise ValueError('Purchase is empty!')

    username = (
        f"{get_purchase.purchase_id}_"
        f"{hashlib.sha256(f'{get_purchase.chat_id}.{uuid.uuid4().hex}'.encode()).hexdigest()[:5]}"
    )

    traffic_to_byte = int(get_purchase.traffic * (1024 ** 3))
    now = datetime.now(pytz.timezone('Asia/Tehran'))
    date_in_timestamp = (now + timedelta(days=get_purchase.period)).timestamp()

    json_config = await create_json_config(username, date_in_timestamp, traffic_to_byte)
    create_user = await panel_api.marzban_api.add_user(get_purchase.product.main_server.server_ip, json_config)

    vpn_crud.update_purchase(session, purchase_id, username=username, subscription_url=create_user['subscription_url'], status='active')
    session.refresh(get_purchase)
    return get_purchase


async def create_service_for_user(update, context, session, purchase_id: int):
    get_purchase = await create_service_in_servers(session, purchase_id)

    ft_instance = FindText(update, context)
    main_server = get_purchase.product.main_server

    server_port = f":{main_server.server_port}" if main_server.server_port != 443 else ""
    sub_link = f"<code>{main_server.server_protocol}{main_server.server_ip}{server_port}{get_purchase.subscription_url}</code>"

    qr_code = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=10,border=4)
    qr_code.add_data(sub_link)
    qr_code.make(fit=True)
    qr_image = qr_code.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    qr_image.save(buffer)
    binary_data = buffer.getvalue()

    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('vpn_get_configs'), callback_data=f"vpn_get_configs_separately__{purchase_id}__yes")],
                [InlineKeyboardButton(await ft_instance.find_keyboard('my_services'), callback_data=f"vpn_my_services_new")],
                [InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'), callback_data=f"start_in_new_message")]]

    await context.bot.send_photo(photo=binary_data,
                                 caption=await ft_instance.find_text('vpn_service_activated') + f'\n\n{sub_link}',
                                 chat_id=get_purchase.chat_id, reply_markup=InlineKeyboardMarkup(keyboard),
                                 parse_mode='html')
    return get_purchase

async def upgrade_service_for_user(update, context, session, purchase_id: int):
    purchase = vpn_crud.get_purchase(session, purchase_id)

    if not purchase.upgrade_traffic or not purchase.upgrade_period:
        raise ValueError('upgrade_traffic or upgrade_period is empty')

    ft_instance = FindText(update, context)
    main_server_ip = purchase.product.main_server.server_ip

    try:

        if purchase.active:
            user = await panel_api.marzban_api.get_user(main_server_ip, purchase.username)
            traffic_to_byte = int((purchase.upgrade_traffic * (1024 ** 3)) + user['data_limit'])
            expire_date = datetime.fromtimestamp(user['expire'])
        else:
            await panel_api.marzban_api.reset_user_data_usage(main_server_ip, purchase.username)
            traffic_to_byte = int(purchase.upgrade_traffic * (1024 ** 3))
            expire_date = datetime.now(pytz.timezone('Asia/Tehran'))

        date_in_timestamp = (expire_date + timedelta(days=purchase.upgrade_period)).timestamp()

        json_config = await create_json_config(purchase.username, date_in_timestamp, traffic_to_byte)
        await panel_api.marzban_api.modify_user(main_server_ip, purchase.username, json_config)

        vpn_crud.update_purchase(
            session,
            purchase_id,
            traffic=purchase.upgrade_traffic,
            period=purchase.upgrade_period,
            upgrade_traffic=0,
            upgrade_period=0,
            status='active'
        )

        session.refresh(purchase)

        success_text = await ft_instance.find_text('upgrade_service_successfuly')
        message_text = success_text.format(purchase.username, purchase.upgrade_traffic, purchase.upgrade_period)
        await context.bot.send_message(text=message_text, chat_id=purchase.chat_id)

        return purchase

    except requests.exceptions.HTTPError as http_error:
        await handle_http_error(purchase, main_server_ip, purchase_id, http_error)


async def handle_http_error(purchase, main_server_ip, purchase_id, original_error: requests.exceptions.HTTPError):
    """
    Handles HTTP errors during the upgrade process and attempts to deactivate the user's service.
    """
    try:
        traffic_to_byte = int(purchase.traffic * (1024 ** 3))
        expire_date = purchase.register_date
        date_in_timestamp = (expire_date + timedelta(days=purchase.period)).timestamp()
        json_config = await create_json_config(purchase.username, date_in_timestamp, traffic_to_byte)
        await panel_api.marzban_api.modify_user(main_server_ip, purchase.username, json_config)
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

            text = f"{await ft_instance.find_text('vpn_test_sevice_test')}"
            text = text.format(traffic, period)

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
            await create_service_for_user(update, context, session, service_id)
            crud.update_user_config(session, user.id, get_vpn_free_service=True)

            admin_msg = ('User Recived Test Service.'
                         f'\nService ID: {purchase.purchase_id}'
                         f'\nService Username: {purchase.username}')

            await utilities_reFactore.report_to_admin('info', 'recive_test_service', admin_msg, purchase.owner)

    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='menu_services')]]
    await query.edit_message_text(text=await ft_instance.find_text('operation_successful'), reply_markup=InlineKeyboardMarkup(keyboard))