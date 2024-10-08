import sys, os, math, functools, logging, traceback
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from admin.admin_utilities import admin_access, cancel_conversation as cancel
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import admin_crud, crud, vpn_crud
from database_sqlalchemy import SessionLocal
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
import utilities_reFactore
from vpn_service import vpn_utilities, buy_and_upgrade_service

DEFAULT_PRODUCT_ID = 1
ADD_CREDIT_BAlANCE = 0

service_status = {
    'active': '✅',
    'limited': '🟡',
    'ban': '🔴'
}


def handle_functions_error(func):
    @functools.wraps(func)
    async def wrapper(update, context, **kwargs):
        user_detail = update.effective_chat
        try:
            return await func(update, context, **kwargs)
        except Exception as e:
            if 'Message is not modified' in str(e): return await update.callback_query.answer()
            logging.error(f'error in {func.__name__}: {str(e)}')
            tb = traceback.format_exc()
            err = (
                f"🔴 An error occurred in {func.__name__}:"
                f"\n\nerror type:{type(e)}"
                f"\nerror reason: {str(e)}"
                f"\n\nTraceback: \n{tb}"
            )
            await context.bot.send_message(chat_id=user_detail.id, text=err)

    return wrapper

@handle_functions_error
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


@handle_functions_error
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

@handle_functions_error
@admin_access
async def view_user_info(update, context, chat_id=None):
    query = update.callback_query
    chat_id, page = chat_id, 1
    if not chat_id:
        chat_id, page = query.data.replace('admin_view_user__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            user = crud.get_user(session, int(chat_id))
            print(user.services.count)
            text = (f'Full Name: {user.first_name} {user.last_name}'
                    f'\nUsername: @{user.username}'
                    f'\nID: {user.user_id}'
                    f'\nChatID: {user.chat_id}'
                    f'\nEmail: {user.email}'
                    f'\nPhone Number: {user.phone_number}'
                    f'\nLanguage: {user.language}'
                    f'\nWallet Balance: {user.wallet:,} IRT'
                    f'\nInvited By: {user.invited_by} {f"({user.invited_by.first_name} {user.invited_by.last_name})" if user.invited_by else ""}'
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
                 InlineKeyboardButton('Message', callback_data=f'reply_ticket_{chat_id}')],
                [InlineKeyboardButton('🔰 Set User Status:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"Active", callback_data=f'admin_set_user_status__{chat_id}__active'),
                 InlineKeyboardButton(f"Ban", callback_data=f'admin_set_user_status__{chat_id}__ban')],

                [InlineKeyboardButton('👝 Change Wallet Balance:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"Add", callback_data=f'admin_cuwb__{chat_id}__increase_balance_by_admin'),
                 InlineKeyboardButton(f"Set", callback_data=f'admin_cuwb__{chat_id}__set'),
                 InlineKeyboardButton(f"Less", callback_data=f'admin_cuwb__{chat_id}__reduction_balance_by_admin')],

                [InlineKeyboardButton('👑 Set User Level:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"Normal", callback_data=f'admin_set_user_level__{chat_id}__1'),
                 InlineKeyboardButton(f"Trustable", callback_data=f'admin_set_user_level__{chat_id}__3')],
                [InlineKeyboardButton(f"SuperUser", callback_data=f'admin_set_user_level__{chat_id}__5'),
                 InlineKeyboardButton(f"Admin", callback_data=f'admin_set_user_level__{chat_id}__10')],

                [InlineKeyboardButton('🎁 VPN Free Test:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"True (received)", callback_data=f'admin_set_vpn_free_test__{chat_id}__true'),
                 InlineKeyboardButton(f"False", callback_data=f'admin_set_vpn_free_test__{chat_id}__false')],

                [InlineKeyboardButton('🎛️ User VPN Services', callback_data=f'admin_user_services__{chat_id}__1__{page}')],

                [InlineKeyboardButton('Back', callback_data=f'admin_manage_users__{page}')]
            ]

            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


@handle_functions_error
@admin_access
async def admin_change_user_status(update, context):
    query = update.callback_query
    chat_id, status = query.data.replace('admin_set_user_status__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(session, int(chat_id), user_status=status)
            await query.answer('+ Changes Saved!')
            return await view_user_info(update, context, chat_id=chat_id)


@handle_functions_error
@admin_access
async def admin_set_user_level(update, context):
    query = update.callback_query
    chat_id, level = query.data.replace('admin_set_user_level__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(session, int(chat_id), user_level=int(level))
            await query.answer('+ Changes Saved!')
            return await view_user_info(update, context, chat_id=chat_id)


@handle_functions_error
@admin_access
async def admin_set_free_vpn_test(update, context):
    query = update.callback_query
    chat_id, status = query.data.replace('admin_set_vpn_free_test__', '').split('__')
    status = status == 'true'
    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(session, int(chat_id), get_vpn_free_service=status)
            await query.answer('+ Changes Saved!')
            return await view_user_info(update, context, chat_id=chat_id)


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
                elif action == 'set':
                    crud.update_user(session, chat_id, wallet=amount)
                elif action == 'reduction_balance_by_admin':
                    crud.less_from_wallet(session, finacial_report)

                msg = (
                    f'Action: {finacial_report.action.replace("_", " ")}'
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

@handle_functions_error
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
            keyboard = [[InlineKeyboardButton(f"{service.username} {service_status.get(service.status)}", callback_data=f'admin_user_service_detail__{service.purchase_id}')]
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


@handle_functions_error
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


@handle_functions_error
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
            [InlineKeyboardButton("Back", callback_data=f'admin_bv_for_user__{chat_id}__{page}__{user_info_page}__{period}_{traffic}')]
        ]

        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_functions_error
async def admin_confirm_buy_vpn_service(update, context):
    query = update.callback_query
    payment_status, chat_id, page, user_info_page, period, traffic = query.data.replace('admin_confirm_bv__', '').split('__')

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

            keyboard = [
                [InlineKeyboardButton("Back", callback_data=f'admin_assurance_bv__{chat_id}__{page}__{user_info_page}__{period}_{traffic}')]
            ]
            text = 'Create Service For User Successful'
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
