import logging
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
import setting
from vpn_service import vpn_utilities

REPLY_TICKET, SEND_TICKET = range(2)

async def cancel(update, context):
    query = update.callback_query
    await query.delete_message()
    user_detail = update.effective_chat
    await context.bot.send_message(chat_id=user_detail.id, text="Action cancelled.", message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None)
    return ConversationHandler.END


async def reply_ticket(update, context):
    await update.callback_query.answer()
    user_detail = update.effective_chat
    query = update.callback_query
    data = query.data
    if 'private' in query.data:
        data = data.replace('private_', '')
        context.user_data[f'ticket_private'] = True

    user_id = int(data.replace('reply_ticket_', ''))
    context.user_data[f'ticket_user_id'] = user_id
    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel_reply_ticket_conversation')]]
    text = 'send message (photo or text):'
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None, reply_markup=InlineKeyboardMarkup(keyboard))
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
        await context.bot.send_message(chat_id=user_detail.id, text=f'Are you sure you want to send this message?\n\n{context.user_data["admin_message"]}', reply_markup=InlineKeyboardMarkup(keyboard), message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None)
        return SEND_TICKET

    except Exception as e:
        logging.error(f'error in get message.\n{e}')
        await context.bot.send_message(text=f'Error in send message: {e}', chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None)
        return ConversationHandler.END


async def answer_ticket(update, context):
    user_detail = update.effective_chat
    query = update.callback_query
    try:
        user_id = context.user_data['ticket_user_id']
        await query.delete_message()
        if query.data == 'cancel_send':
            await context.bot.send_message(chat_id=user_detail.id, text='Conversation closed.',message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None)
            return ConversationHandler.END

        ft_instance = FindText(None, None)
        admin_message = context.user_data['admin_message'] or await ft_instance.find_from_database(user_id, 'without_caption')
        file_id = context.user_data['file_id']

        user_text = (f"{await ft_instance.find_from_database(user_id, 'ticket_was_answered')}"
                     f"\n\n{admin_message}")
        keyboard = [
            [InlineKeyboardButton(await ft_instance.find_from_database(user_id, 'ticket_new_message', 'keyboard'), callback_data=f"create_ticket")],
            [InlineKeyboardButton(await ft_instance.find_from_database(user_id, 'back_button', 'keyboard'), callback_data='start_in_new_message')]
        ]

        if file_id:
            new_message = await context.bot.send_photo(chat_id=int(user_id), photo=file_id, caption=user_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            new_message = await context.bot.send_message(chat_id=int(user_id), text=user_text, reply_markup=InlineKeyboardMarkup(keyboard))

        text = f'Message Recived And Send to User {user_id}'
        keyboard = [
            [InlineKeyboardButton('Send New Message +', callback_data=f"reply_ticket_{user_id}")],
            [InlineKeyboardButton('Delete message for User', callback_data=f"dell_mess_asu__{user_id}__{new_message.message_id}")]
        ]

        await context.bot.send_message(text=text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard),
                                       parse_mode='html', message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None)

        context.user_data[f'ticket_private'] = False
        return ConversationHandler.END

    except Exception as e:
        logging.error(f'erro in send ticket. {e}')
        await context.bot.send_message(text=f'Error in send message: {e}', chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id if not context.user_data.get(f'ticket_private') else None)
        return ConversationHandler.END


admin_ticket_reply_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(reply_ticket, pattern=r'reply_ticket_(.*)')],
    states={
        REPLY_TICKET: [MessageHandler(filters.TEXT | filters.PHOTO, assurance)],
        SEND_TICKET: [CallbackQueryHandler(answer_ticket, pattern='^(confirm_send|cancel_send)$')],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='cancel_reply_ticket_conversation')],
    conversation_timeout=600

)

@vpn_utilities.handle_functions_error
async def delete_message_assuarance(update, context):
    user_detail = update.effective_chat
    query = update.callback_query
    user_id, message_id = query.data.replace('dell_mess_asu__', '').split('__')

    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f'dell_message__{user_id}__{message_id}')],
        [InlineKeyboardButton("Cancel", callback_data=f'cancel_dell__{user_id}')]
    ]
    await context.bot.send_message(
        chat_id=user_detail.id,
        text='are you syre you wanna delete this message?',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@vpn_utilities.handle_functions_error
async def delete_message(update, context):
    query = update.callback_query
    user_id, message_id = query.data.replace('dell_message__', '').split('__')
    await context.bot.delete_message(chat_id=int(user_id), message_id=int(message_id))
    await query.answer('message deleted!')
    await query.edit_message_text(text='message_deleted_successfully for user!')


@vpn_utilities.handle_functions_error
async def cancel_deleteing_message(update, context):
    query = update.callback_query
    user_id = query.data.replace('cancel_dell__', '')
    keyboard = [[InlineKeyboardButton('Send New Message +', callback_data=f"reply_ticket_{user_id}")]]
    await query.answer('operation canceled!')
    await query.edit_message_text(text='Operation Canceled', reply_markup=InlineKeyboardMarkup(keyboard))
