import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import message_token, cancel, FindText, FakeContext
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
import setting


REPLY_TICKET = 0

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
    context.user_data[f'ticket_user_id'] = user_id
    text = ('send message (photo or text):'
            '\n\n/cancel')
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', message_thread_id=setting.ticket_thread_id)
    return REPLY_TICKET

async def get_ticket(update, context):
    user_detail = update.effective_chat

    try:
        class Update:
            class effective_chat:
                id = user_detail.id

        fake_context = FakeContext()
        fake_update = Update()

        ft_instance = FindText(fake_update, fake_context)

        text = 'Message Recived And Send to User {}!'
        file_id = update.message.photo[-1].file_id if update.message.photo else None
        user_id = context.user_data[f'ticket_user_id']
        keyboard = [[InlineKeyboardButton('New Message +', callback_data=f"reply_ticket_{user_id}")]]

        await context.bot.send_message(text=text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html', message_thread_id=setting.ticket_thread_id)

        admin_message = update.message.text if update.message.text else update.message.caption or await ft_instance.find_text('without_caption')

        user_text = (f"{await ft_instance.find_text('ticket_was_answered')}"
                     f"\n\n{admin_message}")

        keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('ticket_new_message'), callback_data=f"create_ticket")],
            [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
        ]

        if file_id:
            context.bot.send_photo(chat_id=user_id, photo=file_id, caption=user_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            context.bot.send_message(chat_id=user_id, text=user_text, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await context.bot.send_message(f'Error in send message: {e}', chat_id=user_detail.id, parse_mode='html')

    finally:
        return ConversationHandler.END


admin_ticket_reply_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(reply_ticket, pattern='reply_ticket_(.*)')],
    states={
        REPLY_TICKET: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.PHOTO, get_ticket)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
