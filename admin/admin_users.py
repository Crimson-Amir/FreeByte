import sys, os, math, requests, pytz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from admin.admin_utilities import admin_access, cancel_conversation as cancel
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import admin_crud, crud, vpn_crud
from database_sqlalchemy import SessionLocal
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
import utilities_reFactore
from datetime import datetime
from vpn_service import vpn_utilities, buy_and_upgrade_service, panel_api

DEFAULT_PRODUCT_ID = 1
ADD_CREDIT_BAlANCE = 0

service_status = {
    'active': '✅',
    'limited': '🟡',
    'ban': '🔴'
}

@vpn_utilities.handle_functions_error
@admin_access
async def all_users_list(update, context):
    query = update.callback_query
    item_per_page = 15
    page = int(query.data.split('__')[1]) if query and query.data.startswith('admin_manage_users') else 1

    with SessionLocal() as session:
        with session.begin():
            users = admin_crud.get_all_users(session)
            total_pages = math.ceil(len(users) / item_per_page)
            start = (page - 1) * item_per_page
            end = start + item_per_page
            current_users = users[start:end]
            text = 'select user to manage:'
            keyboard = [[InlineKeyboardButton(f"{user.first_name} {user.chat_id} {service_status.get(user.config.user_status)}", callback_data=f'admin_view_user__{user.chat_id}__{page}')] for user in current_users]
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton('<- previous', callback_data=f'admin_manage_users__{page - 1}'))
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton('next ->', callback_data=f'admin_manage_users__{page + 1}'))
            if nav_buttons: keyboard.append(nav_buttons)
            keyboard.append([InlineKeyboardButton('Back', callback_data='admin_page')])

            return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def find_user(update, context):
    chat_id_substring = context.args
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            user = crud.get_user(session, int(chat_id_substring[0]))
            if not user: return await context.bot.send_message(chat_id=user_detail.id, text='there is no user with this chat id')
            text = 'select user to manage:'

            keyboard = [[InlineKeyboardButton(f"{user.first_name} {user.chat_id} {service_status.get(user.config.user_status)}", callback_data=f'admin_view_user__{user.chat_id}__1')],
                        [InlineKeyboardButton('Back', callback_data='admin_page')]]

            return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))

