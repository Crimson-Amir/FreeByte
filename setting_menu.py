from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utilities_reFactore import FindText, message_token, handle_error


@handle_error.handle_functions_error
@message_token.check_token
async def setting_menu(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)

    text = await ft_instance.find_text('select_section')

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_setting_lable'), callback_data='vpn_setting_menu')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

