import logging
import sys, os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, handle_error, report_to_admin, cancel_user as cancel
from virtual_number import onlinesim_api, vn_utilities, vn_notification
import math
from telegram.ext import ConversationHandler, filters, MessageHandler, CallbackQueryHandler, CommandHandler
from API import convert_irt_to_usd
from crud import crud, vn_crud
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
        keyboard.append([InlineKeyboardButton(name[:45], callback_data=f'vbn__{service.get("service")}__{country_code}__{country_name}__{page}__{previous_page}')])


@handle_error.handle_functions_error
async def chooice_service_from_country(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    item_per_page = 10
    page, country_name, country_code, previous_page = query.data.replace('vn_chsfc__', '').split('__')
    page = int(page)
    country_data = vn_utilities.countries.get(country_name, {})
    country_flag = country_data.get("flag", "")
    text_template = await ft_instance.find_text('vt_select_service_text')
    text = text_template.format(country_flag, f'+{country_code}')
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
    search_type, country_id, country_name = context.user_data.get('user_search_vn', ['service', 1, 'usa'])
    filter_text = update.message.text.lower()
    keyboard = []
    text = await ft_instance.find_text('search_result')

    if search_type == 'country':
        get_tariffs = await onlinesim_api.onlinesim.get_tariffs(filter_country=filter_text)
        countries = get_tariffs.get('countries', {})

        if filter_text != 'russia': countries.pop('_7')
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
async def vn_buy_number(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    service_name, country_code, country_name, page, previous_page = query.data.replace('vbn__', '').split('__')
    price, service_name = await calculate_service_price(service_name, country_code)


    with SessionLocal() as session:
        user = crud.get_user(session, user_detail.id)
        text = (f"{await ft_instance.find_text('vn_buy_number_text')}"
                f"\n\n{await ft_instance.find_text('price')} {price:,} {await ft_instance.find_text('irt')}"
                f"\n{await ft_instance.find_text('wallet_credit_label')} {user.wallet:,} {await ft_instance.find_text('irt')}")

        if user.wallet < price:
            text += f'\n\n{await ft_instance.find_text("not_enough_credit")}'
            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('refresh'), callback_data=query.data),
                 InlineKeyboardButton(await ft_instance.find_keyboard('increase_balance'), callback_data='buy_credit_volume__in_new_message')],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('vn_recive_number'), callback_data=f'vn_recive_number__{service_name}__{country_code}')],
            ]

        keyboard.append([InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data=f'vn_chsfc__{page}__{country_name}__{country_code}__{previous_page}')])
        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


class LOWBALANCE(Exception):
    pass

class NoCompletedTzid(Exception):
    pass

class ErrorWrongTzid(Exception):
    pass

class ErrorNoService(Exception):
    pass

class ERRORNOOPERATIONS(Exception):
    pass

async def get_number_api(session, service_name, country_code, user, price):
    get_number = await onlinesim_api.onlinesim.get_number(service_name, country_code)
    response = get_number['response']

    if response == 1:
        virtual_number = vn_crud.create_virtual_number_record(
            session,
            chat_id=user.chat_id,
            service_name=service_name,
            country_code=country_code,
            number=get_number['number'],
            tzid=get_number['tzid'],
        )
        financial = crud.create_financial_report(
            session,
            operation='spend',
            chat_id=user.chat_id,
            amount=price,
            action='buy_vn_number_for_sms',
            service_id=virtual_number.virtual_number_id,
            payment_status='hold',
            payment_getway='wallet',
            currency='IRT',
        )

        vn_crud.less_credit_from_wallet(session, financial)
        return financial, virtual_number
    elif response == 'WARNING_LOW_BALANCE':
        msg = ('onlinesim balance not enoght for user purchase!'
               f'\n\npurchase amount: {price:,} IRT ($ {convert_irt_to_usd.convert_irt_to_usd(price)})')
        await report_to_admin('notification', 'get_number_api', msg, user)
        raise LOWBALANCE
    elif response == 'ERROR_NO_SERVICE':
        raise ErrorNoService
    elif response == 'NO_NUMBER':
        raise ErrorNoService
    else:
        raise Exception(response)


async def set_operation_ok_api(session, tzid, vn_id, financial_id, refund_money=True):

    get_number = await onlinesim_api.onlinesim.set_operation_ok(tzid=tzid)
    response = get_number['response']

    if response == 1:
        if refund_money:
            vn_crud.update_virtual_number_record(session, vn_id=vn_id, status='canceled')
            financial = crud.update_financial_report_status(
                session=session, financial_id=financial_id,
                new_status='refund',
                operation='recive', authority=financial_id
            )
            vn_crud.add_credit_to_wallet(session, financial)
        else:
            vn_crud.update_virtual_number_record(session, vn_id=vn_id, status='answer')
            financial = crud.update_financial_report_status(
                session=session, financial_id=financial_id,
                new_status='paid', authority=financial_id
            )

        vn_notification.modify_json(key_to_remove=str(tzid))
        vn_notification.vn_notification_instance.refresh_json()

        return financial
    elif response == 'NO_COMPLETE_TZID':
        raise NoCompletedTzid
    elif response == 'TRY_AGAIN_LATER':
        raise NoCompletedTzid
    elif response == 'ERROR_WRONG_TZID':
        raise ErrorWrongTzid
    else:
        raise Exception(response)