@vpn_utilities.handle_functions_error
@admin_access
async def view_user_info(update, context, chat_id=None, page=None):
    query = update.callback_query
    chat_id, page = chat_id, page
    if not chat_id:
        chat_id, page = query.data.replace('admin_view_user__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            user = crud.get_user(session, int(chat_id))

            text = (f'Full Name: {user.first_name} {user.last_name}'
                    f'\nUsername: @{user.username}'
                    f'\nID: {user.user_id}'
                    f'\nChatID: {user.chat_id}'
                    f'\nEmail: {user.email}'
                    f'\nPhone Number: {user.phone_number}'
                    f'\nLanguage: {user.language}'
                    f'\nWallet Balance: {user.wallet:,} IRT'
                    f'\nInvited By: {user.invited_by}'
                    f'\nRegister Date: {user.register_date.replace(microsecond=0)} ({utilities_reFactore.human_readable(user.register_date, "en")})'
                    f'\n\nLevel: {user.config.user_level}'
                    f'\nStatus: {user.config.user_status}'
                    f'\nTraffic Notification: {user.config.traffic_notification_percent}%'
                    f'\nPeriod Time Notification: {user.config.period_notification_day} Day'
                    f'\nRecive FreeService: {user.config.get_vpn_free_service}'
                    f'\n\nActive Vpn Services: {len([service for service in user.services if service.status == "active" and service.active == True])}'
                    f'\nAll Enable Vpn Services: {len([service for service in user.services if service.active == True])}'
                    f'\nPaid Financials: {len([financial for financial in user.financial_reports if financial.payment_status == "paid"])}'
                    f'\nRefunded Financials: {len([financial for financial in user.financial_reports if financial.payment_status == "refund"])}'
                    f'\nAll Financials: {len(user.financial_reports)}'
                    )

            keyboard = [
                [InlineKeyboardButton('Refresh', callback_data=f'admin_view_user__{chat_id}__{page}'),
                 InlineKeyboardButton('Message', callback_data=f'reply_ticket_private_{chat_id}')],

                [InlineKeyboardButton('👝 Change Wallet Balance:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"Add", callback_data=f'admin_cuwb__{chat_id}__increase_balance_by_admin'),
                 InlineKeyboardButton(f"Set", callback_data=f'admin_cuwb__{chat_id}__set'),
                 InlineKeyboardButton(f"Less", callback_data=f'admin_cuwb__{chat_id}__reduction_balance_by_admin')],

                [InlineKeyboardButton('👑 Set User Level:', callback_data=f'just_for_show')],
                [InlineKeyboardButton("1", callback_data=f'admin_set_user_level__{chat_id}__1__{page}'),
                 InlineKeyboardButton("2", callback_data=f'admin_set_user_level__{chat_id}__2__{page}'),
                InlineKeyboardButton("3", callback_data=f'admin_set_user_level__{chat_id}__3__{page}'),
                 InlineKeyboardButton("4", callback_data=f'admin_set_user_level__{chat_id}__4__{page}'),
                 InlineKeyboardButton("5", callback_data=f'admin_set_user_level__{chat_id}__5__{page}')],
                [InlineKeyboardButton("6", callback_data=f'admin_set_user_level__{chat_id}__6__{page}'),
                 InlineKeyboardButton("7", callback_data=f'admin_set_user_level__{chat_id}__7__{page}'),
                 InlineKeyboardButton("8", callback_data=f'admin_set_user_level__{chat_id}__8__{page}'),
                 InlineKeyboardButton("9", callback_data=f'admin_set_user_level__{chat_id}__9__{page}'),
                 InlineKeyboardButton("10", callback_data=f'admin_set_user_level__{chat_id}__10__{page}')],

                [InlineKeyboardButton('🎁 VPN Free Test:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"True (received)", callback_data=f'admin_set_vpn_free_test__{chat_id}__true__{page}'),
                 InlineKeyboardButton(f"False", callback_data=f'admin_set_vpn_free_test__{chat_id}__false__{page}')],

                [InlineKeyboardButton('🎛️ User VPN Services', callback_data=f'admin_user_services__{chat_id}__1__{page}')],

                [InlineKeyboardButton('Back', callback_data=f'admin_manage_users__{page}')]
            ]

            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

@vpn_utilities.handle_functions_error
@admin_access
async def admin_set_user_level(update, context):
    query = update.callback_query
    chat_id, level, page = query.data.replace('admin_set_user_level__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(session, int(chat_id), user_level=int(level))
            utilities_reFactore.user_data_manager.delete_user_data(int(chat_id))
            await query.answer('+ Changes Saved!')
            return await view_user_info(update, context, chat_id=chat_id, page=page)


@vpn_utilities.handle_functions_error
@admin_access
async def admin_set_free_vpn_test(update, context):
    query = update.callback_query
    chat_id, status, page = query.data.replace('admin_set_vpn_free_test__', '').split('__')
    status = status == 'true'
    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(session, int(chat_id), get_vpn_free_service=status)
            await query.answer('+ Changes Saved!')
            return await view_user_info(update, context, chat_id=chat_id, page=page)


@admin_access
async def get_new_balance(update, context):
    await update.callback_query.answer()
    user_detail = update.effective_chat
    try:
        query = update.callback_query
        chat_id, action = query.data.replace('admin_cuwb__', '').split('__')
        context.user_data[f'admin_increase_user_balance_chat_id'] = chat_id
        context.user_data[f'admin_increase_user_balance_action'] = action
        keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel_increase_wallet_conversation')]]
        text = 'send amount in IRT:'
        await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_CREDIT_BAlANCE
    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'error:\n{e}')
        return ConversationHandler.END


@admin_access
async def admin_change_wallet_balance(update, context):
    user_detail = update.effective_chat
    try:
        with SessionLocal() as session:
            with session.begin():
                ft_instance = utilities_reFactore.FindText(None, None)

                chat_id = int(context.user_data[f'admin_increase_user_balance_chat_id'])
                action = context.user_data[f'admin_increase_user_balance_action']
                amount = int(update.message.text)

                finacial_report = crud.create_financial_report(
                    session, 'recive' if action == 'increase_balance_by_admin' else 'spend',
                    chat_id=chat_id,
                    amount=amount,
                    action=action,
                    service_id=None,
                    payment_status='not paid',
                    payment_getway='wallet',
                    currency='IRT'
                )

                text = f'+ Operation Successfull.\namoutn: {amount:,} IRT\nchat id: {chat_id}\naction: {action}'

                if action == 'increase_balance_by_admin':
                    crud.add_credit_to_wallet(session, finacial_report)

                    user_text = await ft_instance.find_from_database(chat_id, 'amount_added_to_wallet_successfully')
                    user_text = user_text.format(f"{amount:,}")
                    await context.bot.send_message(text=user_text, chat_id=chat_id)

                elif action == 'set':
                    crud.update_user(session, chat_id, wallet=amount)
                elif action == 'reduction_balance_by_admin':
                    crud.less_from_wallet(session, finacial_report)

                msg = (
                    f"Admin Change User Wallet"
                    f'\nAction: {finacial_report.action.replace("_", " ")}'
                    f'\nAuthority: {finacial_report.financial_id}'
                    f'\nAmount: {finacial_report.amount:,}'
                    f'\nService ID: {finacial_report.id_holder}'
                    f'\nUser chat id: {finacial_report.chat_id}'
                    f'\nAdmin chat ID: {user_detail.id} ({user_detail.first_name})'
                )

                await utilities_reFactore.report_to_admin('purchase', 'admin_change_wallet_balance', msg)

                keyboard = [[InlineKeyboardButton('User Detail', callback_data=f"admin_view_user__{chat_id}__1")]]
                await context.bot.send_message(text=text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

                return ConversationHandler.END

    except Exception as e:
        await context.bot.send_message(text=f'Error in add amount: {e}', chat_id=user_detail.id, parse_mode='html')
        return ConversationHandler.END


admin_change_wallet_balance_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_new_balance, pattern='admin_cuwb__(.*)')],
    states={
        ADD_CREDIT_BAlANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_change_wallet_balance)],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='cancel_increase_wallet_conversation')],
    conversation_timeout=600

)

