from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utilities_reFactore import FindText, message_token, handle_error
from database_sqlalchemy import SessionLocal
from crud import crud


@handle_error.handle_functions_error
@message_token.check_token
async def quide_menu(update, context):
    query = update.callback_query
    user = update.effective_chat
    ft_instance = FindText(update, context)

    text = f"{await ft_instance.find_text('quide_and_help_text')}"
    text = text.format(user.id)

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_quide_lable'), callback_data='vpn_quide_menu')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

