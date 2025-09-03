from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from admin import admin_page, admin_system, admin_users, admin_ticket, vpn_admin


def admin_handler(application):
    application.add_handler(CommandHandler('admin', admin_page.admin_page))
    application.add_handler(CommandHandler('add_credit_to_user', admin_page.add_credit_for_user))
    application.add_handler(CommandHandler('add_partner', admin_page.add_partner))
    application.add_handler(CommandHandler('find_user', admin_users.find_user))
    application.add_handler(CommandHandler('find_service', admin_users.find_service))
    application.add_handler(CommandHandler('send_to_users', admin_page.say_to_users))
    application.add_handler(CommandHandler('send_to_everyone', admin_page.say_to_everyone))

    application.add_handler(CallbackQueryHandler(admin_page.admin_page, pattern='admin_page'))
    application.add_handler(CallbackQueryHandler(vpn_admin.admin_page, pattern='admin_vpn'))
    application.add_handler(vpn_admin.admin_add_product_conversation)
    application.add_handler(vpn_admin.admin_add_mainserver_conversation)
    application.add_handler(admin_ticket.admin_ticket_reply_conversation)

    application.add_handler(CallbackQueryHandler(admin_users.all_users_list, pattern='admin_manage_users__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.view_user_info, pattern='admin_view_user__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.all_products, pattern='admin_system__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_view_product, pattern='admin_view_product__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_system.admin_change_product_status, pattern='admin_set_product_status__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.view_product_main_server_info,
                                                 pattern='admin_product_main_server_info__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_xray_core, pattern='admin_view_core__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_system.admin_restart_xray_core, pattern='admin_restart_core__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_system.admin_view_host, pattern='admin_view_host__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_system.admin_view_inbounds, pattern='admin_view_inbounds__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_system.admin_view_online_users, pattern='admin_view_online_users__(.*)'))

    application.add_handler(
        CallbackQueryHandler(admin_users.admin_set_user_level, pattern='admin_set_user_level__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_set_free_vpn_test, pattern='admin_set_vpn_free_test__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_user_services, pattern='admin_user_services__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_ticket.delete_message_assuarance, pattern='dell_mess_asu__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_ticket.delete_message, pattern='dell_message__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_ticket.cancel_deleteing_message, pattern='cancel_dell__(.*)'))

    application.add_handler(
        CallbackQueryHandler(admin_users.admin_user_service_detail, pattern='admin_user_service_detail__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_buy_service_for_user, pattern='admin_bv_for_user__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_assurance_buy_vpn_service, pattern='admin_assurance_bv__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_confirm_buy_vpn_service, pattern='admin_confirm_bv__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_users.admin_upgrade_service_for_user,
                                                 pattern='admin_upgrade_user_vpn_service__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_upgrade_vpn_service,
                                                 pattern='admin_assurance_upgrade_vpn__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_confirm_upgrade_vpn_service, pattern='admin_confirm_upvpn__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_users.admin_set_purchase_period_and_traffic,
                                                 pattern='admin_set_time_and_traffic__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_set_purchase_traffic_and_period,
                                                 pattern='admin_assurance_set_ptp__(.*)'))
    application.add_handler(CallbackQueryHandler(admin_users.admin_confirm_set_purchase_traffic_and_period,
                                                 pattern='admin_confirm_set_ptp__(.*)'))

    application.add_handler(CallbackQueryHandler(admin_users.admin_assurance_remove_vpn_service,
                                                 pattern='admin_assurance_remove_vpn__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_confirm_remove_vpn_service, pattern='admin_confirm_remove_vpn__(.*)'))

    application.add_handler(
        CallbackQueryHandler(admin_page.virtual_number_admin, pattern='admin_virtual_number'))

    application.add_handler(
        CallbackQueryHandler(admin_system.view_product_node_usage, pattern='admin_node_usage__(.*)'))
    application.add_handler(
        CallbackQueryHandler(admin_users.admin_user_node_usage, pattern='admin_user_nu__(.*)'))
    application.add_handler(admin_users.admin_change_wallet_balance_conversation)