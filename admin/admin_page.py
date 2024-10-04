import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import message_token
from admin.admin_utilities import admin_access
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

@admin_access
@message_token.check_token
async def admin_page(update, context):
    user_detail = update.effective_chat

    keyboard = [[InlineKeyboardButton('VPN Section', callback_data=f"admin_vpn")]]
    text = '<b>Select Section who you want manage:</b>'

    if update.callback_query:
        return await update.callback_query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

