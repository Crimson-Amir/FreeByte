import sys, os, math, pprint
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import admin_crud
from database_sqlalchemy import SessionLocal
from utilities_reFactore import human_readable, format_traffic_from_byte
from vpn_service import vpn_utilities, panel_api, vpn_notification

GET_NEW_HOST_CONFIG = 0

service_status = {
    True: '✅',
    'limited': '🟡',
    False: '🔴'
}

@vpn_utilities.handle_functions_error
@admin_access
async def all_products(update, context):
    query = update.callback_query
    item_per_page = 15
    page = int(query.data.split('__')[1]) if query and query.data.startswith('admin_system') else 1

    with SessionLocal() as session:
        with session.begin():
            products = admin_crud.get_all_products(session)
            total_pages = math.ceil(len(products) / item_per_page)
            start = (page - 1) * item_per_page
            end = start + item_per_page
            current_products = products[start:end]
            text = 'select Product to manage:'

            keyboard = [[InlineKeyboardButton('Online Users', callback_data=f'admin_view_online_users__1__{page}')]]
            product_keyboard = [[InlineKeyboardButton(f"{product.product_id} {product.product_name} {service_status.get(product.active)}", callback_data=f'admin_view_product__{product.product_id}__{page}')] for product in current_products]
            keyboard.extend(product_keyboard)

            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton('<- previous', callback_data=f'admin_system__{page - 1}'))
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton('next ->', callback_data=f'admin_system__{page + 1}'))
            if nav_buttons: keyboard.append(nav_buttons)

            keyboard.append([InlineKeyboardButton('Back', callback_data='admin_page')])

            return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_view_online_users(update, context):
    query = update.callback_query
    page, product_page = query.data.replace('admin_view_online_users__', '').split('__')
    page = int(page)
    item_per_page = 15

    online_users = vpn_notification.online_users_instance.online_users

    online_users_count = len(online_users)
    total_pages = math.ceil(online_users_count / item_per_page)

    start = (page - 1) * item_per_page
    end = start + item_per_page
    current_users = online_users[start:end]
    keyboard = [[InlineKeyboardButton(f"{username}", callback_data=f'admin_user_service_detail__{purchase_id}__1__1')] for username, purchase_id in current_users]

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton('<- previous', callback_data=f'admin_view_online_users__{page - 1}__{product_page}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton('next ->', callback_data=f'admin_view_online_users__{page + 1}__{product_page}'))
    if nav_buttons: keyboard.append(nav_buttons)

    text = f'Online Users: {len(online_users)}'
    keyboard.append([InlineKeyboardButton('Refresh', callback_data=f'admin_view_online_users__{page}__{product_page}'),
                    InlineKeyboardButton('Back', callback_data=f'admin_system__{product_page}')])

    return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_view_product(update, context, product_id=None, page=None):
    query = update.callback_query
    product_id, page = product_id, page
    if not product_id:
        product_id, page = query.data.replace('admin_view_product__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            product = admin_crud.get_product(session, int(product_id))

            text = (
                f'Product ID: {product.product_id}'
                f'\nName: {product.product_name}'
                f'\nMain Server ID: {product.main_server_id}'
                f'\nMain Server IP: {product.main_server.server_ip}'
                f'\nMain Server Protocol: {product.main_server.server_protocol}'
                f'\nMain Server Port: {product.main_server.server_port}'
                f'\nStatus: {product.active}'
                f'\nRegister Date: {product.register_date} ({human_readable(product.register_date, "en")})'
                f'\nAll Purchase: {len(product.purchase)}'
                f'\nActive Purchase: {len([purchase for purchase in product.purchase if purchase.status == "active" and purchase.active == True])}'
            )

            keyboard = [
                [InlineKeyboardButton('Node Usage', callback_data=f'admin_node_usage__{product_id}__{page}')],
                [InlineKeyboardButton('Refresh', callback_data=f'admin_view_product__{product_id}__{page}'),
                 InlineKeyboardButton('Xray Core', callback_data=f'admin_view_core__{product_id}__{page}')],
                [InlineKeyboardButton('🔰 Set Product Status:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"Active", callback_data=f'admin_set_product_status__{product_id}__true__{page}'),
                 InlineKeyboardButton(f"Deactive", callback_data=f'admin_set_product_status__{product_id}__false__{page}')],
                [InlineKeyboardButton('View Main Server Info', callback_data=f'admin_product_main_server_info__{product_id}__{page}')],
                [InlineKeyboardButton('Back', callback_data=f'admin_system__{page}')]
            ]

            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def view_product_node_usage(update, context):
    query = update.callback_query
    product_id, page = query.data.replace('admin_node_usage__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            product = admin_crud.get_product(session, int(product_id))
            nodes = await panel_api.marzban_api.get_nodes_usage(product.main_server.server_ip)
            text = 'Node Usage:'

            for node in nodes.get('usages', []):
                total_usage = format_traffic_from_byte(node.get("uplink", 0) + node.get("downlink", 0))
                text += (f'\n\n{node.get("node_id")} - {node.get("node_name")}: {total_usage}GB'
                         f'\nUpLink: {format_traffic_from_byte(node.get("uplink", 0))}GB'
                         f'\nDownLink: {format_traffic_from_byte(node.get("downlink", 0))}GB')

            keyboard = [
                 [InlineKeyboardButton('Refresh', callback_data=f'admin_node_usage__{product_id}__{page}'),
                  InlineKeyboardButton('Back', callback_data=f'admin_view_product__{product_id}__{page}')]
            ]

            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))



@vpn_utilities.handle_functions_error
@admin_access
async def admin_change_product_status(update, context):
    query = update.callback_query
    product_id, status, page = query.data.replace('admin_set_product_status__', '').split('__')
    status = status == 'true'

    with SessionLocal() as session:
        with session.begin():
            admin_crud.update_product(session, int(product_id), active=status)
            await query.answer('+ Changes Saved!')
            return await admin_view_product(update, context, product_id=product_id, page=page)


@vpn_utilities.handle_functions_error
@admin_access
async def admin_xray_core(update, context):
    query = update.callback_query
    product_id, page = query.data.replace('admin_view_core__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            product = admin_crud.get_product(session, int(product_id))
            get_state = await panel_api.marzban_api.get_core_stats(product.main_server.server_ip)
            text = (f'Version: {get_state.get("version")}'
                    f'\nStarted: {get_state.get("started")}')
            keyboard = [
                [InlineKeyboardButton('Restart Core', callback_data=f'admin_restart_core__{product_id}')],
                [InlineKeyboardButton('Refresh', callback_data=f'admin_view_core__{product_id}__{page}'),
                InlineKeyboardButton('Back', callback_data=f'admin_view_product__{product_id}__{page}')]
            ]
            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_restart_xray_core(update, context):
    query = update.callback_query
    product_id = int(query.data.replace('admin_restart_core__', ''))

    with SessionLocal() as session:
        with session.begin():
            product = admin_crud.get_product(session, int(product_id))
            await panel_api.marzban_api.restart_core(product.main_server.server_ip)
            await query.answer('+ Done!')


@vpn_utilities.handle_functions_error
@admin_access
async def view_product_main_server_info(update, context):
    query = update.callback_query
    product_id, page = query.data.replace('admin_product_main_server_info__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            product = admin_crud.get_product(session, int(product_id))
            system = await panel_api.marzban_api.get_system_stats(product.main_server.server_ip)

            text = (
                f'Version: {system.get("version")}'
                f'\nMemory Total: {format_traffic_from_byte(system.get("mem_total"))} GB'
                f'\nMemory Used: {format_traffic_from_byte(system.get("mem_used"))} GB'
                f'\nCPU cores: {system.get("cpu_cores")}'
                f'\nCPU Usage: {system.get("cpu_usage")} %'
                f'\nTotal User: {system.get("total_user")}'
                f'\nActive Users: {system.get("users_active")}'
                f'\nIncoming Bandwidth: {format_traffic_from_byte(system.get("incoming_bandwidth"))} GB'
                f'\nOutgoing Bandwidth: {format_traffic_from_byte(system.get("outgoing_bandwidth"))} GB'
                f'\nIncoming Bandwidth Speed: {format_traffic_from_byte(system.get("incoming_bandwidth_speed"))} GB'
                f'\nOutgoing Bandwidth Speed: {format_traffic_from_byte(system.get("outgoing_bandwidth_speed"))} GB'
            )

            keyboard = [
                [InlineKeyboardButton('View Host', callback_data=f'admin_view_host__{product_id}__{page}'),
                 InlineKeyboardButton('View Inbounds', callback_data=f'admin_view_inbounds__{product_id}__{page}')],
                [InlineKeyboardButton('Refresh', callback_data=f'admin_product_main_server_info__{product_id}__{page}'),
                 InlineKeyboardButton('Back', callback_data=f'admin_view_product__{product_id}__{page}')]
            ]

            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

@admin_access
async def admin_view_host(update, context):
    query = update.callback_query
    product_id, page = query.data.replace('admin_view_host__', '').split('__')

    with SessionLocal() as session:
        get_product = admin_crud.get_product(session, product_id)
        get_host = await panel_api.marzban_api.get_host(get_product.main_server.server_ip)
        prettify = pprint.pformat(get_host)

        keyboard = [
            [InlineKeyboardButton('Refresh', callback_data=f'admin_view_host__{product_id}__{page}'),
             InlineKeyboardButton('Back', callback_data=f'admin_product_main_server_info__{product_id}__{page}')]
        ]
        return await query.edit_message_text(text=f"{prettify}"[:4096], reply_markup=InlineKeyboardMarkup(keyboard))


@admin_access
async def admin_view_inbounds(update, context):
    query = update.callback_query
    product_id, page = query.data.replace('admin_view_inbounds__', '').split('__')

    with SessionLocal() as session:
        get_product = admin_crud.get_product(session, product_id)
        get_inbounds = await panel_api.marzban_api.get_inbounds(get_product.main_server.server_ip)
        prettify = pprint.pformat(get_inbounds)

        keyboard = [
            [InlineKeyboardButton('Refresh', callback_data=f'admin_view_inbounds__{product_id}__{page}'),
             InlineKeyboardButton('Back', callback_data=f'admin_product_main_server_info__{product_id}__{page}')]
        ]
        return await query.edit_message_text(text=f"{prettify}"[:4096], reply_markup=InlineKeyboardMarkup(keyboard))