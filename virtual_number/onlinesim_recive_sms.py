import logging
import sys, os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, message_token, handle_error
from virtual_number import onlinesim_api, vn_utilities
import math
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
from API import convert_irt_to_usd
from utilities_reFactore import cancel_user as cancel
from crud import crud
from database_sqlalchemy import SessionLocal

SEARCH_VN = 0

async def create_country_pagination(countries, ft_instance, keyboard, page, item_per_page):

    start, end = (page - 1) * item_per_page, page * item_per_page
    user_lang = await ft_instance.find_user_language()

    row_keyboard = []
    for index, country in enumerate(countries.values()):
        if index < start: continue
        if index >= end: break

        country_data = vn_utilities.countries.get(country.get("original"), {})
        country_flag = country_data.get("flag", "")
        country_name = country_data.get("name_in_other_language", {}).get(user_lang, country.get(
            "original")) if user_lang != 'en' else country.get("original")

        row_keyboard.append(InlineKeyboardButton(f'{country_flag} {country_name[:10]}', callback_data=f'vn_chsfc__1__{country.get("original")}__{country.get("code")}__{page}'))

        if len(row_keyboard) == 3:
            keyboard.append(row_keyboard)
            row_keyboard = []

    if row_keyboard:
        keyboard.append(row_keyboard)

@handle_error.handle_functions_error
@message_token.check_token
async def recive_sms_select_country(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    page = int(query.data.replace('recive_sms_select_country__', ''))
    back_button_key = await ft_instance.find_keyboard('back_button')
    text, no_country_found = await ft_instance.find_text('vt_select_country_text'), await ft_instance.find_text('no_country_found')
    search_country_key, search_service_key = await ft_instance.find_keyboard('vn_search_country'), await ft_instance.find_keyboard('vn_search_service')

    get_tariffs = await onlinesim_api.onlinesim.get_tariffs(count=1)
    countries = get_tariffs.get('countries', {})
    item_per_page = 30
    total_pages = math.ceil(len(countries) / item_per_page)
    if not countries:
        return await query.answer(no_country_found)

    keyboard = [
        [InlineKeyboardButton(search_country_key, callback_data='vn_search__country__None__None')]
    ]
    await create_country_pagination(countries, ft_instance, keyboard, page, item_per_page)
    previous_key, next_key = await ft_instance.find_keyboard('previous'), await ft_instance.find_keyboard('next')
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(previous_key, callback_data=f'recive_sms_select_country__{page - 1}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(next_key, callback_data=f'recive_sms_select_country__{page + 1}'))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(back_button_key, callback_data='virtual_number_menu')])

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


async def create_service_keyboard(services, country_code, country_name, ft_instance, keyboard, page, previous_page):
    user_lang = await ft_instance.find_user_language()

    for service in services.values():
        service_name = vn_utilities.social_media.get(service.get("service"), {}).get("name_in_other_language", {}).get(user_lang, service.get("service")) if user_lang != 'en' else service.get("service")
        service_price = convert_irt_to_usd.convert_usd_to_irt(float(service.get("price", 0)))

        available = f'- ? {await ft_instance.find_text("available")}'
        if isinstance(service.get("count", 0), int):
            available = f'- {service.get("count", 0)} {await ft_instance.find_text("available")}' if service.get("count", 0) < 50 else ''

        name = f'{service_name} - {service_price:,} {await ft_instance.find_text("irt")} {available}'
        keyboard.append([InlineKeyboardButton(name[:45], callback_data=f'vn_buy_number__{service.get("service")}__{country_code}__{country_name}__{page}__{previous_page}')])


@handle_error.handle_functions_error
@message_token.check_token
async def chooice_service_from_country(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    item_per_page = 10
    page, country_name, country_code, previous_page = query.data.replace('vn_chsfc__', '').split('__')
    page = int(page)
    country_data = vn_utilities.countries.get(country_name, {})
    country_flag = country_data.get("flag", "")
    text_template = await ft_instance.find_text('vt_select_service_text')
    text = text_template.format(country_flag)

    get_tariffs = await onlinesim_api.onlinesim.get_tariffs(count=item_per_page, country=country_code, page=page)

    services = get_tariffs.get('services', {})
    total_pages = math.ceil(len(services) + 1 / item_per_page)

    if not get_tariffs.get('services'):
        return await query.answer(await ft_instance.find_text('no_service_found'))

    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('vn_search_service'), callback_data=f'vn_search__service__{country_code}__{country_name}')]]
    await create_service_keyboard(services, country_code, country_name, ft_instance, keyboard, page, previous_page)

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(await ft_instance.find_keyboard('previous'), callback_data=f'vn_chsfc__{page - 1}__{country_name}__{country_code}__{previous_page}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(await ft_instance.find_keyboard('next'), callback_data=f'vn_chsfc__{page + 1}__{country_name}__{country_code}__{previous_page}'))
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'recive_sms_select_country__{previous_page}')])

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_conversetion_error
async def get_search_key(update, context):
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('cancel_button'), callback_data='cancel_search')]]

    text = await ft_instance.find_text('vn_search_text')
    context.user_data['user_search_vn'] = update.callback_query.data.replace('vn_search__', '').split('__')
    await update.callback_query.answer()
    await context.bot.send_message(text=text, chat_id=user_detail.id, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
    return SEARCH_VN

@handle_error.handle_conversetion_error
async def find_search_result(update, context):
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    search_type, country_id, country_name = context.user_data.get('user_search_vn', ['service', 1])
    filter_text = update.message.text
    keyboard = []
    text = await ft_instance.find_text('search_result')

    if search_type == 'country':
        get_tariffs = await onlinesim_api.onlinesim.get_tariffs(filter_country=filter_text)
        countries = get_tariffs.get('countries', {})
        if int(country_id) != 7: countries.pop('_7')
        if not countries:
            text = await ft_instance.find_text('no_country_found')
        else:
            await create_country_pagination(countries, ft_instance, keyboard, 1, 40)
    else:
        get_tariffs = await onlinesim_api.onlinesim.get_tariffs(filter_service=filter_text, country=country_id)
        services = get_tariffs.get('services', {})
        if not services:
            text = await ft_instance.find_text('no_service_found')
        else:
            await create_service_keyboard(services, country_id, country_name, ft_instance, keyboard, 1, 1)

    keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'recive_sms_select_country__1')])
    await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END