@vpn_utilities.handle_functions_error
@admin_access
async def admin_user_services(update, context):
    query = update.callback_query
    item_per_page = 10
    chat_id, page, user_info_page = query.data.replace('admin_user_services__', '').split('__')
    page = int(page)

    with SessionLocal() as session:
        with session.begin():
            purchases = vpn_crud.get_purchase_by_chat_id(session, chat_id)

            if not purchases:
                return await query.answer('there is no service for this user')

            total_pages = math.ceil(len(purchases) / item_per_page)
            start = (page - 1) * item_per_page
            end = start + item_per_page
            current_services = purchases[start:end]

            text = 'Select the service to view info:'
            keyboard = [[InlineKeyboardButton(f"{service.username} {service_status.get(service.status)}", callback_data=f'admin_user_service_detail__{service.purchase_id}__{page}__{user_info_page}')]
                        for service in current_services]

            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton('<- previous', callback_data=f'admin_user_services__{page - 1}__{user_info_page}'))
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton('next ->', callback_data=f'admin_user_services__{page + 1}__{user_info_page}'))

            if nav_buttons:
                keyboard.append(nav_buttons)

            keyboard.extend([[InlineKeyboardButton('Buy Service For This user', callback_data=f'admin_bv_for_user__{chat_id}__{page}__{user_info_page}__30__40')],
                             [InlineKeyboardButton('Back', callback_data=f'admin_view_user__{chat_id}__{user_info_page}')]])

            return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_buy_service_for_user(update, context):
    query = update.callback_query
    chat_id, page, user_info_page, period_callback, traffic_callback = query.data.replace('admin_bv_for_user__', '').split('__')
    user_detail = update.effective_chat

    traffic = max(min(int(traffic_callback), 150), 1) or 40
    period = max(min(int(period_callback), 90), 1) or 30

    price = await vpn_utilities.calculate_price(traffic, period, user_detail.id)

    text = (f"Customize service for user:"
            f"\n\nPrice {price:,} IRT")

    keyboard = [
        [InlineKeyboardButton('Traffic', callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"admin_bv_for_user__{chat_id}__{page}__{user_info_page}__{period}__{traffic - 1}"),
         InlineKeyboardButton(f"{traffic} GB", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"admin_bv_for_user__{chat_id}__{page}__{user_info_page}__{period}__{traffic + 10}")],
        [InlineKeyboardButton('Period Time', callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"admin_bv_for_user__{chat_id}__{page}__{user_info_page}__{period - 1}__{traffic}"),
         InlineKeyboardButton(f"{period} Days", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"admin_bv_for_user__{chat_id}__{page}__{user_info_page}__{period + 10}__{traffic}")],
        [InlineKeyboardButton("Back", callback_data=f'admin_user_services__{chat_id}__{page}__{user_info_page}'),
         InlineKeyboardButton("Confirm", callback_data=f"admin_assurance_bv__{chat_id}__{page}__{user_info_page}__{period}__{traffic}")]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_assurance_buy_vpn_service(update, context):
    query = update.callback_query
    chat_id, page, user_info_page, period, traffic = query.data.replace('admin_assurance_bv__', '').split('__')
    with SessionLocal() as session:
        price = await vpn_utilities.calculate_price(traffic, period, chat_id)
        get_user = crud.get_user(session, chat_id)

        text = (f"Are you sure you wanna buy this service for user?"
                f"\nSelect payment status."
                f"\nimportant: if user does not have enough credit, wallet will be negative"
                f"\n\nPrice {price:,} IRT"
                f"\nUser Balance: {get_user.wallet}"
                f"\n\nUser Name: {get_user.first_name} {get_user.last_name}"
                f"\n\nUser chat id: {chat_id}")

        keyboard = [
            [InlineKeyboardButton("Create And reduce credit from wallet", callback_data=f"admin_confirm_bv__reduce__{chat_id}__{page}__{user_info_page}__{period}__{traffic}")],
            [InlineKeyboardButton("Create without reduce", callback_data=f"admin_confirm_bv__noreduce__{chat_id}__{page}__{user_info_page}__{period}__{traffic}")],
            [InlineKeyboardButton("Back", callback_data=f'admin_bv_for_user__{chat_id}__{page}__{user_info_page}__{period}__{traffic}')]
        ]

        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_confirm_buy_vpn_service(update, context):
    query = update.callback_query
    payment_status, chat_id, page, user_info_page, period, traffic = query.data.replace('admin_confirm_bv__', '').split('__')
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            amount = await vpn_utilities.calculate_price(traffic, period, chat_id)
            purchase = crud.create_purchase(session, DEFAULT_PRODUCT_ID, chat_id, traffic, period)

            if payment_status == 'reduce':
                finacial_report = crud.create_financial_report(
                    session, 'spend',
                    chat_id=chat_id,
                    amount=amount,
                    action='buy_vpn_service',
                    service_id=purchase.purchase_id,
                    payment_status='not paid',
                    payment_getway='wallet',
                    currency='IRT'
                )
                crud.less_from_wallet(session, finacial_report)

            await buy_and_upgrade_service.create_service_for_user(context, session, purchase_id=purchase.purchase_id)

            msg = (
                f'admin Create Service For User'
                f'\npayment_status: {payment_status}'
                f'\nAmount: {amount:,}'
                f'\nService ID: {purchase.purchase_id}'
                f'\nService username: {purchase.username}'
                f'\nService Traffic: {purchase.traffic}'
                f'\nService Period: {purchase.period}'
                f'\nProduct Name: {purchase.product.product_name}'
                f'\nUser chat id: {chat_id}'
                f'\nAdmin chat ID: {user_detail.id} ({user_detail.first_name})'
            )

            await utilities_reFactore.report_to_admin('purchase', 'admin_confirm_buy_vpn_service', msg)

            keyboard = [
                [InlineKeyboardButton("Back", callback_data=f'admin_assurance_bv__{chat_id}__{page}__{user_info_page}__{period}__{traffic}')]
            ]
            text = 'Create Service For User Successful'
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))



