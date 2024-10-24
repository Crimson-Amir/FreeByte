import logging, sys, pytz
from datetime import time
from utilities_reFactore import FindText, message_token, handle_error
import start_reFactore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import setting, wallet_reFactore, my_service, setting_menu, guidnes_and_support
from vpn_service import buy_and_upgrade_service, my_service_detail, vpn_setting_menu, vpn_guid, statistics, vpn_notification
from admin import admin_page, vpn_admin, admin_ticket, admin_users, admin_system
from database_sqlalchemy import SessionLocal
from crud import crud

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
    user = update.effective_chat

    with SessionLocal() as session:
        config = crud.get_user_config(session, user.id)

        keyboard = [
            [InlineKeyboardButton(await ft_instance.find_keyboard('get_vpn_test_label'), callback_data='vpn_recive_test_service') if not config.get_vpn_free_service else None,
             InlineKeyboardButton(await ft_instance.find_keyboard('buy_vpn_service_label'), callback_data='vpn_set_period_traffic__30_40_1')],
            [InlineKeyboardButton(await ft_instance.find_keyboard('back_button'), callback_data='start')]
        ]

        keyboard = [list(filter(None, row)) for row in keyboard]
        return await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='html')

async def unknown_message(update, context):
    ft_instance = FindText(update, context)
    text = await ft_instance.find_text('unknown_input')
    await update.message.reply_text(text)


