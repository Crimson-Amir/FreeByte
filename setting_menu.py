from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from utilities_reFactore import FindText, message_token, handle_error
from database_sqlalchemy import SessionLocal
from crud import crud

@handle_error.handle_functions_error
@message_token.check_token
async def setting_menu(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)

    text = f"⚙️ {await ft_instance.find_text('select_section')}"

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('change_language_setting'),callback_data='user_language_setting'),
         InlineKeyboardButton(await ft_instance.find_keyboard('vpn_setting_label'), callback_data='vpn_setting_menu')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))



@handle_error.handle_functions_error
@message_token.check_token
async def user_language_setting(update, context):
    query = update.callback_query
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)

    with SessionLocal() as session:
        with session.begin():
            user = crud.get_user(session, user_detail.id)

            text = await ft_instance.find_text('please_select_your_language')

            languages = {
                'fa':  '🇮🇷 فارسی',
                'en': '🇬🇧 English',
            }

            keyboard = []
            for language, name in languages.items():
                if user.language == language:
                    keyboard.append([InlineKeyboardButton(f"{name} ✅", callback_data=f"already_on_this")])
                    continue
                keyboard.append([InlineKeyboardButton(f"{name}", callback_data=f"set_user_language_on__{language}")])

            keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='setting_menu')])
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

@handle_error.handle_functions_error
@message_token.check_token
async def change_user_language(update, context):
    query = update.callback_query
    with SessionLocal() as session:
        with session.begin():
            user_detail = update.effective_chat
            ft_instance = FindText(update, context)
            user_new_language = query.data.replace('set_user_language_on__', '')

            crud.update_user(session, user_detail.id, language=user_new_language)
            context.user_data['user_language'] = user_new_language


            await query.answer(await ft_instance.find_text('config_applied_successfully'))
            return await user_language_setting(update, context)