import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import message_token, cancel, FindText, FakeContext
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
import setting


REPLY_TICKET, SEND_TICKET = 0, 1

@admin_access
@message_token.check_token
async def admin_page(update, context):
    user_detail = update.effective_chat

    keyboard = [[InlineKeyboardButton('VPN Section', callback_data=f"admin_vpn")]]
    text = '<b>Select Section who you want manage:</b>'

    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


async def reply_ticket(update, context):
    await update.callback_query.answer()
    user_detail = update.effective_chat
    query = update.callback_query
    user_id = int(query.data.replace('reply_ticket_', ''))
    print(user_id)
    context.user_data[f'ticket_user_id'] = user_id
    text = ('send message (photo or text):'
            '\n\n/cancel')
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
    return REPLY_TICKET

async def assurance(update, context):
    user_detail = update.effective_chat

    try:
        context.user_data['admin_message'] = update.message.text if update.message.text else update.message.caption
        context.user_data['file_id'] = update.message.photo[-1].file_id if update.message.photo else None
        await context.bot.send_message(chat_id=user_detail.id, text='Are you sure you wanna send this message?\n\n/yes\n/no', message_thread_id=setting.ticket_thread_id)
        return SEND_TICKET

    except Exception as e:
        await context.bot.send_message(f'Error in send message: {e}', chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
        return REPLY_TICKET


async def answer_ticket(update, context):
    user_detail = update.effective_chat
    # try:
    class Update:
        class effective_chat:
            id = user_detail.id

    if update.message.text == 'no':
        await context.bot.send_message(chat_id=user_detail.id, text='Conversation closed.', message_thread_id=setting.ticket_thread_id)
        return ConversationHandler.END

    fake_context = FakeContext()
    fake_update = Update()

    ft_instance = FindText(fake_update, fake_context)

    admin_message = context.user_data[f'admin_message'] or await ft_instance.find_text('without_caption')
    file_id = context.user_data[f'file_id']

    user_id = context.user_data[f'ticket_user_id']
    text = f'Message Recived And Send to User {user_id}'
    keyboard = [[InlineKeyboardButton('New Message +', callback_data=f"reply_ticket_{user_id}")]]

    await context.bot.send_message(text=text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard),
                                   parse_mode='html', message_thread_id=setting.ticket_thread_id)


    user_text = (f"{await ft_instance.find_text('ticket_was_answered')}"
                 f"\n\n{admin_message}")

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('ticket_new_message'), callback_data=f"create_ticket")],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]

    if file_id:
        await context.bot.send_photo(chat_id=int(user_id), photo=file_id, caption=user_text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await context.bot.send_message(chat_id=int(user_id), text=user_text, reply_markup=InlineKeyboardMarkup(keyboard))

    return ConversationHandler.END

    # except Exception as e:
    #     await context.bot.send_message(text='Error in send message: {e}', chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
    #     return REPLY_TICKET

admin_ticket_reply_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(reply_ticket, pattern='reply_ticket_(.*)')],
    states={
        REPLY_TICKET: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.PHOTO, assurance)],
        SEND_TICKET: [MessageHandler(filters.COMMAND, answer_ticket)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
