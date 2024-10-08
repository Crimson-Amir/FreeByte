import sys, os, math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from admin.admin_utilities import admin_access, cancel_conversation as cancel
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from crud import admin_crud, crud
from database_sqlalchemy import SessionLocal
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler

ADD_CREDIT_BAlANCE = 0

service_status = {
    'active': '✅',
    'limited': '🟡',
    'ban': '🔴'
}

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
                nav_buttons.append(InlineKeyboardButton('Previous', callback_data=f'admin_manage_users__{page - 1}'))
            if page < total_pages:
                nav_buttons.append(InlineKeyboardButton('Next', callback_data=f'admin_manage_users__{page + 1}'))
            if nav_buttons: keyboard.append(nav_buttons)
            keyboard.append([InlineKeyboardButton('Back', callback_data='admin_page')])

            return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@admin_access
async def find_user(update, context):
    chat_id_substring = context.args
    user_detail = update.effective_chat

    with SessionLocal() as session:
        with session.begin():
            users = crud.get_user(session, chat_id_substring)
            text = 'select user to manage:'

            keyboard = [[InlineKeyboardButton(
                f"{user.first_name} {user.chat_id} {service_status.get(user.config.user_status)}",
                callback_data=f'admin_view_user__{user.chat_id}__{1}')] for user in users]

            keyboard.append([InlineKeyboardButton('Back', callback_data='admin_page')])

            return await context.bot.send_message(chat_id=user_detail.id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@admin_access
async def view_user_info(update, context, chat_id=None):
    query = update.callback_query
    chat_id, page = [chat_id, 1] or query.data.replace('admin_view_user__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            user = crud.get_user(session, int(chat_id))

            text = f'{chat_id}'

            keyboard = [
                [InlineKeyboardButton('Set User Status:', callback_data=f'')],
                [InlineKeyboardButton(f"Active", callback_data=f'admin_set_user_status__{chat_id}__active'),
                 InlineKeyboardButton(f"Ban", callback_data=f'admin_set_user_status__{chat_id}__ban')],

                [InlineKeyboardButton('Change Wallet Balance:', callback_data=f'')],
                [InlineKeyboardButton(f"Add", callback_data=f'admin_change_user_wallet_balance__{chat_id}__increase_balance_by_admin'),
                 InlineKeyboardButton(f"Set", callback_data=f'admin_change_user_wallet_balance__{chat_id}__set'),
                 InlineKeyboardButton(f"Less", callback_data=f'admin_change_user_wallet_balance__{chat_id}__reduction_balance_by_admin')],

                [InlineKeyboardButton('Back', callback_data=f'admin_manage_users__{page}')]
            ]


            return await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@admin_access
async def admin_change_user_status(update, context):
    query = update.callback_query
    chat_id, status = query.data.replace('admin_set_user_status__', '').split('__')

    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(session, int(chat_id), user_status=status)
            await query.answer('+ Changes Saved!')
            return await view_user_info(update, context, chat_id)


@admin_access
async def get_new_balance(update, context):
    await update.callback_query.answer()
    user_detail = update.effective_chat
    query = update.callback_query
    chat_id, action = query.data.replace('admin_change_user_wallet_balance__', '').split('__')
    context.user_data[f'admin_increase_user_balance_chat_id'] = chat_id
    context.user_data[f'admin_increase_user_balance_action'] = action
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel_increase_wallet_conversation')]]
    text = 'send amount in IRT:'
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CREDIT_BAlANCE


@admin_access
async def admin_change_wallet_balance(update, context):
    user_detail = update.effective_chat
    query = update.callback_query
    try:
        await query.delete_message()
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

                text = f'+ Operation Successfull.\namoutn: {amount}\nchat id: {chat_id}\naction: {action}'

                if action == 'increase_balance_by_admin':
                    crud.add_credit_to_wallet(session, finacial_report)
                elif action == 'set':
                    crud.update_user(session, chat_id, wallet=amount)
                elif action == 'reduction_balance_by_admin':
                    crud.less_from_wallet(session, finacial_report)

                await query.answer('+ Changes Saved!')
                keyboard = [[InlineKeyboardButton('User Detail', callback_data=f"admin_view_user__{chat_id}__1")]]
                await context.bot.send_message(text=text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

                return ConversationHandler.END

    except Exception as e:
        await context.bot.send_message(text=f'Error in add amount: {e}', chat_id=user_detail.id, parse_mode='html')


admin_change_wallet_balance_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_new_balance, pattern=r'admin_change_user_wallet_balance__(.*)')],
    states={
        ADD_CREDIT_BAlANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_change_wallet_balance)],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='cancel_increase_wallet_conversation')],
    conversation_timeout=600

)




