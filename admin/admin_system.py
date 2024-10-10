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
            keyboard = [[InlineKeyboardButton(f"{product.product_id} {product.product_name} {service_status.get(product.active)}", callback_data=f'admin_view_product__{product.product_id}__{page}')] for product in current_products]
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
                f'\nRegister Date: {product.register_date} ({utilities_reFactore.human_readable(product.register_date, "en")})'
                f'\nAll Purchase: {len(product.purchase)}'
                f'\nActive Purchase: {len([purchase for purchase in product.purchase if purchase.status == "active" and purchase.active == True])}'
            )

            keyboard = [
                [InlineKeyboardButton('Refresh', callback_data=f'admin_view_product__{product_id}__{page}')],
                [InlineKeyboardButton('🔰 Set Product Status:', callback_data=f'just_for_show')],
                [InlineKeyboardButton(f"Active", callback_data=f'admin_set_product_status__{product_id}__true__{page}'),
                 InlineKeyboardButton(f"Deactive", callback_data=f'admin_set_product_status__{product_id}__false__{page}')],
                [InlineKeyboardButton('View Main Server Info', callback_data=f'admin_product_main_server_info__{product_id}__{page}')],
                [InlineKeyboardButton('Back', callback_data=f'admin_system__{page}')]
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
async def view_product_main_server_info(update, context):
    query = update.callback_query
    product_id, page = query.data.replace('admin_product_main_server_info__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            product = admin_crud.get_product(session, int(product_id))
            system = panel_api.marzban_api.get_system_stats(product.main_server.server_ip)

            text = (
                f'Version: {system.get("version")}'
                f'\nMemory Total: {system.get("mem_total")}'
                f'\nMemory Used: {system.get('mem_used')}'
                f'\nCPU cores: {system.get("cpu_cores")}'
                f'\nCPU Usage: {system.get("cpu_usage")}'
                f'\nTotal User: {system.get("total_user")}'
                f'\nActive Users: {system.get("users_active")}'
                f'\nIncoming Bandwidth: {system.get("incoming_bandwidth")}'
                f'\nOutgoing Bandwidth: {system.get("outgoing_bandwidth")}'
                f'\nIncoming Bandwidth Speed: {system.get("incoming_bandwidth_speed")}'
                f'\nOutgoing Bandwidth Speed: {system.get("outgoing_bandwidth_speed")}'

            )

            keyboard = [
                [InlineKeyboardButton('Refresh', callback_data=f'admin_product_main_server_info__{product_id}__{page}'),
                InlineKeyboardButton('Back', callback_data=f'admin_view_product__{product_id}__{page}')]
            ]

            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

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