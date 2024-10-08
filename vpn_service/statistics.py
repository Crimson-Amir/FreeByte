import json, traceback
from datetime import datetime, timedelta
import telegram.error, pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
import sys, os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vpn_service import panel_api, plot, vpn_utilities
from crud import vpn_crud
from utilities_reFactore import FindText, handle_error, report_to_admin
from database_sqlalchemy import SessionLocal

STATISTICS_TIMER_HORSE = 3

async def make_day_name_farsi(ft_instance, day):
    days_mapping = {
        'Saturday': await ft_instance.find_text('saturday'),
        'Sunday': await ft_instance.find_text('sunday'),
        'Monday': await ft_instance.find_text('monday'),
        'Tuesday': await ft_instance.find_text('tuesday'),
        'Wednesday': await ft_instance.find_text('wednesday'),
        'Thursday': await ft_instance.find_text('thursday'),
        'Friday': await ft_instance.find_text('friday'),
    }

    return days_mapping[day]


async def statistics_timer(context):
    try:
        with SessionLocal() as session:
            with session.begin():
                users_last_usage = vpn_crud.get_users_last_usage(session)

                if not users_last_usage:
                    users_last_usage = {}
                else:
                    users_last_usage = json.loads(users_last_usage.last_usage)

                all_product = vpn_crud.get_all_product(session)
                last_usage_dict, statistics_usage_traffic = {}, {}
                for product in all_product:
                    get_users_usage = await panel_api.marzban_api.get_users(product.main_server.server_ip)
                    for purchase in product.purchase:
                        if purchase.status != 'active': continue
                        for user in get_users_usage['users']:
                            if user['username'] == purchase.username:

                                last_traffic_usage = users_last_usage.get(str(purchase.purchase_id))
                                usage_traffic_in_megabyte = round(user['used_traffic'] / (1024 ** 2), 2)
                                print(user['used_traffic'], usage_traffic_in_megabyte)
                                last_usage_dict[str(purchase.purchase_id)] = usage_traffic_in_megabyte

                                if not last_traffic_usage: continue
                                traffic_use = max(int((usage_traffic_in_megabyte - last_traffic_usage)), 0)
                                statistics_usage_traffic[str(purchase.purchase_id)] = traffic_use
                                break

                vpn_crud.create_new_last_usage(session, json.dumps(last_usage_dict))
                vpn_crud.create_new_statistics(session, json.dumps(statistics_usage_traffic))
    except Exception as e:
        tb = traceback.format_exc()
        msg = ('error in statistics-timer!'
               f'\n\nerror type: {type(e)}'
               f'\nTraceBack:\n{tb}')
        await report_to_admin('error', 'statistics_timer', msg)

def datetime_range(start, end, delta):
    current = start
    while current <= end:
        yield current
        current += delta


