import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import crud, admin_crud
from database_sqlalchemy import SessionLocal
from vpn_service import vpn_utilities
from admin import partner
from virtual_number import onlinesim_api
import asyncio

@admin_access
async def admin_page(update, context):
    user_detail = update.effective_chat

    keyboard = [
        [InlineKeyboardButton('System', callback_data=f"admin_system__1"),
         InlineKeyboardButton('Virtual Number', callback_data=f"admin_virtual_number")],
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
    get_balance = await onlinesim_api.onlinesim.get_balance()

    text = (f'Currnet Balance: ${get_balance.get("balance")}'
            f'\nZBalance: ${get_balance.get("zbalance")}')

    keyboard = [[InlineKeyboardButton('Back', callback_data='admin_page')]]

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
async def say_to_users(update, context):
    user_detail = update.effective_chat
    message = update.message.reply_to_message.text

    with SessionLocal() as session:
        all_user = admin_crud.get_all_purchase(session)
        users = set()
        for user in all_user:
            if user.chat_id in users:
                continue
            try:
                users.add(user.chat_id)
                await context.bot.send_message(
                    chat_id=user.chat_id,
                    text=message,
                    parse_mode='html'
                )
                await asyncio.sleep(1)
            except Exception as e:
                await context.bot.send_message(
                    chat_id=user_detail.id,
                    text=f'- failed to send message.\n{str(e)}'
                )
                await asyncio.sleep(1)


@admin_access
async def say_to_everyone(update, context):
    user_detail = update.effective_chat
    message = update.message.reply_to_message.text

    with SessionLocal() as session:
        all_user = admin_crud.get_all_users(session)
        users = {}
        for user in all_user:
            if user.chat_id not in [6450325872]: continue
            if user in users: continue
            try:
                users.add(user.chat_id)
                await context.bot.send_message(chat_id=user.chat_id, text=message, parse_mode='html')
                await asyncio.sleep(3)
            except Exception as e:
                await context.bot.send_message(chat_id=user_detail.id, text=f'- failed to send message.\n{str(e)}')
                await asyncio.sleep(3)