import logging, sys
from utilities_reFactore import FindText, message_token, handle_error
import start_reFactore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import setting, wallet_reFactore, my_service, setting_menu, guidnes_and_support
from vpn_service import buy_and_upgrade_service, my_service_detail, vpn_setting_menu, vpn_guid
from admin import admin_page, vpn_admin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)',
    handlers=[
        logging.FileHandler("freebyte.log"),
        logging.StreamHandler()
    ]
)

def log_uncaught_exceptions(exctype, value, tb):
    logging.error("Uncaught exception", exc_info=(exctype, value, tb))

sys.excepthook = log_uncaught_exceptions

@handle_error.handle_functions_error
@message_token.check_token
async def services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('select_section')
    main_keyboard = [
        [InlineKeyboardButton(await ft_instance.find_keyboard('buy_vpn_service_label'), callback_data='vpn_set_period_traffic__30_40')],
        [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
    ]
    return await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(main_keyboard), parse_mode='html')



if __name__ == '__main__':
    application = ApplicationBuilder().token(setting.telegram_bot_token).build()

    # Commands
    application.add_handler(CommandHandler('start', start_reFactore.start))
    application.add_handler(CommandHandler('vpn_start', start_reFactore.start))
    application.add_handler(CommandHandler('admin', admin_page.admin_page))

    # Bot Main Menu
    application.add_handler(CallbackQueryHandler(start_reFactore.start, pattern='start'))
    application.add_handler(CallbackQueryHandler(start_reFactore.start, pattern='start_in_new_message'))
    application.add_handler(CallbackQueryHandler(start_reFactore.register_user, pattern='register_user_(.*)'))
    application.add_handler(CallbackQueryHandler(services, pattern='menu_services'))
    application.add_handler(CallbackQueryHandler(start_reFactore.just_for_show, pattern='just_for_show'))
    application.add_handler(CallbackQueryHandler(my_service.my_services, pattern='my_services'))

    # Wallet
    application.add_handler(CallbackQueryHandler(wallet_reFactore.wallet_page, pattern='wallet_page'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.financial_transactions_wallet, pattern='financial_transactions_wallet'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.buy_credit_volume, pattern='buy_credit_volume'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.create_invoice, pattern='create_invoice__(.*)'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.pay_by_zarinpal, pattern='pay_by_zarinpal__(.*)'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.pay_by_cryptomus, pattern='pay_by_cryptomus__(.*)'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.pay_by_wallet, pattern='pay_by_wallet__(.*)'))

    # VPN Section
    application.add_handler(CallbackQueryHandler(buy_and_upgrade_service.buy_custom_service, pattern='vpn_set_period_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(buy_and_upgrade_service.upgrade_service, pattern='vpn_upgrade_service__(.*)'))
    application.add_handler(CallbackQueryHandler(my_service_detail.service_info, pattern='vpn_my_service_detail__(.*)'))
    application.add_handler(CallbackQueryHandler(my_service_detail.my_services, pattern='vpn_my_services(.*)'))
    application.add_handler(CallbackQueryHandler(my_service_detail.ask_remove_service_for_user, pattern='vpn_remove_service_ask__(.*)'))
    application.add_handler(CallbackQueryHandler(my_service_detail.remove_service_for_user, pattern='vpn_remove_service__(.*)'))

    # Admin
    application.add_handler(CallbackQueryHandler(admin_page.admin_page, pattern='admin_page'))
    application.add_handler(CallbackQueryHandler(vpn_admin.admin_page, pattern='admin_vpn'))
    application.add_handler(vpn_admin.admin_add_product_conversation)
    application.add_handler(vpn_admin.admin_add_mainserver_conversation)

    # Setting
    application.add_handler(CallbackQueryHandler(setting_menu.setting_menu, pattern='setting_menu'))
    application.add_handler(CallbackQueryHandler(vpn_setting_menu.setting_menu, pattern='vpn_setting_menu'))
    application.add_handler(CallbackQueryHandler(vpn_setting_menu.handle_vpn_notification, pattern='vpn_set_notification_period_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(vpn_setting_menu.apply_notification_setting, pattern='vpn_apply_notification_period_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(setting_menu.user_language_setting, pattern='user_language_setting'))
    application.add_handler(CallbackQueryHandler(setting_menu.change_user_language, pattern='set_user_language_on__(.*)'))

    # Quide And Support
    application.add_handler(CallbackQueryHandler(guidnes_and_support.guide_menu, pattern='guide_menu'))
    application.add_handler(CallbackQueryHandler(vpn_guid.guide_menu, pattern='vpn_guide_menu'))
    application.add_handler(CallbackQueryHandler(vpn_guid.vpn_guide, pattern='vpn_guid__(.*)'))

    application.run_polling()

