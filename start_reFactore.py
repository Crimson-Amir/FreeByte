import logging
from crud import crud
from utilities_reFactore import FindText, UserNotFound, handle_error, message_token, start as ustart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import setting
from database_sqlalchemy import SessionLocal

user_request_to_join = {}

@handle_error.handle_functions_error
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, in_new_message=False):
    user_detail = update.effective_chat

    try:
        await ustart(update, context, in_new_message, True)
    except UserNotFound:
        if context.args:
            text = ('<b>• زبان خود را انتخاب کنید:'
                    '\n• Please choose your language:</b>')

            context.user_data[f'inviter_{user_detail.id}'] = context.args[0].replace('ref_', '').split('_')

            keyboard = [[InlineKeyboardButton('English 🇬🇧', callback_data='register_user_en'),
                         InlineKeyboardButton('فارسی 🇮🇷', callback_data='register_user_fa')]]
            new_select = await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
            message_token.set_message_time(new_select.message_id)
        else:
            if user_detail.id in user_request_to_join:
                return await context.bot.send_message(chat_id=user_detail.id, text='You already send a join request!\nشما قبلا درخواست عضویت ارسال کردید!')
            text = ('This bot is private, please return with the invite link. Or send a request to join the admin.'
                    '\nاین ربات خصوصی است، لطفا با لینک دعوت برگردید یا درخواست عضویت ارسال کنید.')
            keyboard = [[InlineKeyboardButton('درخواست عضویت | Reques to Join', callback_data=f'user_requested_to_join')]]
            await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

    except Exception as e:
        logging.error(f'error in send start message! \n{e}')
        await context.bot.send_message(chat_id=user_detail.id, text='<b>Sorry, somthing went wrong!\nبخشید مشکلی وجود داشت!</b>', parse_mode='html')


@handle_error.handle_functions_error
async def manage_request_to_join_by_admin(update, context):
    query = update.callback_query
    user_detail = update.effective_chat

    if user_request_to_join.get(user_detail.id):
        return await query.answer('you already send a request!')

    user_request_to_join[user_detail.id] = {'user_detail': user_detail}

    photos = await context.bot.get_user_profile_photos(user_id=user_detail.id)
    text = (f'👤 User Request to join the BOT\n\n'
            f'User Name: {user_detail.first_name} {user_detail.last_name}\n'
            f'User ID: {user_detail.id}\n'
            f'UserName: @{user_detail.username}\n'
            )
    admin_keyboard = [
        [InlineKeyboardButton("Accept User✅", callback_data=f'user_join_request_accept__{user_detail.id}'),
         InlineKeyboardButton("Deny User❌", callback_data=f'user_join_request_deny__{user_detail.id}')],
    ]

    if photos.total_count > 0:
        photo_file_id = photos.photos[0][-1].file_id
        await context.bot.send_photo(chat_id=setting.ADMIN_CHAT_IDs[0], photo=photo_file_id, caption=text,
                                     reply_markup=InlineKeyboardMarkup(admin_keyboard), message_thread_id=setting.new_user_thread_id)
    else:
        await context.bot.send_message(chat_id=setting.ADMIN_CHAT_IDs[0], text=text + '\n\n• No Profile Picture (or not public)',
                                       reply_markup=InlineKeyboardMarkup(admin_keyboard), message_thread_id=setting.new_user_thread_id)

    await query.answer('✅')
    await query.edit_message_text(
        text='• We will check your request and announce the result through this robot.'
             '\n• ما درخواست شمارو بررسی مکینیم و نتیجه رو از طریق همین ربات اعلام میکنیم.',
        reply_markup=InlineKeyboardMarkup([])
    )


async def check_new_user_request_by_admin(update, context):
    query = update.callback_query
    chat_id = int(query.data.replace('user_join_request_accept__', '').replace('user_join_request_deny__', ''))
    user_detail = user_request_to_join[chat_id]['user_detail']

    if 'accept' in query.data:
        user_request_to_join[chat_id]['without_invite_link'] = True
        text = ('<b>• زبان خود را انتخاب کنید:'
                '\n• Please choose your language:</b>')
        keyboard = [[InlineKeyboardButton('English 🇬🇧', callback_data='register_user_en'),
                     InlineKeyboardButton('فارسی 🇮🇷', callback_data='register_user_fa')]]
        await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')
    else:
        await context.bot.send_message(chat_id=user_detail.id, text='your join request not accespted, but still you can return with invite link!\nدرخواست عضویت شما قبول نشد، اما همچنان میتواند با لینک دعوت برگردید!', parse_mode='html')

    await query.answer('Done ✅')
    await query.edit_message_reply_markup(InlineKeyboardMarkup([]))


@handle_error.handle_functions_error
@message_token.check_token
async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_detail = update.effective_chat
    query = update.callback_query
    selected_language = query.data.replace('register_user_', '')


    with SessionLocal() as session:
        with session.begin():

            join_without_invite_link = user_request_to_join.get(user_detail.id, {}).get('without_invite_link')
            inviter_chat_id = None

            if not join_without_invite_link:
                inviter_chat_id, inviter_user_id = context.user_data[f'inviter_{user_detail.id}']
                inviter_user = crud.get_user_by_chat_id_and_user_id(session, inviter_chat_id, inviter_user_id)
                if not inviter_user:
                    return context.bot.send_message(chat_id=user_detail.id, text='The inviting user does not exist in our database!\nکاربر دعوت کننده در دیتابیس ما وجود ندارد!')

            crud.create_user(session, user_detail, inviter_chat_id, selected_language)
            photos = await context.bot.get_user_profile_photos(user_id=user_detail.id)

            start_text_notif = (f'👤 New Start IN Bot\n\n'
                                f'User Name: {user_detail.first_name} {user_detail.last_name}\n'
                                f'User ID: <a href=\"tg://user?id={user_detail.id}\">{user_detail.id}</a>\n'
                                f'UserName: @{user_detail.username}\n'
                                f'Selected Language: {selected_language}\n'
                                f"\nInvited By: <a href=\"tg://user?id={inviter_chat_id}\">{inviter_chat_id}</a>")

            if photos.total_count > 0:
                photo_file_id = photos.photos[0][-1].file_id
                await context.bot.send_photo(chat_id=setting.ADMIN_CHAT_IDs[0], photo=photo_file_id, caption=start_text_notif, parse_mode='HTML', message_thread_id=setting.new_user_thread_id)
            else:
                await context.bot.send_message(chat_id=setting.ADMIN_CHAT_IDs[0], text=start_text_notif + '\n\n• Without profile picture (or not public)', parse_mode='HTML', message_thread_id=setting.new_user_thread_id)
            context.user_data.pop(f'inviter_{user_detail.id}', None)
            user_request_to_join.pop(user_detail.id, None)

    return await start(update, context)


async def just_for_show(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context, notify_user=False)
    await query.answer(text=await ft_instance.find_text('just_for_show'))


async def already_on_this(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context, notify_user=False)
    await query.answer(text=await ft_instance.find_text('already_on_this'))