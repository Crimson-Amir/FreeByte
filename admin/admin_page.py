import logging
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import message_token, FindText, FakeContext
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
import setting


REPLY_TICKET, SEND_TICKET = range(2)

@admin_access
@message_token.check_token
async def admin_page(update, context):
    user_detail = update.effective_chat

    keyboard = [[InlineKeyboardButton('VPN Section', callback_data=f"admin_vpn")]]
    text = '<b>Select Section who you want manage:</b>'

    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


async def cancel(update, context):
    user_detail = update.effective_chat
    await context.bot.send_message(chat_id=user_detail.id, text="Action cancelled.", message_thread_id=setting.ticket_thread_id)
    return ConversationHandler.END


async def reply_ticket(update, context):
    await update.callback_query.answer()
    user_detail = update.effective_chat
    query = update.callback_query
    user_id = int(query.data.replace('reply_ticket_', ''))
    print(user_id)
    context.user_data[f'ticket_user_id'] = user_id
    text = 'send message (photo or text):'
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
    return REPLY_TICKET

async def assurance(update, context):
    user_detail = update.effective_chat

    try:
        context.user_data['admin_message'] = update.message.text if update.message.text else update.message.caption
        context.user_data['file_id'] = update.message.photo[-1].file_id if update.message.photo else None
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='confirm_send')],
            [InlineKeyboardButton("Cancel", callback_data='cancel_send')]
        ]
        await context.bot.send_message(chat_id=user_detail.id, text=f'Are you sure you want to send this message?\n\n{context.user_data["admin_message"]}', reply_markup=InlineKeyboardMarkup(keyboard), message_thread_id=setting.ticket_thread_id)
        return SEND_TICKET

    except Exception as e:
        logging.error(f'error in get message.\n{e}')
        await context.bot.send_message(text=f'Error in send message: {e}', chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
        return REPLY_TICKET


async def answer_ticket(update, context):
    user_detail = update.effective_chat
    query = update.callback_query
    try:
        user_id = context.user_data['ticket_user_id']
        await query.delete_message()
        if query.data == 'cancel_send':
            await context.bot.send_message(chat_id=user_detail.id, text='Conversation closed.', message_thread_id=setting.ticket_thread_id)
            return ConversationHandler.END

        ft_instance = FindText(None, None)
        admin_message = context.user_data['admin_message'] or await ft_instance.find_from_database(user_id, 'without_caption')
        file_id = context.user_data['file_id']

        text = f'Message Recived And Send to User {user_id}'
        keyboard = [[InlineKeyboardButton('New Message +', callback_data=f"reply_ticket_{user_id}")]]

        await context.bot.send_message(text=text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard),
                                       parse_mode='html', message_thread_id=setting.ticket_thread_id)

        user_text = (f"{await ft_instance.find_from_database(user_id, 'ticket_was_answered')}"
                     f"\n\n{admin_message}")
        keyboard = [
            [InlineKeyboardButton(await ft_instance.find_from_database(user_id, 'ticket_new_message', 'keyboard'), callback_data=f"create_ticket")],
            [InlineKeyboardButton(await ft_instance.find_from_database(user_id, 'back_button', 'keyboard'), callback_data='start_in_new_message')]
        ]

        if file_id:
            await context.bot.send_photo(chat_id=int(user_id), photo=file_id, caption=user_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await context.bot.send_message(chat_id=int(user_id), text=user_text, reply_markup=InlineKeyboardMarkup(keyboard))

        return ConversationHandler.END

    except Exception as e:
        logging.error(f'erro in send ticket. {e}')
        await context.bot.send_message(text=f'Error in send message: {e}', chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
        return REPLY_TICKET


admin_ticket_reply_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(reply_ticket, pattern=r'reply_ticket_(\d+)')],
    states={
        REPLY_TICKET: [MessageHandler(filters.TEXT | filters.PHOTO, assurance)],
        SEND_TICKET: [CallbackQueryHandler(answer_ticket, pattern='^(confirm_send|cancel_send)$')],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)