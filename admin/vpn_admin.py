import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import message_token, cancel
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
from crud import admin_crud
from enum import Enum
from database_sqlalchemy import SessionLocal


class AdminState(Enum):
    GET_PRODUCT_DETAIL = 1
    GET_MAINSERVER_DETAIL = 2


@admin_access
@message_token.check_token
async def admin_page(update: Update, context):
    user_detail = update.effective_chat
    keyboard = [
        [InlineKeyboardButton('Add Product', callback_data='admin_add_product'),
         InlineKeyboardButton('Add MainServer', callback_data='admin_add_mainserver')],
        [InlineKeyboardButton('Back', callback_data='admin_page')]
    ]
    text = '<b>Select Section to manage:</b>'
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, parse_mode='html', reply_markup=reply_markup)

    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=reply_markup, parse_mode='html')


async def ask_for_details(update: Update, context, detail_type: str) -> int:
    user_detail = update.effective_chat
    messages = {
        "product": ("Send new product detail in this format:"
                    "\n\n<code>active (Bool)\nproduct_name (Str)\nmain_service_id (Str)</code>\n\n/cancel"),

        "mainserver": ("Send new mainserver detail in this format:"
                       "\n\n<code>active (Bool)\nserver_ip (Str)\nserver_protocol (Str)\n"
                       "server_port (Int)\nserver_username (Str)\nserver_password (Str)</code>\n\n/cancel")
    }
    await context.bot.send_message(text=messages[detail_type], chat_id=user_detail.id, parse_mode='html')
    return AdminState.GET_PRODUCT_DETAIL if detail_type == "product" else AdminState.GET_MAINSERVER_DETAIL


@admin_access
async def admin_add_product(update: Update, context) -> int:
    return await ask_for_details(update, context, 'product')


@admin_access
async def admin_add_mainserver(update: Update, context) -> int:
    return await ask_for_details(update, context, 'mainserver')


async def process_details(update: Update, context, entity_type: str):
    user_detail = update.effective_chat
    user_text = update.message.text

    try:
        with SessionLocal() as session:
            with session.begin():
                if entity_type == 'product':
                    active, product_name, main_service_id = user_text.split('\n')
                    active = active == 'True'
                    new_entry = admin_crud.add_product(session, active, product_name, main_service_id)
                    new_id = new_entry.product_id
                else:
                    active, server_ip, server_protocol, server_port, server_username, server_password = user_text.split('\n')
                    active = active == 'True'
                    new_entry = admin_crud.add_mainserver(session, active, server_ip, server_protocol, server_port, server_username, server_password)
                    new_id = new_entry.server_id

                text = f'New {entity_type} added successfully\nID: {new_id}'
                await context.bot.send_message(text=text, chat_id=user_detail.id)
                return ConversationHandler.END

    except Exception as e:
        await context.bot.send_message(text=f"An error occurred.\n{str(e)}", chat_id=user_detail.id)
        return ConversationHandler.END


@admin_access
async def get_product_detail(update: Update, context) -> int:
    return await process_details(update, context, 'product')


@admin_access
async def get_mainserver_detail(update: Update, context) -> int:
    return await process_details(update, context, 'mainserver')


admin_add_product_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_add_product, pattern='admin_add_product')],
    states={
        AdminState.GET_PRODUCT_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_detail)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

admin_add_mainserver_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_add_mainserver, pattern='admin_add_mainserver')],
    states={
        AdminState.GET_MAINSERVER_DETAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mainserver_detail)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