if __name__ == '__main__':
    application = ApplicationBuilder().token(setting.telegram_bot_token).build()

    # Commands
    application.add_handler(CommandHandler('start', start_reFactore.start))
    application.add_handler(CommandHandler('vpn_start', start_reFactore.start))
    application.add_handler(CommandHandler('admin', admin_page.admin_page))
    application.add_handler(CommandHandler('add_credit_to_user', admin_page.add_credit_for_user))
    application.add_handler(CommandHandler('add_partner', admin_page.add_partner))
    application.add_handler(CommandHandler('find_user', admin_users.find_user))
    application.add_handler(CommandHandler('find_service', admin_users.find_service))
    application.add_handler(CommandHandler('find_my_service', my_service_detail.find_my_service))
    application.add_handler(CommandHandler('send_to_everyone', admin_page.say_to_every_one))


    # Bot Main Menu
    application.add_handler(CallbackQueryHandler(start_reFactore.start, pattern='start(.*)'))
    application.add_handler(CallbackQueryHandler(start_reFactore.web_application, pattern='web_application'))
    application.add_handler(CallbackQueryHandler(start_reFactore.register_user, pattern='register_user_(.*)'))
    application.add_handler(CallbackQueryHandler(services, pattern='menu_services'))
    application.add_handler(CallbackQueryHandler(start_reFactore.just_for_show, pattern='just_for_show'))
    application.add_handler(CallbackQueryHandler(start_reFactore.already_on_this, pattern='already_on_this'))
    application.add_handler(CallbackQueryHandler(my_service.my_services, pattern='my_services'))
    application.add_handler(CallbackQueryHandler(start_reFactore.manage_request_to_join_by_admin, pattern='user_requested_to_join'))
    application.add_handler(CallbackQueryHandler(start_reFactore.check_new_user_request_by_admin, pattern='user_join_request_(.*)'))
    application.add_handler(CallbackQueryHandler(start_reFactore.invite_firends, pattern='invite_firends'))



    # Wallet
    application.add_handler(CallbackQueryHandler(wallet_reFactore.wallet_page, pattern='wallet_page'))
    application.add_handler(CallbackQueryHandler(wallet_reFactore.financial_transactions_wallet, pattern='financial_transactions_wallet_(.*)'))
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
    application.add_handler(CallbackQueryHandler(my_service_detail.service_advanced_options, pattern='vpn_advanced_options__(.*)'))
    application.add_handler(CallbackQueryHandler(my_service_detail.get_configs_separately, pattern='vpn_get_configs_separately__(.*)'))
    application.add_handler(CallbackQueryHandler(buy_and_upgrade_service.recive_test_service_info, pattern='vpn_recive_test_service'))
    application.add_handler(CallbackQueryHandler(buy_and_upgrade_service.recive_test_service, pattern='vpn_recive_test__(.*)'))
    application.add_handler(CallbackQueryHandler(statistics.report_section, pattern='statistics_(.*)'))
    application.add_handler(my_service_detail.change_ownership_conversation)

    application.job_queue.run_repeating(vpn_notification.notification_timer, interval=10 * 60, first=0)
    application.job_queue.run_repeating(statistics.statistics_timer, interval=180 * 60, first=0)
    application.job_queue.run_daily(
        vpn_notification.tasks_schedule,
        time(hour=0, minute=0, second=0, tzinfo=pytz.timezone('Asia/Tehran'))
    )

    # Admin
    application.add_handler(CallbackQueryHandler(admin_page.admin_page, pattern='admin_page'))
    application.add_handler(CallbackQueryHandler(vpn_admin.admin_page, pattern='admin_vpn'))
    application.add_handler(vpn_admin.admin_add_product_conversation)
    application.add_handler(vpn_admin.admin_add_mainserver_conversation)
    application.add_handler(admin_ticket.admin_ticket_reply_conversation)

    application.add_handler(CallbackQueryHandler(admin_users.all_users_list, pattern='admin_manage_users__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.view_user_info, pattern='admin_view_user__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.all_products, pattern='admin_system__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_view_product, pattern='admin_view_product__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_change_product_status, pattern='admin_set_product_status__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.view_product_main_server_info, pattern='admin_product_main_server_info__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_xray_core, pattern='admin_view_core__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_restart_xray_core, pattern='admin_restart_core__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_system.admin_view_host, pattern='admin_view_host__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_view_inbounds, pattern='admin_view_inbounds__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_view_online_users, pattern='admin_view_online_users__(.*)'))


    application.add_handler(CallbackQueryHandler(admin_users.admin_set_user_level, pattern='admin_set_user_level__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_set_free_vpn_test, pattern='admin_set_vpn_free_test__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_user_services, pattern='admin_user_services__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_ticket.delete_message_assuarance, pattern='dell_mess_asu__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_ticket.delete_message, pattern='dell_message__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_ticket.cancel_deleteing_message, pattern='cancel_dell__(.*)'))


    application.add_handler(CallbackQueryHandler(admin_users.admin_user_service_detail, pattern='admin_user_service_detail__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_buy_service_for_user, pattern='admin_bv_for_user__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_buy_vpn_service, pattern='admin_assurance_bv__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_confirm_buy_vpn_service, pattern='admin_confirm_bv__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_users.admin_upgrade_service_for_user, pattern='admin_upgrade_user_vpn_service__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_upgrade_vpn_service, pattern='admin_assurance_upgrade_vpn__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_confirm_upgrade_vpn_service, pattern='admin_confirm_upvpn__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_users.admin_set_purchase_period_and_traffic, pattern='admin_set_time_and_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_set_purchase_traffic_and_period, pattern='admin_assurance_set_ptp__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_confirm_set_purchase_traffic_and_period, pattern='admin_confirm_set_ptp__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_remove_vpn_service, pattern='admin_assurance_remove_vpn__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_confirm_remove_vpn_service, pattern='admin_confirm_remove_vpn__(.*)'))

    application.add_handler(admin_users.admin_change_wallet_balance_conversation)

    # Setting
    application.add_handler(CallbackQueryHandler(setting_menu.setting_menu, pattern='setting_menu'))
    application.add_handler(CallbackQueryHandler(vpn_setting_menu.setting_menu, pattern='vpn_setting_menu'))
    application.add_handler(CallbackQueryHandler(vpn_setting_menu.handle_vpn_notification, pattern='vpn_set_notification_period_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(vpn_setting_menu.apply_notification_setting, pattern='vpn_apply_notification_period_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(setting_menu.user_language_setting, pattern='user_language_setting'))
    application.add_handler(CallbackQueryHandler(setting_menu.change_user_language, pattern='set_user_language_on__(.*)'))

    # Guide And Support
    application.add_handler(CallbackQueryHandler(guidnes_and_support.guide_menu, pattern='guide_menu'))
    application.add_handler(CallbackQueryHandler(vpn_guid.guide_menu, pattern='vpn_guide_menu(.*)'))
    application.add_handler(CallbackQueryHandler(vpn_guid.vpn_guide, pattern='vpn_guide__(.*)'))
    application.add_handler(guidnes_and_support.ticket_conversation)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))

    application.run_polling()

