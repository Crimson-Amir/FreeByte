import sys, os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, message_token, handle_error

@handle_error.handle_functions_error
@message_token.check_token
async def vn_menu(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)

    text = f"⚙️ {await ft_instance.find_text('select_section')}"

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vn_rent_number'), callback_data='vn_rent_number'),
         InlineKeyboardButton(await ft_instance.find_keyboard('vn_recive_sms'),callback_data='recive_sms_select_country__1')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='menu_services')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

