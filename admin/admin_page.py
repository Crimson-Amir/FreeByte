import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import crud, admin_crud
from database_sqlalchemy import SessionLocal
from vpn_service import vpn_utilities
from admin import partner

@admin_access
async def admin_page(update, context):
    user_detail = update.effective_chat

    keyboard = [
        [InlineKeyboardButton('System', callback_data=f"admin_system__1"),
         InlineKeyboardButton('Virtual Number', callback_data=f"admin_manage_users__1")],
        [InlineKeyboardButton('VPN Section', callback_data=f"admin_vpn"),
         InlineKeyboardButton('Manage Users', callback_data=f"admin_manage_users__1")]
    ]
    text = '<b>Select Section who you want manage:</b>'

    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

@vpn_utilities.handle_functions_error
@admin_access
async def virtual_number_admin(update, context):
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


@admin_access
async def add_credit_for_user(update, context):
    user_detail = update.effective_chat
    ft_instance = FindText(None, None)
    try:
        with SessionLocal() as session:
            with session.begin():

                amount, user_chat_id = context.args

                finacial_report = crud.create_financial_report(
                    session, 'recive',
                    chat_id=user_chat_id,
                    amount=int(amount),
                    action='increase_balance_by_admin',
                    service_id=None,
                    payment_status='not paid',
                    payment_getway='wallet',
                    currency='IRT',
                )

                crud.add_credit_to_wallet(session, finacial_report)
                text = await ft_instance.find_from_database(user_chat_id, 'amount_added_to_wallet_successfully')
                text = text.format(f"{int(amount):,}")

                await context.bot.send_message(chat_id=user_chat_id, text=text)
                await context.bot.send_message(chat_id=user_detail.id, text=f'+ successfully Add {int(amount):,} IRT to user wallet.')

    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to add credit to user wallet.\n{str(e)}')


@admin_access
async def add_partner(update, context):
    user_detail = update.effective_chat
    try:
        with SessionLocal() as session:
            with session.begin():
                chat_id, price_per_traffic, price_per_period = context.args

                admin_crud.add_partner(
                    session, True,
                    chat_id,
                    vpn_price_per_gigabyte_irt=price_per_traffic,
                    vpn_price_per_period_time_irt=price_per_period
                )
                partner.partners.refresh_partner()
                await context.bot.send_message(chat_id=user_detail.id, text=f'+ successfully Add Partner.')

    except Exception as e:
        await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to add Partner.\n{str(e)}')


@admin_access
async def say_to_every_one(update, context):
    user_detail = update.effective_chat
    message = update.message.reply_to_message.text

    with SessionLocal() as session:
        all_user = admin_crud.get_all_users(session)
        for user in all_user:
            try:
                await context.bot.send_message(chat_id=user.chat_id, text=message, parse_mode='html')
            except Exception as e:
                await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to send message.\n{str(e)}')
