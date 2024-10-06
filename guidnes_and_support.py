import logging

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

import setting
from utilities_reFactore import FindText, message_token, handle_error
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
from utilities_reFactore import cancel
from setting import ADMIN_CHAT_IDs

TICKET_MESSAGE = 0

@handle_error.handle_functions_error
@message_token.check_token
async def guide_menu(update, context):
    query = update.callback_query
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)

    text = await ft_instance.find_text('guide_and_help_text')
    text = text.format(user_detail.id)

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_guide_label'), callback_data='vpn_guide_menu')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('create_ticket_label'), callback_data='create_ticket')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


async def create_ticket(update, context):
    await update.callback_query.answer()
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('create_ticket_text')
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html')
    return TICKET_MESSAGE


async def get_ticket(update, context):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    # try:

    text = await ft_instance.find_text('ticket_recived')
    file_id = update.message.photo[-1].file_id if update.message.photo else None

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('ticket_new_message'), callback_data=f"create_ticket")],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]

    await context.bot.send_message(text, chat_id=user_detail.id, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    user_message = update.message.text if update.message.text else update.message.caption or 'Witout Caption!'
    admin_text = (f"📩 New Ticket Recived"
                  "\n\n👤 User Info:"
                  f"\nUser name: {user_detail.first_name} {user_detail.last_name}"
                  f"\nUser ID: {user_detail.id}"
                  f"\nUsername: @{user_detail.username}"
                  f"\n\n💬 Message:"
                  f"\n{user_message}")
    admin_keyboard = [[InlineKeyboardButton("Reply", callback_data=f"reply_ticket_{user_detail.id}")]]

    if file_id:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_IDs[0], photo=file_id, caption=admin_text, reply_markup=InlineKeyboardMarkup(admin_keyboard), message_thread_id=setting.ticket_thread_id)
    else:
        await context.bot.send_message(chat_id=ADMIN_CHAT_IDs[0], text=admin_text, reply_markup=InlineKeyboardMarkup(admin_keyboard), message_thread_id=setting.ticket_thread_id)

    # except Exception as e:
    #     logging.error(f'erro in recive ticket:\n{e}')
    #     await context.bot.send_message(text=await ft_instance.find_text('error_in_recive_ticket'), chat_id=user_detail.id, parse_mode='html')
    #
    # finally:
    #     return ConversationHandler.END


ticket_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(create_ticket, pattern='create_ticket')],
    states={
        TICKET_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.PHOTO, get_ticket)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
