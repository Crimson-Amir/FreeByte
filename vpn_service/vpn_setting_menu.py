import sys, os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utilities_reFactore import FindText, message_token, handle_error
from crud import crud
from database_sqlalchemy import SessionLocal


@handle_error.handle_functions_error
@message_token.check_token
async def setting_menu(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)

    text = await ft_instance.find_text('select_section')

    keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('vpn_notification_setting'), callback_data='vpn_set_notification_period_traffic__db')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='setting_menu')]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def handle_vpn_notification(update, context):
    query = update.callback_query
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    query_data = query.data.replace('vpn_set_notification_period_traffic__', '')

    if query_data == 'db':
        with SessionLocal() as session:
            with session.begin():
                config = crud.get_user_config(session, user_detail.id)
                traffic_percent = config.traffic_notification_percent
                period_percent = config.period_notification_day
    else:
        period_percent_callback, traffic_percent_callback = query_data.split('__')
        traffic_percent = max(min(int(traffic_percent_callback), 5), 95)
        period_percent = max(min(int(period_percent_callback), 1), 10)

    show_status_text = await ft_instance.find_text('vpn_set_notification_status')
    show_status_text = show_status_text.format(traffic_percent, period_percent)
    text = f"<b>{await ft_instance.find_text('vpn_setting_section_lable')}</b>\n\n{show_status_text}"

    keyboard = [
        [InlineKeyboardButton("➖", callback_data=f"vpn_set_notification_period_traffic__{period_percent}__{traffic_percent - 5}"),
         InlineKeyboardButton(f"{traffic_percent}%", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"vpn_set_notification_period_traffic__{period_percent}_{traffic_percent + 10}")],
        [InlineKeyboardButton("➖", callback_data=f"vpn_set_notification_period_traffic__{period_percent - 5}_{traffic_percent}"),
         InlineKeyboardButton(f"{period_percent} {await ft_instance.find_keyboard('day_lable')}", callback_data="just_for_show"),
         InlineKeyboardButton("➕", callback_data=f"vpn_set_notification_period_traffic__{period_percent + 10}_{traffic_percent}")],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='vpn_setting_menu'),
         InlineKeyboardButton(await ft_instance.find_keyboard('confirm'), callback_data=f"vpn_apply_notification_period_traffic__{period_percent}__{traffic_percent}")]
    ]

    await query.edit_message_text(text=text, parse_mode='html', reply_markup=InlineKeyboardMarkup(keyboard))


@handle_error.handle_functions_error
@message_token.check_token
async def apply_notification_setting(update, context):
    query = update.callback_query
    user_detail = update.effective_chat
    ft_instance = FindText(update, context)
    query_data = query.data.replace('vpn_apply_notification_period_traffic__', '')

    period_percent_callback, traffic_percent_callback = query_data.split('__')
    traffic_percent = max(min(int(traffic_percent_callback), 5), 95)
    period_percent = max(min(int(period_percent_callback), 1), 10)

    with SessionLocal() as session:
        with session.begin():
            crud.update_user_config(
                session,
                user_detail.id,
                traffic_notification_percent=traffic_percent,
                period_notification_day=period_percent
            )

    await query.answer(ft_instance.find_text('config_applied_successfully'), show_alert=True)