@vpn_utilities.handle_functions_error
@admin_access
async def admin_user_service_detail(update, context):
    query = update.callback_query
    data = query.data
    user_detail = update.effective_chat

    purchase_id, page, user_info_page = data.replace('admin_user_service_detail__', '').split('__')

    try:
        with SessionLocal() as session:
            purchase = vpn_crud.get_purchase(session, purchase_id)

            if not purchase:
                return await query.answer('service not found', show_alert=True)

            main_server = purchase.product.main_server
            get_from_server = await panel_api.marzban_api.get_user(purchase.product.main_server.server_ip, purchase.username)

            used_traffic = round(get_from_server.get('used_traffic') / (1024 ** 3), 3)
            data_limit = round(get_from_server.get('data_limit') / (1024 ** 3), 3)
            lifetime_used_traffic = round(get_from_server.get('lifetime_used_traffic') / (1024 ** 3), 3)

            server_port = f":{main_server.server_port}" if main_server.server_port != 443 else ""
            subscribe_link = f"{main_server.server_protocol}{main_server.server_ip}{server_port}{get_from_server.get('subscription_url')}"

            onlien_at = utilities_reFactore.human_readable(get_from_server.get('online_at'), 'en') if get_from_server.get('online_at') else 'not online yet'

            text = (
                f"\n\nUsername: {purchase.username}"
                f"\n\nOnline at: {onlien_at}"
                f"\nStatus: {service_status.get(get_from_server.get('status'), get_from_server.get('status'))} {get_from_server.get('status')}"
                f"\nUsed Traffic: {used_traffic}GB"
                f"\nData Limit: {data_limit}GB"
                f"\nLifeTime Used Traffic: {lifetime_used_traffic}GB"
                f"\nSubscription Updated at: ({utilities_reFactore.human_readable(get_from_server.get('sub_updated_at'), 'en')})"
                f"\ncreated at: {datetime.fromisoformat(get_from_server.get('created_at')).strftime('%Y-%m-%d %H:%M:%S')} ({utilities_reFactore.human_readable(datetime.fromisoformat(get_from_server.get('created_at')), 'en')})"
                f"\nExpired: {datetime.fromtimestamp(get_from_server.get('expire'))} ({utilities_reFactore.human_readable(datetime.fromtimestamp(get_from_server.get('expire')), 'en')})"
                f"\n\nSubscription Link:"
                f"\n\n<code>{subscribe_link}</code>"
            )

            keyboard = [
                [InlineKeyboardButton("Set Traffic And Period",callback_data=f'admin_set_time_and_traffic__{purchase_id}__{page}__{user_info_page}__30__40')],
                [InlineKeyboardButton("Remove", callback_data=f'admin_assurance_remove_vpn__{purchase_id}__{page}__{user_info_page}'),
                 InlineKeyboardButton("Upgrade", callback_data=f'admin_upgrade_user_vpn_service__{purchase_id}__{page}__{user_info_page}__30__40')],
                [InlineKeyboardButton("Statistics", callback_data=f'statistics_week_{purchase_id}_hide'),
                 InlineKeyboardButton("Refresh", callback_data=f'admin_user_service_detail__{purchase_id}__{page}__{user_info_page}')],
                [InlineKeyboardButton("Back", callback_data=f'admin_user_services__{purchase.chat_id}__{page}__{user_info_page}')]
            ]

            if update.callback_query and 'remove_this_message__' in update.callback_query.data:
                await query.delete_message()
                return await context.bot.send_message(chat_id=user_detail.id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

    except requests.exceptions.HTTPError as e:
        if '404 Client Error' in str(e):
            return await query.answer('vpn service not exit in server', show_alert=True)

    except Exception as e:
        raise e


@vpn_utilities.handle_functions_error
@admin_access
async def admin_set_purchase_period_and_traffic(update, context):
    query = update.callback_query
    purchase_id, page, user_info_page, period_callback, traffic_callback = query.data.replace('admin_set_time_and_traffic__', '').split('__')
    user_detail = update.effective_chat

    traffic = max(min(int(traffic_callback), 150), 1) or 40
    period = max(min(int(period_callback), 90), 1) or 30

    price = await vpn_utilities.calculate_price(traffic, period, user_detail.id)

    text = (f"set purchase traffic andperiod time:"
            f"\n\nPrice {price:,} IRT")

    keyboard = [
        [InlineKeyboardButton('Traffic', callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"admin_set_time_and_traffic__{purchase_id}__{page}__{user_info_page}__{period}__{traffic - 1}"),
         InlineKeyboardButton(f"{traffic} GB", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"admin_set_time_and_traffic__{purchase_id}__{page}__{user_info_page}__{period}__{traffic + 10}")],
        [InlineKeyboardButton('Period Time', callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"admin_set_time_and_traffic__{purchase_id}__{page}__{user_info_page}__{period - 1}__{traffic}"),
         InlineKeyboardButton(f"{period} Days", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"admin_set_time_and_traffic__{purchase_id}__{page}__{user_info_page}__{period + 10}__{traffic}")],
        [InlineKeyboardButton("Back", callback_data=f'admin_user_service_detail__{purchase_id}__{page}__{user_info_page}'),
         InlineKeyboardButton("Confirm", callback_data=f"admin_assurance_set_ptp__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}")]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_assurance_set_purchase_traffic_and_period(update, context):
    query = update.callback_query
    purchase_id, page, user_info_page, period, traffic = query.data.replace('admin_assurance_set_ptp__', '').split('__')

    text = (f"Are you sure you wanna set traffic and period?\nno amount has add or descread!\n\n"
            f"Traffic: {traffic} GB"
            f"Period: {period} Day")

    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f"admin_confirm_set_ptp__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}"),
        InlineKeyboardButton("Back", callback_data=f'admin_set_time_and_traffic__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

from datetime import timedelta
@vpn_utilities.handle_functions_error
@admin_access
async def admin_confirm_set_purchase_traffic_and_period(update, context):
    query = update.callback_query
    purchase_id, page, user_info_page, period, traffic = query.data.replace('admin_confirm_set_ptp__', '').split('__')
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            purchase = vpn_crud.update_purchase(
                session,
                purchase_id,
                traffic=traffic,
                period=period,
                register_date=datetime.now(pytz.timezone('Asia/Tehran'))
            )

            main_server_ip = purchase.product.main_server.server_ip
            await panel_api.marzban_api.reset_user_data_usage(main_server_ip, purchase.username)
            traffic_to_byte = int(traffic * (1024 ** 3))
            expire_date = datetime.now(pytz.timezone('Asia/Tehran'))

            date_in_timestamp = (expire_date + timedelta(days=period)).timestamp()

            json_config = await buy_and_upgrade_service.create_json_config(purchase.username, date_in_timestamp, traffic_to_byte)
            await panel_api.marzban_api.modify_user(main_server_ip, purchase.username, json_config)

            msg = (
                f'admin Set Service Traffic and Period For User'
                f'\nService ID: {purchase.purchase_id}'
                f'\nService username: {purchase.username}'
                f'\nService Traffic Now: {purchase.traffic} GB'
                f'\nService Period Now: {purchase.period} GB'
                f'\nProduct Name: {purchase.product.product_name}'
                f'\nUser chat id: {purchase.chat_id}'
                f'\nAdmin chat ID: {user_detail.id} ({user_detail.first_name})'
            )

            await utilities_reFactore.report_to_admin('purchase', 'admin_confirm_upgrade_vpn_service', msg)

            keyboard = [
                [InlineKeyboardButton("Back", callback_data=f'admin_user_service_detail__{purchase_id}__{page}__{user_info_page}')]
            ]

            text = 'set Service For User Successful'
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_upgrade_service_for_user(update, context):
    query = update.callback_query
    purchase_id, page, user_info_page, period_callback, traffic_callback = query.data.replace('admin_upgrade_user_vpn_service__', '').split('__')
    user_detail = update.effective_chat

    traffic = max(min(int(traffic_callback), 150), 1) or 40
    period = max(min(int(period_callback), 90), 1) or 30

    price = await vpn_utilities.calculate_price(traffic, period, user_detail.id)

    text = (f"Customize service for Upgrade:"
            f"\n\nPrice {price:,} IRT")

    keyboard = [
        [InlineKeyboardButton('Traffic', callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"admin_upgrade_user_vpn_service__{purchase_id}__{page}__{user_info_page}__{period}__{traffic - 1}"),
         InlineKeyboardButton(f"{traffic} GB", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"admin_upgrade_user_vpn_service__{purchase_id}__{page}__{user_info_page}__{period}__{traffic + 10}")],
        [InlineKeyboardButton('Period Time', callback_data="just_for_show")],
        [InlineKeyboardButton("➖", callback_data=f"admin_upgrade_user_vpn_service__{purchase_id}__{page}__{user_info_page}__{period - 1}__{traffic}"),
         InlineKeyboardButton(f"{period} Days", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"admin_upgrade_user_vpn_service__{purchase_id}__{page}__{user_info_page}__{period + 10}__{traffic}")],
        [InlineKeyboardButton("Back", callback_data=f'admin_user_service_detail__{purchase_id}__{page}__{user_info_page}'),
         InlineKeyboardButton("Confirm", callback_data=f"admin_assurance_upgrade_vpn__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}")]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_assurance_upgrade_vpn_service(update, context):
    query = update.callback_query
    purchase_id, page, user_info_page, period, traffic = query.data.replace('admin_assurance_upgrade_vpn__', '').split('__')

    with SessionLocal() as session:
        purchase = vpn_crud.get_purchase(session, purchase_id)
        price = await vpn_utilities.calculate_price(traffic, period, purchase.chat_id)

        text = (f"Are you sure you wanna Upgrade this service for user?"
                f"\nSelect payment status."
                f"\nimportant: if user does not have enough credit, wallet will be negative"
                f"\n\nPrice {price:,} IRT"
                f"\nUser Balance: {purchase.owner.wallet:,} IRT"
                f"\n\nUser Name: {purchase.owner.first_name} {purchase.owner.last_name}"
                f"\n\nUser chat id: {purchase.chat_id}")

        keyboard = [
            [InlineKeyboardButton("Upgrade And reduce credit from wallet", callback_data=f"admin_confirm_upvpn__reduce__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}")],
            [InlineKeyboardButton("Upgrade without reduce", callback_data=f"admin_confirm_upvpn__noreduce__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}")],
            [InlineKeyboardButton("Back", callback_data=f'admin_upgrade_user_vpn_service__{purchase_id}__{page}__{user_info_page}__{period}__{traffic}')]
        ]

        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_confirm_upgrade_vpn_service(update, context):
    query = update.callback_query
    payment_status, purchase_id, page, user_info_page, period, traffic = query.data.replace('admin_confirm_upvpn__', '').split('__')
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            purchase = vpn_crud.update_purchase(
                session,
                purchase_id,
                upgrade_traffic=traffic,
                upgrade_period=period,
                register_date=datetime.now(pytz.timezone('Asia/Tehran'))
            )
            amount = await vpn_utilities.calculate_price(traffic, period, purchase.chat_id)

            if payment_status == 'reduce':
                finacial_report = crud.create_financial_report(
                    session, 'spend',
                    chat_id=purchase.chat_id,
                    amount=amount,
                    action='upgrade_vpn_service',
                    service_id=purchase.purchase_id,
                    payment_status='not paid',
                    payment_getway='wallet',
                    currency='IRT'
                )
                crud.less_from_wallet(session, finacial_report)

            purchase, traffic_for_upgrade, period_for_upgrade = await buy_and_upgrade_service.upgrade_service_for_user(
                context,
                session,
                purchase_id=purchase_id
            )

            msg = (
                f'admin Upgrade Service For User'
                f'\npayment_status: {payment_status}'
                f'\nAmount: {amount:,} IRT'
                f'\nService ID: {purchase.purchase_id}'
                f'\nService username: {purchase.username}'
                f'\nService Traffic Now: {purchase.traffic} GB'
                f'\nService Period Now: {purchase.period} GB'
                f'\nService Upgrade Traffic: {traffic_for_upgrade} GB'
                f'\nService Upgrade Period: {period_for_upgrade} GB'
                f'\nProduct Name: {purchase.product.product_name}'
                f'\nUser chat id: {purchase.chat_id}'
                f'\nAdmin chat ID: {user_detail.id} ({user_detail.first_name})'
            )

            await utilities_reFactore.report_to_admin('purchase', 'admin_confirm_upgrade_vpn_service', msg)

            keyboard = [
                [InlineKeyboardButton("Back", callback_data=f'admin_user_service_detail__{purchase_id}__{page}__{user_info_page}')]
            ]

            text = 'Upgrade Service For User Successful'
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_assurance_remove_vpn_service(update, context):
    query = update.callback_query
    purchase_id, page, user_info_page = query.data.replace('admin_assurance_remove_vpn__', '').split('__')

    with SessionLocal() as session:
        purchase = vpn_crud.get_purchase(session, purchase_id)
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

        text = (f"Are you sure you wanna Remove this service for user?"
                f"\nSelect payment status."
                f"\n\nReturnable Amount {returnable_amount:,} IRT"
                f"\nUser Balance: {purchase.owner.wallet:,} IRT"
                f"\n\nUser Name: {purchase.owner.first_name} {purchase.owner.last_name}"
                f"\n\nUser chat id: {purchase.chat_id}")

        keyboard = [
            [InlineKeyboardButton("Remove and return credit to user wallet", callback_data=f"admin_confirm_remove_vpn__refund__{purchase_id}__{page}__{user_info_page}")] if returnable_amount else None,
            [InlineKeyboardButton("Remove without return", callback_data=f"admin_confirm_remove_vpn__norefund__{purchase_id}__{page}__{user_info_page}")],
            [InlineKeyboardButton("Back", callback_data=f'admin_user_service_detail__{purchase_id}__{page}__{user_info_page}')]
        ]
        keyboard = [list(filter(None, row)) for row in keyboard]

        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@vpn_utilities.handle_functions_error
@admin_access
async def admin_confirm_remove_vpn_service(update, context):
    query = update.callback_query
    payment_status, purchase_id, page, user_info_page = query.data.replace('admin_confirm_remove_vpn__', '').split('__')
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            purchase = vpn_crud.remove_purchase(session, purchase_id, user_detail.id)
            main_server_ip = purchase.product.main_server.server_ip
            returnable_amount = 0
            if payment_status == 'refund':
                returnable_amount = await vpn_utilities.remove_service_in_server(session, purchase)
            else:
                await panel_api.marzban_api.remove_user(main_server_ip, purchase.username)

            msg = (
                f'admin Remove Service For User'
                f'\npayment_status: {payment_status}'
                f'\nReturned Amount: {returnable_amount:,} IRT'
                f'\nService ID: {purchase.purchase_id}'
                f'\nService username: {purchase.username}'
                f'\nService Traffic: {purchase.traffic} GB'
                f'\nService Period: {purchase.period} Day'
                f'\nProduct Name: {purchase.product.product_name}'
                f'\nUser chat id: {purchase.chat_id}'
                f'\nAdmin chat ID: {user_detail.id} ({user_detail.first_name})'
            )

            await utilities_reFactore.report_to_admin('info', 'admin_confirm_remove_vpn_service', msg)

            keyboard = [
                [InlineKeyboardButton("Back", callback_data=f'admin_user_services__{purchase.chat_id}__{page}__{user_info_page}')]
            ]

            text = 'Remove Service For User Successful'
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

@vpn_utilities.handle_functions_error
@admin_access
async def find_service(update, context):
    service_id = context.args
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            service = vpn_crud.get_purchase(session, int(service_id[0]))
            if not service:
                return await context.bot.send_message(chat_id=user_detail.id, text='there is no service with this chat id')
            text = 'select service to manage:'

            keyboard = [[InlineKeyboardButton(f"{service.username} {service_status.get(service.status)}", callback_data=f'admin_user_service_detail__{service.purchase_id}__1__1')],
                        [InlineKeyboardButton('Back', callback_data='admin_page')]]

            return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))