vn_search_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_search_key, pattern=r'vn_search__(.*)')],
    states={
        SEARCH_VN: [MessageHandler(filters.TEXT, find_search_result)],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='cancel_search')],
    conversation_timeout=400
)

async def calculate_service_price(service_name, country_code):
    get_tariffs = await onlinesim_api.onlinesim.get_tariffs(count=1, country=country_code, filter_service=service_name)
    services = get_tariffs.get('services', {})
    if not services:
        logging.error(f'error in find service. reason:\n{get_tariffs.status_code} | {get_tariffs.json()}')
        raise ValueError('service not found')
    service = next(iter(services.values()))
    print(service)
    price = convert_irt_to_usd.convert_usd_to_irt(float(service["price"]))
    service_name = service["service"]
    return price, service_name


@handle_error.handle_functions_error
@message_token.check_token
async def vn_buy_number(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    service_name, country_code, country_name, page, previous_page = query.data.replace('vn_buy_number__', '').split('__')
    price, service_name = await calculate_service_price(service_name, country_code)


    with SessionLocal() as session:
        user = crud.get_user(session, user_detail.id)
        text = (f"{await ft_instance.find_text('vn_buy_number_text')}"
                f"\n\n{await ft_instance.find_text('price')} {price:,} {await ft_instance.find_text('irt')}"
                f"\n{await ft_instance.find_text('wallet_credit_label')} {user.wallet:,} {await ft_instance.find_text('irt')}")

        if user.wallet < price:
            text += f'\n\n{await ft_instance.find_text("not_enough_credit")}'
            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('increase_balance'), callback_data='buy_credit_volume')],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('vn_recive_number.'), callback_data='buy_credit_volume')],
            ]
        keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vn_chsfc__{page}__{country_name}__{country_code}__{previous_page}')])
        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))
