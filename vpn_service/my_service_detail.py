from _datetime import datetime
import sys, os, math, pytz
import requests.exceptions
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import setting

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, message_token, handle_error, human_readable, report_to_admin, cancel_user as cancel
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
from crud import vpn_crud, crud
from database_sqlalchemy import SessionLocal
from vpn_service import panel_api, vpn_utilities

GET_NEW_USER_CHAT_ID, GET_ASSURNACE = range(2)

@handle_error.handle_functions_error
async def my_services(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    item_per_page = 10
    page = int(query.data.split('__')[1]) if query and query.data.startswith('vpn_my_services') else 1

    with SessionLocal() as session:
        with session.begin():
            purchases = vpn_crud.get_purchase_by_chat_id(session, user_detail.id)

            if not purchases:
                return await query.answer(await ft_instance.find_text('no_service_available'), show_alert=True)

            total_pages = math.ceil(len(purchases) / item_per_page)
            start = (page - 1) * item_per_page
            end = start + item_per_page
            current_services = purchases[start:end]

            service_status = {
                'active': '✅',
                'limited': '🔴',
                'expired': '🔴'
            }

            text = f"<b>{await ft_instance.find_text('vpn_select_service_for_info')}</b>"
            keyboard = [[InlineKeyboardButton(f"{service.username} {service_status.get(service.status)}", callback_data=f'vpn_my_service_detail__{service.purchase_id}')]

                        for service in current_services]

            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton(await ft_instance.find_keyboard('previous'), callback_data=f'vpn_my_services__{page - 1}'))
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton(await ft_instance.find_keyboard('next'), callback_data=f'vpn_my_services__{page + 1}'))

            if nav_buttons:
                keyboard.append(nav_buttons)

            keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='my_services_new')])

            if update.callback_query and 'vpn_my_services_new' not in update.callback_query.data:
                return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

            if query:
                await query.answer()

            return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