async def reports_func(session, ft_instance, chat_id, get_purchased, period):
    with session.begin():
        date_now = datetime.now(pytz.timezone('Asia/Tehran'))
        purchased = [get_purchased]
        period = period
        print(purchased)
        if purchased[0] == 'all':
            all_user_purchases = vpn_crud.get_purchase_by_chat_id(session, chat_id)
            purchased = [purchase.purchase_id for purchase in all_user_purchases]

        period_mapping = {
            'day': (1, await ft_instance.find_text('day')),
            'week': (7, await ft_instance.find_text('week')),
            'month': (30, await ft_instance.find_text('month')),
            'year': (365, await ft_instance.find_text('year'))
        }

        delta_days, period_text = period_mapping.get(period, (365, await ft_instance.find_text('annually')))
        date = date_now - timedelta(days=delta_days)

        get_statistics = vpn_crud.get_specific_time_statistics(session, date)
        user_usage_dict = {}

        for get_date in get_statistics:
            get_user_usage = [{purchase_id: usage} for purchase_id, usage in json.loads(get_date.traffic_usage).items() if purchase_id in purchased]
            user_usage_dict[get_date.register_date] = get_user_usage

        detail_text, final_dict, final_traffic, avreage_traffic, index = '', {}, 0, 0, 1

        if period == 'day':
            for index, (timedate, usage_list) in enumerate(user_usage_dict.items()):
                time = timedate
                first_time = timedate - timedelta(hours=STATISTICS_TIMER_HORSE)

                usage_detail, get_traffic = [], 0

                for usage in usage_list:
                    usage_name = next(iter(usage.keys()))
                    usage_traffic = next(iter(usage.values()))

                    usage_detail.append(
                        f'\n- {await ft_instance.find_text("vpn_service_with_number")} {usage_name} = {await vpn_utilities.format_traffic_from_megabyte(ft_instance, usage_traffic)}' if usage_traffic else '')
                    get_traffic += usage_traffic

                detail_text += f'\n\n• {await ft_instance.find_text("vpn_from_clock")} {first_time.strftime("%H:%M")} {await ft_instance.find_text("to")} {time.strftime("%H:%M")} = {await vpn_utilities.format_traffic_from_megabyte(ft_instance,get_traffic)}'
                detail_text += ''.join(usage_detail[:5]) if purchased[0] == 'all' else ''

                final_traffic += get_traffic

                if not index:
                    final_dict[time.strftime("%a %H:00")] = get_traffic
                    continue

                final_dict[time.strftime("%H:00")] = get_traffic

            avreage_traffic = (final_traffic / 3) / index if final_traffic and index else 0

        elif period == 'week':
            for index, our_date in enumerate(datetime_range(date, date_now, timedelta(days=1))):
                date_ = our_date.strftime('%Y-%m-%d')
                get_usage, get_traff = {}, 0
                for _ in user_usage_dict.items():
                    time = _[0].strftime('%Y-%m-%d')
                    if time == date_:
                        for usage in _[1]:
                            usage_name, usage_traffic = next(iter(usage.items()))
                            get_traff += usage_traffic
                            get_usage[usage_name] = get_usage.get(usage_name, 0) + usage_traffic

                usage_detail = [f'\n- {await ft_instance.find_text("vpn_service_with_number")} {get_name} = {await vpn_utilities.format_traffic_from_megabyte(ft_instance,get_traffic)}' for get_name, get_traffic in get_usage.items() if get_traffic]
                detail_text += f"\n\n• {await ft_instance.find_text('in')} {await make_day_name_farsi(ft_instance, our_date.strftime('%A'))} {date_} = {await vpn_utilities.format_traffic_from_megabyte(ft_instance,get_traff)}"
                detail_text += ''.join(usage_detail[:5]) if purchased[0] == 'all' else ''

                final_traffic += get_traff
                final_dict[f"{our_date.strftime('%d')}"] = get_traff

            avreage_traffic = final_traffic / index if final_traffic and index else 0

        period_info = {
            'month': {'timedelta': timedelta(days=1), 'date_format': '%Y-%m-%d', 'plot_format': '%d', 'first_date': '%b', 'avg_data_devison': 4},
            'year': {'timedelta': timedelta(days=30), 'date_format': '%Y-%m', 'plot_format': '%m', 'first_date': '%Y', 'avg_data_devison': 12}
        }

        for period_key, period_value in period_info.items():
            if period == period_key:
                for index, our_date in enumerate(datetime_range(date, date_now, period_value['timedelta'])):
                    date_ = our_date.strftime(period_value['date_format'])
                    get_usage, get_traff = {}, 0
                    for _ in user_usage_dict.items():
                        time = datetime.strptime(_[0], '%Y-%m-%d %H:%M:%S').strftime(period_value['date_format'])
                        if time == date_:
                            for usage in _[1]:
                                usage_name, usage_traffic = next(iter(usage.items()))
                                get_traff += usage_traffic
                                get_usage[usage_name] = get_usage.get(usage_name, 0) + usage_traffic


                    detail_text += f'\n\n• {await ft_instance.find_text("in")} {our_date.strftime("%Y-%m-%d")} = {await vpn_utilities.format_traffic_from_megabyte(ft_instance,get_traff)}'

                    if period_key != 'month':
                        usage_detail = [f'\n- {await ft_instance.find_text("vpn_service_with_number")} {get_name} = {await vpn_utilities.format_traffic_from_megabyte(ft_instance,get_traffic)}' for get_name, get_traffic
                                        in get_usage.items() if get_traffic]
                        detail_text += ''.join(usage_detail[:5]) if purchased[0] == 'all' else ''

                    final_traffic += get_traff
                    if not index:
                        final_dict[f"{our_date.strftime(period_value['first_date'])} {our_date.strftime(period_value['plot_format'])}"] = get_traff
                    else:
                        final_dict[f"{our_date.strftime(period_value['plot_format'])}"] = get_traff

                avreage_traffic = final_traffic / period_value.get('avg_data_devison', index) if final_traffic and index else 0
                break

        return detail_text, final_dict, final_traffic, avreage_traffic

