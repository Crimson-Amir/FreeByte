import datetime, json, arrow
from database_sqlalchemy import SessionLocal
import setting, logging, traceback
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from dialogue_texts import text_transaction, keyboard_transaction
from setting import default_language, ADMIN_CHAT_IDs, telegram_bot_token
from telegram.ext import ConversationHandler
import functools, requests
from crud import crud
class UserNotFound(Exception):
    def __init__(self): super().__init__("user was't register in bot!")


def human_readable(date, user_language):
    if not date: return
    get_date = arrow.get(date)

    try:
        return get_date.humanize(locale=user_language)

    except ValueError as e:
        if 'week' in str(e) and user_language == 'fa':
            return str(get_date.humanize()).replace('weeks ago', 'هفته پیش').replace('a week ago', 'هفته پیش').replace('in', 'در').replace('weeks', 'هفته').replace('a week', 'یک هفته')
        else:
            return get_date.humanize()

    except Exception as e:
        logging.error(f'an error in humanize data: {e}')
        return f'Error In Parse Data'

def format_traffic_from_byte(traffic_in_byte, convert_to='GB'):
    convert_to_dict = {
        'GB': 3,
        'MB': 2
    }
    return round(traffic_in_byte / (1024 ** convert_to_dict.get(convert_to, 3)), 2)


