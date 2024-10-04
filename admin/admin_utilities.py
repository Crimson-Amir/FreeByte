import sys, os, functools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crud import admin_crud
from database_sqlalchemy import SessionLocal
from telegram.ext import ConversationHandler

class Admin:
    def __init__(self):
        self.allow_admin = {}
        self.refresh_admins()
    def refresh_admins(self):
        with SessionLocal() as session:
            admins = admin_crud.get_admins(session)
            for admin in admins:
                self.allow_admin[admin.chat_id] = admin.user_level

    async def refresh_admins_schedule(self):
        self.refresh_admins()


admin_check = Admin()

def admin_access(func):
    @functools.wraps(func)
    async def wrapper(update, context, **kwargs):
        user_detail = update.effective_chat
        if user_detail.id in admin_check.allow_admin:
            return await func(update, context, **kwargs)

    return wrapper

async def cancel(update, context):
    user_detail = update.effective_chat
    await context.bot.send_message(chat_id=user_detail.id, text="Action cancelled.")
    return ConversationHandler.END