@handle_error.handle_functions_error
async def report_section(update, context):
    query = update.callback_query
    period, purchase_id, button_status = query.data.replace('statistics_', '').split('_')

    print(period, purchase_id, button_status)

    chat_id = query.message.chat_id
    ft_instance = FindText(update, context)

    with SessionLocal() as session:
        get_data = await reports_func(session, ft_instance, chat_id, get_purchased=purchase_id, period=period)

        if sum(get_data[1].values()) == 0 and not query.message.photo:
            keyboard = [[InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start_in_new_message_delete_previos')]]
            await query.edit_message_text(text=await ft_instance.find_text('vpn_no_usage_recored'), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
            return

        mapping = {
            'day': (None, await ft_instance.find_text('day'), f'statistics_week_{purchase_id}_{button_status}', await ft_instance.find_text('hour')),
            'week': (f'statistics_day_{purchase_id}_{button_status}', await ft_instance.find_text('week'), f'statistics_month_{purchase_id}_{button_status}', await ft_instance.find_text('day')),
            'month': (f'statistics_week_{purchase_id}_{button_status}', await ft_instance.find_text('month'), f'statistics_year_{purchase_id}_{button_status}', await ft_instance.find_text('week')),
            'year': (f'statistics_month_{purchase_id}_{button_status}', await ft_instance.find_text('year'), None, await ft_instance.find_text('month')),
        }

        back_button, button_name, next_button, constituent_name = (
            mapping.get(period, (f'statistics_day_{purchase_id}', await ft_instance.find_text('week'), f'statistics_month_{purchase_id}', await ft_instance.find_text('day'))))

        detail_emoji, detail_callback, detail_text = '+', 'open', ''

        if button_status == 'open':
            detail_emoji, detail_callback = '-', 'hide'
            detail_text = get_data[0]

        arrows = []
        if back_button: arrows.append(InlineKeyboardButton("⇤", callback_data=back_button))
        arrows.append(InlineKeyboardButton(f"{button_name}", callback_data='just_for_show'))
        if next_button: arrows.append(InlineKeyboardButton("⇥", callback_data=next_button))

        keyboard = [
            arrows,
            [InlineKeyboardButton(f"{detail_emoji} {await ft_instance.find_keyboard('report_detail')}", callback_data=f'statistics_{period}_{purchase_id}_{detail_callback}')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('all_services_report'), callback_data=f'statistics_{period}_all_{button_status}'),
             InlineKeyboardButton(await ft_instance.find_keyboard('refresh'), callback_data=f"statistics_{period}_{purchase_id}_{button_status}")],
            [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start_in_new_message_delete_previos' if purchase_id == 'all' else f'vpn_advanced_options__remove_this_message__{purchase_id}')]
        ]

        get_plot_image = plot.get_plot(get_data[1], period)

        text = (f'<b>{await ft_instance.find_text("usage_report")} {button_name}:</b>'
                f'\n\n<b>• {await ft_instance.find_text("vpn_traffic_use")} {button_name}: {await vpn_utilities.format_traffic_from_megabyte(ft_instance, get_data[2])}</b>'
                f'\n<b>• {await ft_instance.find_text("avreage_usage_in")} {constituent_name}: {await vpn_utilities.format_traffic_from_megabyte(ft_instance, get_data[3])}</b>')
        text += f'\n{detail_text}'

        if query.message.photo:
            media_photo = InputMediaPhoto(media=get_plot_image, parse_mode='html')
            await context.bot.edit_message_media(media=media_photo, chat_id=chat_id, message_id=query.message.message_id)
            await context.bot.edit_message_caption(caption=text[:1024], parse_mode='html', chat_id=chat_id, message_id=query.message.message_id, reply_markup=InlineKeyboardMarkup(keyboard))

        else:
            try:
                await query.delete_message()
            except telegram.error.BadRequest as e:
                if "Message can't be deleted for everyone" in str(e):
                    await query.answer()
                else:
                    raise e

            await context.bot.send_photo(photo=get_plot_image, chat_id=chat_id, caption=text[:1024], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')