@handle_error.handle_functions_error
@message_token.check_token
async def service_info(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    purchase_id = query.data.replace('vpn_my_service_detail__', '')

    try:
        with (SessionLocal() as session):
            with session.begin():
                purchase = vpn_crud.get_purchase(session, purchase_id)
                if not purchase:
                    return await query.answer(await ft_instance.find_text('no_service_available'), show_alert=True)

                main_server = purchase.product.main_server
                get_from_server = await panel_api.marzban_api.get_user(purchase.product.main_server.server_ip, purchase.username)
                service_stauts_server = get_from_server['status']

                if service_stauts_server in ['limited', 'expired'] and purchase.status == 'active':
                    vpn_crud.update_purchase(session, purchase.purchase_id, status=service_stauts_server)

                expire_date = human_readable(get_from_server.get('expire'), await ft_instance.find_user_language())

                get_last_online_time = get_from_server.get('online_at')
                online_at = await ft_instance.find_text('not_connected_yet')

                if get_last_online_time:
                    online_at = datetime.fromisoformat(get_last_online_time).replace(microsecond=0)
                    now = datetime.now()
                    if (now - online_at).total_seconds() < 60:
                        online_at = now
                    online_at = human_readable(online_at, await ft_instance.find_user_language())

                used_traffic = round(get_from_server.get('used_traffic') / (1024 ** 3), 2)
                data_limit = int(get_from_server.get('data_limit') / (1024 ** 3))

                server_port = f":{main_server.server_port}" if main_server.server_port != 443 else ""
                subscribe_link = f"{main_server.server_protocol}{main_server.server_ip}{server_port}{get_from_server.get('subscription_url')}"

                service_status = {
                    'active': await ft_instance.find_text('vpn_service_active'),
                    'limited': await ft_instance.find_text('vpn_service_limited'),
                    'expired': await ft_instance.find_text('vpn_service_expired')
                }

                text = (
                    f"<b>{await ft_instance.find_text('vpn_selected_service_info')}</b>"
                    f"\n\n{await ft_instance.find_text('vpn_service_name')} <code>{purchase.username}</code>"
                    f"\n\n{await ft_instance.find_text('online_at')} {online_at}"
                    f"\n{await ft_instance.find_text('vpn_service_status')} {service_status.get(service_stauts_server, service_stauts_server)}"
                    f"\n{await ft_instance.find_text('vpn_expire_date')} {expire_date}"
                    f"\n{await ft_instance.find_text('vpn_traffic_use')} {used_traffic}/{data_limit}GB"
                    f"\n\n{await ft_instance.find_text('vpn_subsrciption_address')}"
                    f"\n\n<code>{subscribe_link}</code>"
                )

                keyboard = [
                    [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_upgrade_service'), callback_data=f'vpn_upgrade_service__{purchase.period}__{purchase.traffic}__{purchase_id}')],
                    [InlineKeyboardButton(await ft_instance.find_keyboard('refresh'), callback_data=f'vpn_my_service_detail__{purchase_id}'),
                     InlineKeyboardButton(await ft_instance.find_keyboard('vpn_remove_service'), callback_data=f'vpn_remove_service_ask__{purchase_id}')],
                    [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_advanced_options'),callback_data=f'vpn_advanced_options__{purchase_id}')],
                    [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='vpn_my_services__1')]
                ]

                await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

    except requests.exceptions.HTTPError as e:
        if '404 Client Error' in str(e):
            return await query.answer(await ft_instance.find_text('vpn_service_not_exit_in_server'), show_alert=True)
        raise e

    except Exception as e:
        raise e


@handle_error.handle_functions_error
@message_token.check_token
async def ask_remove_service_for_user(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    purchase_id = int(query.data.replace('vpn_remove_service_ask__', ''))

    with SessionLocal() as session:
        with session.begin():
            purchase = vpn_crud.get_purchase_with_chat_id(session, purchase_id, user_detail.id)

            if not purchase:
                return await query.answer(await ft_instance.find_text('no_service_available'), show_alert=True)

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

                returnable_amount = await vpn_utilities.calculate_price(traffic_left_in_gigabyte, days_left, purchase.chat_id)

            text = f"<b>{await ft_instance.find_text('vpn_ask_user_for_removing_service')}</b>"

            if returnable_amount:
                text += f"<b>\n{await ft_instance.find_text('returnable_amount')}</b>"
                text = text.format(f"{returnable_amount:,}")

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('yes_im_sure'), callback_data=f'vpn_remove_service__{purchase_id}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vpn_my_service_detail__{purchase_id}')]
            ]

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def remove_service_for_user(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    purchase_id = int(query.data.replace('vpn_remove_service__', ''))
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            purchase = vpn_crud.remove_purchase(session, purchase_id, user_detail.id)

            returnable_amount = await vpn_utilities.remove_service_in_server(session, purchase)

            text = await ft_instance.find_text('vpn_service_deleted_successfully')
            keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vpn_my_services__1')]]

            admin_msg = (
                f'The user deleted the service.'
                f'\n\nService username: {purchase.username}'
                f'\nService ID: {purchase.purchase_id}'
                f'\nService status before delete: {purchase.active}'
                f'\nService Product Name: {purchase.product.product_name}'
                f'\nReturnable Amount: {returnable_amount:,}'
            )

            await report_to_admin('info', 'remove_service_for_user', admin_msg, purchase.owner)
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def service_advanced_options(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    data = query.data
    user_detail = update.effective_chat

    if 'remove_this_message__' in data:
        data = data.replace('remove_this_message__', '')

    purchase_id = int(data.replace('vpn_advanced_options__', ''))

    try:
        with SessionLocal() as session:
            purchase = vpn_crud.get_purchase(session, purchase_id)

            if not purchase:
                return await query.answer(await ft_instance.find_text('no_service_available'), show_alert=True)

            main_server = purchase.product.main_server
            get_from_server = await panel_api.marzban_api.get_user(purchase.product.main_server.server_ip, purchase.username)

            used_traffic = round(get_from_server.get('used_traffic') / (1024 ** 3), 3)
            data_limit = round(get_from_server.get('data_limit') / (1024 ** 3), 3)
            lifetime_used_traffic = round(get_from_server.get('lifetime_used_traffic') / (1024 ** 3), 3)

            server_port = f":{main_server.server_port}" if main_server.server_port != 443 else ""
            subscribe_link = f"{main_server.server_protocol}{main_server.server_ip}{server_port}{get_from_server.get('subscription_url')}"

            onlien_at = human_readable(get_from_server.get('online_at'), await ft_instance.find_user_language()) \
                if get_from_server.get('online_at') else await ft_instance.find_text('not_connected_yet')

            service_status = {
                'active': await ft_instance.find_text('vpn_service_active'),
                'limited': await ft_instance.find_text('vpn_service_limited'),
                'expired': await ft_instance.find_text('vpn_service_expired')
            }

            text = (
                f"<b>{await ft_instance.find_text('vpn_selected_service_advanced_info')}</b>"
                f"\n\n{await ft_instance.find_text('vpn_service_name')} {purchase.username}"
                f"\n\n{await ft_instance.find_text('online_at')} {onlien_at}"
                f"\n{await ft_instance.find_text('vpn_service_status')} {service_status.get(get_from_server.get('status'), get_from_server.get('status'))}"
                f"\n{await ft_instance.find_text('vpn_used_traffic')} {used_traffic}GB"
                f"\n{await ft_instance.find_text('vpn_total_traffic')} {data_limit}GB"
                f"\n{await ft_instance.find_text('vpn_lifetime_used_traffic')} {lifetime_used_traffic}GB"
                f"\n{await ft_instance.find_text('created_at')} {datetime.fromisoformat(get_from_server.get('created_at')).strftime('%Y-%m-%d %H:%M:%S')}"
                f"\n{await ft_instance.find_text('vpn_expire_date')} {datetime.fromtimestamp(get_from_server.get('expire'))}"
                f"\n\n{await ft_instance.find_text('vpn_subsrciption_address')}"
                f"\n\n<code>{subscribe_link}</code>"
            )

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_get_configs'), callback_data=f'vpn_get_configs_separately__{purchase_id}__no')],
                [InlineKeyboardButton(await ft_instance.find_text('usage_report'), callback_data=f'statistics_week_{purchase_id}_hide'),
                 InlineKeyboardButton(await ft_instance.find_keyboard('refresh'), callback_data=f'vpn_advanced_options__{purchase_id}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_change_service_ownership'), callback_data=f'vpn_change_service_ownership__{purchase_id}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vpn_my_service_detail__{purchase.purchase_id}')]
            ]

            if update.callback_query and 'remove_this_message__' in update.callback_query.data:
                await query.delete_message()
                return await context.bot.send_message(chat_id=user_detail.id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

    except requests.exceptions.HTTPError as e:
        if '404 Client Error' in str(e):
            return await query.answer(await ft_instance.find_text('vpn_service_not_exit_in_server'), show_alert=True)

    except Exception as e:
        raise e


@handle_error.handle_functions_error
@message_token.check_token
async def get_configs_separately(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    purchase_id, in_new_message = query.data.replace('vpn_get_configs_separately__', '').split('__')
    get_service = context.user_data.get(f'service_detail_{purchase_id}')
    user_detail = update.effective_chat
    configs_text = ''

    if get_service:
        get_configs = get_service.get('info_from_server', {}).get('links', ['no_links'])

    else:
        with SessionLocal() as session:
            with session.begin():
                purchase = vpn_crud.get_purchase(session, int(purchase_id))
                main_server_ip = purchase.product.main_server.server_ip
                get_from_server = await panel_api.marzban_api.get_user(main_server_ip, purchase.username)
                get_configs = get_from_server.get('links')

    for config in get_configs:
        configs_text += f'\n\n<code>{config}</code>'

    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vpn_advanced_options__{purchase_id}')]]
    if in_new_message == 'yes':
        return await context.bot.send_message(text=configs_text, chat_id=user_detail.id, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    await query.edit_message_text(text=configs_text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_conversetion_error
async def get_new_user_chat_id(update, context):
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('cancel_button'), callback_data='cancel_change_ownership_conversation')]]
    text = await ft_instance.find_text('send_new_ownership_user_id')
    context.user_data['change_ownership_purchase_id'] = int(update.callback_query.data.replace('vpn_change_service_ownership__', ''))
    await update.callback_query.answer()
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return GET_NEW_USER_CHAT_ID


@handle_error.handle_conversetion_error
async def assurance(update, context):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    context.user_data['new_ownership_user_id'] = int(update.message.text)
    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('yes_im_sure'), callback_data='confirm_change')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('cancel_button'), callback_data='cancel_change')]
    ]
    text = await ft_instance.find_text('ask_for_assurnace')
    text = text.format(context.user_data['change_ownership_purchase_id'], update.message.text)
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return GET_ASSURNACE

@handle_error.handle_conversetion_error
async def change_ownership(update, context):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    query = update.callback_query
    purchase_id = context.user_data['change_ownership_purchase_id']
    new_user_id = context.user_data['new_ownership_user_id']
    await query.delete_message()

    if query.data == 'cancel_change':
        await context.bot.send_message(chat_id=user_detail.id, text=await ft_instance.find_text('action_canceled'))
        return ConversationHandler.END

    crud.change_purchase_ownership(purchase_id, new_user_id, user_detail.id)
    text = await ft_instance.find_text('change_ownership_was_successfull')
    text = text.format(purchase_id, new_user_id)
    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start_in_new_message')]]
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


change_ownership_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_new_user_chat_id, pattern=r'vpn_change_service_ownership__(\d+)')],
    states={
        GET_NEW_USER_CHAT_ID: [MessageHandler(filters.TEXT, assurance)],
        GET_ASSURNACE: [CallbackQueryHandler(change_ownership, pattern='^(confirm_change|cancel_change)$')],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='cancel_change_ownership_conversation')],
    conversation_timeout=600

)