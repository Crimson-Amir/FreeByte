from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utilities_reFactore import FindText, message_token, handle_error

@handle_error.handle_functions_error
@message_token.check_token
async def guide_menu(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat

    text = f"{await ft_instance.find_text('select_section')}"

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('android_lable'), callback_data='vpn_guide__android'),
         InlineKeyboardButton(await ft_instance.find_keyboard('ios_lable'), callback_data='vpn_guide__ios')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('windows_lable'), callback_data='vpn_guide__windows'),
         InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='guide_menu')]
    ]

    if "in_new_message" in query.data:
        return await context.bot.send_message(chat_id=user_detail.id, text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def vpn_guide(update, context):

    query = update.callback_query
    ft_instance = FindText(update, context)
    platform = query.data.replace('vpn_guide__', '')

    if platform == 'android':
        text = f"{await ft_instance.find_text('vpn_android_guide')}"
        text += '\n\n<a href="https://play.google.com/store/apps/details?id=com.v2ray.ang&hl=en&pli=1">Google Play</a>'
        text += '\n<a href="https://github.com/2dust/v2rayng/releases">GitHub</a>'

    elif platform == 'ios':
        text = f"{await ft_instance.find_text('vpn_ios_guide')}"
        text += '\n\n<a href="https://apps.apple.com/us/app/streisand/id6450534064">Streisand</a>'
        text += '\n<a href="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690">V2Box</a>'

    elif platform == 'windows':
        text = f"{await ft_instance.find_text('vpn_windows_guide')}"
        text += '\n\n<a href="https://github.com/2dust/v2rayN/releases/download/6.23/v2rayN-With-Core.zip">v2rayN</a>'

    else:
        text = f"{await ft_instance.find_text('error_message')}"

    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='vpn_guide_menu')]]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