async def start(update, context, in_new_message=False, raise_error=False):
    query = update.callback_query
    user_detail = update.effective_chat
    ft_instance = FindText(update, context, notify_user=False)
    text = await ft_instance.find_text('start_menu')
    try:
        main_keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('menu_services'), callback_data='menu_services')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('wallet'), callback_data='wallet_page'),
             InlineKeyboardButton(await ft_instance.find_keyboard('my_services'), callback_data='my_services')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('setting'), callback_data='setting_menu'),
             InlineKeyboardButton(await ft_instance.find_keyboard('invite_firend'), callback_data='invite_firends')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('help_button'), callback_data='guide_menu')],
        ]

        if update.callback_query and "start_in_new_message" not in update.callback_query.data and not in_new_message:
            return await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')
        if query:
            if 'start_in_new_message_delete_previos' in query.data:
                await query.delete_message()
            await query.answer()
        return await context.bot.send_message(chat_id=user_detail.id, text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')

    except Exception as e:
        if raise_error: raise e
        logging.error(f'error in send start message! \n{e}')
        await context.bot.send_message(chat_id=user_detail.id, text='<b>Sorry, somthing went wrong!</b>', parse_mode='html')


class UserDataManager:
    def __init__(self):
        self.user_data_store = {}

    def get_user_database_id(self, session, user_id):
        user_database_id = self.user_data_store.get(user_id)
        if not user_database_id:
            user_database_id = crud.get_user(session, user_id)
            self.user_data_store[user_id] = type(
                'user_detail',
                (object, ),
                {
                    'user_id': user_database_id.user_id,
                    'user_level': user_database_id.config.user_level
                }
            )
        return self.user_data_store[user_id]

    def update_user_database_id(self, user_id, new_database_id):
        self.user_data_store[user_id] = new_database_id

    def delete_user_data(self, user_id):
        if user_id in self.user_data_store:
            del self.user_data_store[user_id]


user_data_manager = UserDataManager()

async def find_user(session, user_id):
    user_database_id = user_data_manager.get_user_database_id(session, user_id)
    return user_database_id


class FindText:
    def __init__(self, update, context, user_id=None, notify_user=True):
        self._update = update
        self._context = context
        self._notify_user = notify_user
        self._user_id = user_id

    @staticmethod
    async def handle_error_message(update, context, message_text=None):
        user_id = update.effective_chat.id
        if update.callback_query:
            await update.callback_query.answer(message_text)
            return
        await context.bot.send_message(text=message_text, chat_id=user_id)

    @staticmethod
    async def language_transaction(text_key, language_code=default_language, section="text") -> str:
        transaction = text_transaction
        if section == "keyboard": transaction = keyboard_transaction
        return transaction.get(text_key, transaction.get('error_message')).get(language_code, 'language not found!')

    @staticmethod
    async def get_language_from_database(user_id):
        with SessionLocal() as session:
            user = crud.get_user(session, user_id)
        if user:
            return user.language

    async def find_user_language(self):
        user_id = self._update.effective_chat.id
        user_language = self._context.user_data.get('user_language')
        if not user_language:
            get_user_language_from_db = await self.get_language_from_database(user_id)
            if not get_user_language_from_db:
                if self._notify_user:
                    await self.handle_error_message(self._update, self._context, message_text="Your info was't found, please register with /start command!")
                raise UserNotFound()
            user_language = get_user_language_from_db
            self._context.user_data['user_language'] = user_language
        return user_language

    async def find_text(self, text_key):
        return await self.language_transaction(text_key, await self.find_user_language())

    async def find_keyboard(self, text_key):
        return await self.language_transaction(text_key, await self.find_user_language(), section='keyboard')

    async def find_from_database(self, user_id, text_key, section='text'):
        user_language = await self.get_language_from_database(user_id)
        return await self.language_transaction(text_key, user_language, section=section)

class HandleErrors:
    def handle_functions_error(self, func):
        @functools.wraps(func)
        async def wrapper(update, context, **kwargs):
            user_detail = update.effective_chat
            try:
                return await func(update, context, **kwargs)
            except Exception as e:
                if 'Message is not modified' in str(e): return await update.callback_query.answer()
                logging.error(f'error in {func.__name__}: {str(e)}')
                tb = traceback.format_exc()
                err = (
                    f"🔴 An error occurred in {func.__name__}:"
                    f"\n\nerror type:{type(e)}"
                    f"\nerror reason: {str(e)}"
                    f"\n\nUser fullname: {user_detail.first_name} {user_detail.last_name}"
                    f"\nUsername: @{user_detail.username}"
                    f"\nUser ID: {user_detail.id}"
                    f"\n\nTraceback: \n{tb}"
                )

                await self.report_to_admin(err)
                await self.handle_error_message_for_user(update, context)
        return wrapper
    def handle_conversetion_error(self, func):
        @functools.wraps(func)
        async def wrapper(update, context, **kwargs):
            user_detail = update.effective_chat
            try:
                return await func(update, context, **kwargs)
            except Exception as e:
                logging.error(f'error in {func.__name__}: {str(e)}')
                tb = traceback.format_exc()
                err = (
                    f"🔴 An error occurred in {func.__name__}:"
                    f"\n\nerror type:{type(e)}"
                    f"\nerror reason: {str(e)}"
                    f"\n\nUser fullname: {user_detail.first_name} {user_detail.last_name}"
                    f"\nUsername: @{user_detail.username}"
                    f"\nUser ID: {user_detail.id}"
                    f"\n\nTraceback: \n{tb}"
                )
                await self.report_to_admin(err)
                await self.handle_error_message_for_user(update, context)
                return ConversationHandler.END
        return wrapper

    @staticmethod
    async def report_to_admin(msg, message_thread_id=setting.error_thread_id):
        response = requests.post(
            url=f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
            json={'chat_id': ADMIN_CHAT_IDs[0], 'text': msg[:4096], 'message_thread_id': message_thread_id}
        )
        logging.info(f'send report to admin status code: {response.status_code}')

    @staticmethod
    async def handle_error_message_for_user(update, context, message_text=None):
        user_id = update.effective_chat.id
        ft_instance = FindText(update, context)
        message_text = message_text if message_text else await ft_instance.find_text('error_message')
        if update.callback_query:
            return await update.callback_query.answer(message_text)
        await context.bot.send_message(text=message_text, chat_id=user_id)

async def report_to_admin(level, fun_name, msg, user_table=None):
    try:
        report_level = {
            'purchase': {'thread_id': setting.purchased_thread_id, 'emoji': '🟢'},
            'info': {'thread_id': setting.info_thread_id, 'emoji': '🔵'},
            'warning': {'thread_id': setting.info_thread_id, 'emoji': '🟡'},
            'error': {'thread_id': setting.error_thread_id, 'emoji': '🔴'},
            'emergency_error': {'thread_id': setting.error_thread_id, 'emoji': '🔴🔴'},
        }

        emoji = report_level.get(level, {}).get('emoji', '🔵')
        thread_id = report_level.get(level, {}).get('thread_id', setting.info_thread_id)
        message = f"{emoji} Report {level.replace('_', ' ')} {fun_name}\n\n{msg}"

        if user_table:
            message += (
                "\n\n👤 User Info:"
                f"\nUser name: {user_table.first_name} {user_table.last_name}"
                f"\nUser ID: {user_table.chat_id}"
                f"\nUsername: @{user_table.username}"
            )

        await HandleErrors.report_to_admin(message, thread_id)
    except Exception as e:
        logging.error(f'error in report to admin.\n{e}')


async def report_to_user(level, user_id, msg):
    try:
        report_level = {
            'success': '🟢',
            'info': '🔵',
            'warning': '🟡',
            'error': '🔴',
        }
        emoji = report_level.get(level, '🔵')
        message = emoji + msg

        requests.post(
            url=f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
            json={'chat_id': user_id, 'text': message}
        )

    except Exception as e:
        logging.error(f'error in send message for user!\n{e}')


class MessageToken:
    message_timer = {}

    @classmethod
    def set_message_time(cls, message_id):
        cls.message_timer[message_id] = datetime.datetime.now()

    @classmethod
    def message_expierd(cls, message_id):
        if (cls.message_timer[message_id] + datetime.timedelta(hours=1)) < datetime.datetime.now():
            return True
        return False

    @classmethod
    def check_token(cls, func):
        @functools.wraps(func)
        async def wrapper(update, context, **kwargs):

            if update.message:
                message_id = update.message.message_id
            elif update.callback_query and update.callback_query.message:
                message_id = update.callback_query.message.message_id
            else:
                return await func(update, context, **kwargs)

            timer_exist_in_message_timer = cls.message_timer.get(message_id)

            if timer_exist_in_message_timer:
                if cls.message_expierd(message_id):
                    await context.bot.delete_message(update.effective_chat.id, message_id)
                    new_message = await start(update, context, in_new_message=True)
                    del cls.message_timer[message_id]
                    cls.set_message_time(new_message.message_id)
                else:
                    cls.set_message_time(message_id)
                    return await func(update, context, **kwargs)
            else:
                cls.set_message_time(message_id)
                return await func(update, context, **kwargs)

        return wrapper

class FakeContext:
    user_data = {}

    class bot:
        @staticmethod
        async def send_message(chat_id, text, parse_mode=None):
            url = f"https://api.telegram.org/bot{setting.telegram_bot_token}/sendMessage"
            json_data = {'chat_id': chat_id, 'text': text, 'parse_mode':parse_mode or 'html'}
            a = requests.post(url=url, json=json_data)
            print(a, chat_id, text)
        @staticmethod
        async def send_photo(photo, chat_id, caption, reply_markup, parse_mode):
            url = f"https://api.telegram.org/bot{setting.telegram_bot_token}/sendPhoto"
            files = {'photo': ('qr_code.png', photo, 'image/png')}
            keyboard = [[{'text': button.text, 'callback_data': button.callback_data} for button in row] for row in reply_markup.inline_keyboard]
            reply_markup_json = json.dumps({'inline_keyboard': keyboard})

            data = {
                'chat_id': chat_id,
                'caption': caption,
                'reply_markup': reply_markup_json,
                'parse_mode': parse_mode
            }

            response = requests.post(url=url, data=data, files=files)
            print(response)

async def cancel(update, context):
    user_detail = update.effective_chat
    await context.bot.send_message(chat_id=user_detail.id, text="Action cancelled.")
    return ConversationHandler.END

async def cancel_user(update, context):
    query = update.callback_query
    ft_instance = FindText(update, context)
    await query.delete_message()
    user_detail = update.effective_chat
    await context.bot.send_message(chat_id=user_detail.id, text=await ft_instance.find_text('action_canceled'))
    return ConversationHandler.END

handle_error = HandleErrors()
message_token = MessageToken()