async def get_state_api(tzid, vn_id, financial_id):
    get_number = await onlinesim_api.onlinesim.get_state(tzid=tzid, message_to_code=1, msg_list=1)

    if isinstance(get_number, list):
        response = get_number[0]['response']
    else:
        response = get_number['response']

    if response == 'ERROR_NO_OPERATIONS':
        raise ERRORNOOPERATIONS

    elif response == 'TZ_NUM_WAIT':
        return False, get_number[0]

    elif response == 'TZ_NUM_ANSWER':
        with SessionLocal() as session:
            with session.begin():
                vn_crud.update_virtual_number_record(session, vn_id=vn_id, status='answer')
                crud.update_financial_report_status(
                    session=session, financial_id=financial_id,
                    new_status='paid', authority=financial_id
                )
        return True, get_number[0]


@handle_error.handle_functions_error
async def vn_recive_number(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    user_detail = update.effective_chat
    service_name, country_code = query.data.replace('vn_recive_number__', '').split('__')
    price, service_name = await calculate_service_price(service_name, country_code)

    with SessionLocal() as session:
        session.begin()
        user = crud.get_user(session, user_detail.id)

        if user.wallet < price:
            return await query.answer(await ft_instance.find_text("not_enough_credit"), show_alert=True)

        try:
            financial, virtual_number = await get_number_api(session, service_name, country_code, user, price)
            text = await ft_instance.find_text('buy_vn_number_page')
            text = text.format(f"<code>{virtual_number.number}</code>", '15:00')

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('vn_cancel_number'), callback_data=f'vncn__{financial.id_holder}__{virtual_number.tzid}__{financial.financial_id}'),
                 InlineKeyboardButton(await ft_instance.find_keyboard('vn_update_state'), callback_data=f'vn_update_number__{virtual_number.tzid}__{financial.id_holder}__{financial.financial_id}')],
                [InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'),callback_data=f'start_in_new_message')],
            ]
            session.commit()

            data = {
                'financial_id': financial.financial_id,
                'recived_code_count': 0,
                'chat_id': user_detail.id
            }

            vn_notification.modify_json(key_to_add=virtual_number.tzid, value_to_add=data)
            vn_notification.vn_notification_instance.refresh_json()

            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

        except LOWBALANCE:
            session.rollback()
            return await query.answer(await ft_instance.find_text("vn_our_balance_is_low"), show_alert=True)

        except ErrorNoService:
            session.rollback()
            return await query.answer(await ft_instance.find_text("vn_error_no_service"), show_alert=True)


@handle_error.handle_functions_error
async def vn_cancel_number(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    vn_id, tzid, financial_id = query.data.replace('vncn__', '').split('__')
    tzid = int(tzid)

    with SessionLocal() as session:
        session.begin()
        try:
            status, data = await get_state_api(tzid, vn_id, financial_id)
            refund_money, text_key = True, 'vn_remove_number_successful'

            if status:
                refund_money = False
                text_key = 'vn_remove_number_successful_witout_refund'

            remove_number = await set_operation_ok_api(session, tzid, vn_id, int(financial_id), refund_money)
            text = await ft_instance.find_text(text_key)
            text = text.format(f'{remove_number.amount:,}')

            keyboard = [
                [InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'),callback_data=f'start_in_new_message')],
            ]
            session.commit()
            await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

        except ERRORNOOPERATIONS:
            await query.answer(await ft_instance.find_text("vn_error_wrong_tz_id_error"), show_alert=True)
            keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'), callback_data=f'start_in_new_message')]]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

        except NoCompletedTzid:
            session.rollback()
            return await query.answer(await ft_instance.find_text("vn_no_completed_tzid_error"), show_alert=True)

        except ErrorWrongTzid:
            session.rollback()
            await query.answer(await ft_instance.find_text("vn_error_wrong_tz_id_error"), show_alert=True)
            keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('vn_update_state'), callback_data=f'vn_update_number__{vn_id}__{financial_id}'),
                         InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'),callback_data=f'start_in_new_message')]]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

def seconds_to_minutes(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02}:{remaining_seconds:02}"


@handle_error.handle_functions_error
async def vn_update_number(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    tzid, vn_id, financial_id = query.data.replace('vn_update_number__', '').split('__')
    tzid = int(tzid)
    user_lang = await ft_instance.find_user_language()

    try:
        status, data = await get_state_api(tzid, vn_id, financial_id)

        text = await ft_instance.find_text('buy_vn_number_page')
        text = text.format(f"<code>{data.get('number')}</code>", seconds_to_minutes(data.get('time', '00:00')))
        if status:
            for msg in data['msg']:
                service = vn_utilities.social_media.get(data.get("service"), {}).get("name_in_other_language", {}).get(user_lang, data.get("service"))
                text += f"\n\n{await ft_instance.find_text('service_label')} {service}\n{await ft_instance.find_text('sended_code')} <code>{msg['msg']}</code>"

        keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('vn_cancel_number'), callback_data=f'vncn__{vn_id}__{tzid}__{financial_id}'),
             InlineKeyboardButton(await ft_instance.find_keyboard('vn_update_state'), callback_data=f'vn_update_number__{tzid}__{vn_id}__{financial_id}')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'), callback_data=f'start_in_new_message')],
        ]
        await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))

    except ERRORNOOPERATIONS:
        await query.answer(await ft_instance.find_text("vn_error_wrong_tz_id_error"), show_alert=True)
        keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('bot_main_menu'), callback_data=f'start_in_new_message')]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


