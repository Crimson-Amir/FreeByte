import dialogues.vpn_dialogues as vpn_service_dialogues
import dialogues.virtual_number_dialogues as virtual_number_service_dialogues


text_transaction = {
    "error_message": {
        "en": "Oops, something went wrong!",
        "fa": "خطا در انجام عملیات!",
    },
    "start_menu": {
        "en": "👋 Welcome to FreeByte Bot!",
        "fa": "درود، به ربات فری‌بایت خوش آمدید! 👋",
    },
    "select_section": {
        "en": "Please choose the section you’d like to continue:",
        "fa": "برای ادامه بخش مورد نظر خودتان را انتخاب کنید:",
    },
    "message_expired_send_new_message": {
        "en": "⏳ This message has expired! We’ve sent you a new menu.",
        "fa": "⏳ پیام منقضی شده است! منوی جدید برای شما ارسال شد.",
    },
    "recent_transactions": {
        "en": "• Recent Transactions:",
        "fa": "• تراکنش‌های اخیر:",
    },
    "receive_money": {
        "en": "💰 Received",
        "fa": "💰 دریافت",
    },
    "spend_money": {
        "en": "💸 Spend",
        "fa": "💸 برداشت",
    },
    "irt": {
        "en": "IRT",
        "fa": "تومان",
    },
    "available": {
        "en": "are available",
        "fa": "عدد مانده",
    },
    "search_result": {
        "en": "🔍 Search Result:",
        "fa": "🔍 نتیجه جستجو:",
    },
    "usd": {
        "en": "USD",
        "fa": "دلار",
    },
    "no_transaction_yet": {
        "en": "You haven’t made any transactions yet!",
        "fa": "شما تا به حال تراکنشی نداشتید!",
    },
    "no_service_found": {
        "en": "There is no Service find!",
        "fa": "هیچ سرویسی پیدا نشد!",
    },
    "no_country_found": {
        "en": "There is no Country find!",
        "fa": "هیچ کشوری پیدا نشد!",
    },
    "wallet_page_title": {
        "en": "Your Wallet Overview:",
        "fa": "اطلاعات کیف پول شما:",
    },
    "wallet_balance_key": {
        "en": "• Balance:",
        "fa": "• موجودی حساب:",
    },
    "last_transaction": {
        "en": "• Last Transaction:",
        "fa": "• آخرین تراکنش:",
    },
    "add_credit_to_wallet_title": {
        "en": "• Choose an amount to add to your wallet:",
        "fa": "• مشخص کنید چه مقدار اعتبار به کیف پولتون اضافه بشه:",
    },
    "invoice_title": {
        "en": "• Please review the details below and finalize your payment if everything looks good:",
        "fa": "• اطلاعات زیر را بررسی کنید و درصورت تایید، پرداخت را نهایی کنید:",
    },
    "price": {
        "en": "Amount:",
        "fa": "مبلغ:",
    },
    "payment_option_title": {
        "en": "⤷ Select one of the following payment methods:",
        "fa": "⤶ برای پرداخت می‌توانید یکی از روش‌های زیر را انتخاب کنید:",
    },
    "invoice_extra_data": {
        "en": "• Invoice Details:",
        "fa": "• اطلاعات فاکتور:",
    },
    "charge_wallet": {
        "en": "Add Credit to Wallet",
        "fa": "افزایش اعتبار کیف پول",
    },
    "buy_vpn_service": {
        "en": "Purchase VPN Service",
        "fa": "خرید سرویس VPN",
    },
    "upgrade_vpn_service": {
        "en": "Upgrade VPN Service #{0}",
        "fa": "ارتقاء سرویس VPN شماره {0}",
    },
    "traffic": {
        "en": "• Data Traffic:",
        "fa": "• ترافیک (حجم):",
    },
    "wallet_credit_label": {
        "en": "Wallet Balance:",
        "fa": "اعتبار کیف پول:",
    },
    "period": {
        "en": "• Duration:",
        "fa": "• دوره زمانی:",
    },
    "payment_gateway_title": {
        "en": "• Redirecting to Payment Page",
        "fa": "• هدایت به صفحه پرداخت",
    },
    "zarinpal_payment_gateway_body": {
        "en": "By clicking below, you’ll be transferred to the payment page. Please don’t close the page until the process completes.",
        "fa": "با کلیک روی دکمه پایین به صفحه پرداخت منتقل می‌شوید.\n لطفاً تا پایان فرآیند پرداخت صبور باشید و از بستن صفحه خودداری کنید.",
    },
    "payment_gateway_tail": {
        "en": "• Your transaction will be processed automatically after payment.",
        "fa": "• پس از تکمیل پرداخت، عملیات به‌صورت خودکار انجام خواهد شد.",
    },
    "cryptomus_payment_gateway_body": {
        "en": "By clicking below, you’ll be redirected to the payment page. Ensure the correct currency and network are selected.",
        "fa": "با کلیک روی دکمه پایین به صفحه پرداخت منتقل می‌شوید. لطفاً به ارز و شبکه پرداخت دقت کنید.",
    },
    "amount_added_to_wallet_successfully": {
        "en": "An amount of {0} IRT has been added to your wallet successfully ✅",
        "fa": "مبلغ {0} تومان به کیف پول شما اضافه شد ✅",
    },
    "payment_gateway_label": {
        "en": "Payment Gateway:",
        "fa": "درگاه پرداخت:",
    },
    "zarinpal_label": {
        "en": "ZarinPal",
        "fa": "زرین پال",
    },
    "cryptomus_label": {
        "en": "Cryptomus",
        "fa": "کریپتوموس",
    },
    "just_for_show": {
        "en": "This button is just for showing info.",
        "fa": "این دکمه جهت نمایش اطلاعات است.",
    },
    "invoice_already_paid": {
        "en": "This invoice has already been paid.",
        "fa": "این فاکتور قبلاً پرداخت شده است.",
    },
    "not_enough_credit": {
        "en": "You don’t have enough credit to pay this invoice!",
        "fa": "اعتبار شما برای پرداخت این فاکتور کافی نیست!",
    },
    "user_balance_vs_amount": {
        "en": "Price: {0}"
              "\nYour Balance: {1}",
        "fa": "مبلغ: {0}"
              "\nاعتبار کیف پول: {1}",
    },
    "invoice_paid_by_wallet_message": {
        "en": "The invoice has been paid successfully ✅",
        "fa": "فاکتور با موفقیت پرداخت شد ✅",
    },
    "upgrade_service_successfully": {
        "en": "🟢 Your service {0} has been upgraded successfully!"
        "\n• New specifications added:"
        "\n• Traffic: {1} GB"
        "\n• Duration: {2} days",
        "fa": "🟢 سرویس شما با نام {0} با موفقیت ارتقا یافت!"
        "\n• مشخصات جدید اضافه شده:"
        "\n• ترافیک: {1} گیگابایت"
        "\n• دوره زمانی: {2} روز",
    },
    "no_service_available": {
        "en": "You don’t have any active services!",
        "fa": "شما هیچ سرویس فعالی ندارید!",
    },
    "select_service_category": {
        "en": "Select a category to view details:",
        "fa": "برای مشاهده جزئیات، دسته‌بندی مورد نظر را انتخاب کنید:",
    },
    "config_applied_successfully": {
        "en": "Configuration applied successfully ✅",
        "fa": "تنظیمات با موفقیت اعمال شد ✅",
    },
    "operation_successful": {
        "en": "The operation was successful ✅",
        "fa": "عملیات با موفقیت انجام شد ✅",
    },
    "please_select_your_language": {
        "en": "🌎 Please select your language:",
        "fa": "🌎 لطفاً زبان خود را انتخاب کنید:",
    },
    "guide_and_help_text": {
        "en": "📚 Welcome to the Bot Help Section!" "\n\n• Your ID: {0}",
        "fa": "📚 به بخش راهنمای ربات خوش آمدید!" "\n\n• آیدی شما: {0}",
    },
    "not_paid": {
        "en": "❌ Not Paid",
        "fa": "❌ پرداخت نشده",
    },
    "paid": {
        "en": "✔️ Paid",
        "fa": "✔️ پرداخت شده",
    },
    "refund": {
        "en": "↩️ Refunded",
        "fa": "↩️ بازپرداخت شده",
    },
    "hold": {
        "en": "⏸️ Hold",
        "fa": "⏸️ معلق",
    },
    "upgrade_vpn_service_action": {
        "en": "Upgrade VPN Service Number",
        "fa": "ارتقاء سرویس VPN شماره",
    },
    "buy_vpn_service_action": {
        "en": "Buy VPN Service Number",
        "fa": "خرید سرویس VPN شماره",
    },
    "increase_wallet_balance_action": {
        "en": "Increase Wallet Balance With ID",
        "fa": "افزایش اعتبار کیف پول با شماره",
    },
    "remove_vpn_sevice_and_recive_payback": {
        "en": "Remove VPN Service Number",
        "fa": "حذف سرویس VPN با شماره",
    },
    "payment_authority": {
        "en": "Payment Authority:",
        "fa": "شناسه پرداخت:",
    },
    "already_on_this": {
        "en": "You already on this option!",
        "fa": "این گزینه از قبل انتخاب شده است!",
    },
    "create_ticket_text": {
        "en": "Please send Your message (text, photo)",
        "fa": "لطفا پیام خودتون رو بفرستید (متن یا عکس)",
    },
    "ticket_recived": {
        "en": "Your message has been sent ✅"
        "\nThe answer of the admin will be sent to you through the bot.",
        "fa": "پیام شما ارسال شد✅" "\n• پاسخ ادمین از طریق ربات به اطلاع شما میرسد.",
    },
    "error_in_recive_ticket": {
        "en": "❌ There was a problem sending the message! Please try again later",
        "fa": "❌ مشکلی در ارسال پیام وجود داشت! لطفا بعدا تلاش کنید",
    },
    "without_caption": {
        "en": "Without Caption",
        "fa": "بدون توضیحات",
    },
    "this_service_is_not_available": {
        "en": "This Service is Not Available Anymore!",
        "fa": "این سرویس دیگر در دسترس نیست!",
    },
    "ticket_was_answered": {
        "en": "🎯 You recive message from admin",
        "fa": "🎯 یک پیام از مدیر دریافت کردید",
    },
    "action_canceled": {
        "en": "Action Canceled ✅",
        "fa": "عملیات کنسل شد ✅",
    },
    "send_new_ownership_user_id": {
        "en": "Please send new user chat id.",
        "fa": "لطفا آیدی عددی اکانت مورد نظر را بفرستید.",
    },
    "ask_for_assurnace": {
        "en": "Are you sure you want to do this?"
        "\nService ID: {0}"
        "\nNew user ID: {1}",
        "fa": "از انجام این کار مطمئن هستید؟"
        "\nشماره سرویس: {0}"
        "\nآیدی یوزر جدید: {1}",
    },
    "somthin_wrong_in_change_ownership": {
        "en": "Somthing went srong with changing ownership.\nPlease try again later",
        "fa": "مشکلی در تغییر مالکیت وجود داشت.\n لطفا بعدا امتحان کنید.",
    },
    "change_ownership_was_successfull": {
        "en": "✅ Service with ID {0} was successfully transferred to user with chatID {1}",
        "fa": "✅ سرویس شماره {0} با موفقیت به یوزر با آیدی {1} انتقال یافت.",
    },
    "unknown_input": {
        "en": "message is invalid ❌",
        "fa": "دستور شما نامعتبر است. ❌"
        "\nلطفا از دستورات یا دکمه‌های موجود در منو استفاده کنید.",
    },
    "increase_balance_by_admin": {
        "en": "increase balance by admin",
        "fa": "افزایش اعتبار توسط ادمین",
    },
    "reduction_balance_by_admin": {
        "en": "reduction balance by admin",
        "fa": "کاهش اعتبار توسط ادمین",
    },
    "recive_money_for_referral": {
        "en": "Your friend made the first purchase, {0}% of the purchase amounting to {1} IRT was deposited into your account✅",
        "fa": "دوست شما اولین خرید خودش رو انجام داد، {0} درصد خرید به مبلغ {1} تومن به حساب شما واریز شد✅",
    },
    "invite_firend_text": {
        "en": "👥 By sending an invitation link, receive {0}% of your friends' first transaction amount as a gift!",
        "fa": "👥 با ارسال لینک دعوت، {0} درصد مبلغ اولین تراکنش دوستانتان را به عنوان هدیه دریافت کنید!",
    },
    "invite_firend_text_link": {
        "en": "",
        "fa": "",
    },
    "first_purchase_referral": {
        "en": "Referral for the first purchase of your subcategory",
        "fa": "رفرال اولین خرید زیرمجموعه شما",
    },
    "price_with_discount": {
        "en": "Price With {0}% discount:",
        "fa": "مبلغ با {0}% تخفیف:",
    },
    "manual_check_text": {
        "en": "• Click on 'Manual Check' button if payment was successful, but you have got an error or you do not receive service",
        "fa": '• اگر پرداخت با موفقیت انجام شد اما نتیجه را دریافت نکردید، از گزینه "بررسی دستی" استفاده کنید.',
    },

    "web_application_text": {
        "en": "Access the web app without a VPN to buy or renew your service easily."
              "\n\nYour login details are private—don’t share them."
              "\nSave them for future use."
              "\n\nUsername: {0}"
              "\nPassword: {1}",
        "fa": "• بدون نیاز به VPN از طریق وب‌اپلیکیشن سرویس خود را خریداری یا تمدید کنید."
              "\n\n🔺 اطلاعات ورود شما محرمانه است، آن را به اشتراک نگذارید."
              "\n\nاین اطلاعات را ذخیره کنید."
              "\n\nنام کاربری: {0}"
              "\nرمز عبور: {1}",
    },
}

keyboard_transaction = {
    "open_web_application": {
        "en": "Go to WebApp",
        "fa": "برو به وب اپلیکیشن",
    },
    "manual_check_zarinpal_payment": {
        "en": "Manual Check ↓",
        "fa": "بررسی دستی ↓",
    },
    "web_application": {
        "en": "🌐 Web Application",
        "fa": "🌐 وب اپلیکیشن",
    },
    "virtual_number": {
        "en": "Virtual Number",
        "fa": "شماره مجازی",
    },
    "invite_firend": {
        "en": "🔗 Invite Firends",
        "fa": "🔗 دعوت از دوستان",
    },
    "send_invite_link": {
        "en": "Send Invite Link",
        "fa": "ارسال لینک دعوت",
    },
    "error_message": {
        "en": "Oops, something went wrong!",
        "fa": "خطا در انجام عملیات!",
    },
    "menu_services": {
        "en": "Services",
        "fa": "خدمات",
    },
    "wallet": {
        "en": "👝 Wallet",
        "fa": "👝 کیف پول",
    },
    "ranking": {
        "en": "👥️ Ranking",
        "fa": "👥️ رتبه‌بندی",
    },
    "setting": {
        "en": "⚙️ Settings",
        "fa": "⚙️ تنظیمات",
    },
    "my_services": {
        "en": "🎛 My Services",
        "fa": "🎛 سرویس‌های من",
    },
    "back_button": {
        "en": "↰ Back",
        "fa": "↰ برگشت",
    },
    "bot_main_menu": {
        "en": "↵ Main Menu",
        "fa": "↵ صفحه اصلی ربات",
    },
    "confirm": {
        "en": "✓ Confirm",
        "fa": "✓ تایید",
    },
    "help_button": {
        "en": "📚 Help & Support",
        "fa": "📚 راهنما و پشتیبانی",
    },
    "cancel_button": {
        "en": "✘ Cancel",
        "fa": "✘ انصراف",
    },
    "financial_transactions": {
        "en": "• Financial Transactions",
        "fa": "• تراکنش‌های مالی",
    },
    "increase_balance": {
        "en": "↟ Increase Balance",
        "fa": "↟ افزایش موجودی",
    },
    "refresh": {
        "en": "⟳ Refresh",
        "fa": "⟳ تازه‌سازی",
    },
    "buy_vpn_service_label": {
        "en": "VPN Service",
        "fa": "سرویس VPN",
    },
    "vpn_services_label": {
        "en": "VPN Services",
        "fa": "سرویس‌های VPN",
    },
    "vpn_setting_label": {
        "en": "VPN Settings",
        "fa": "تنظیمات VPN",
    },
    "iran_payment_gateway": {
        "en": "Iran Payment Gateway",
        "fa": "درگاه پرداخت بانکی",
    },
    "cryptomus_payment_gateway": {
        "en": "Pay with Crypto",
        "fa": "پرداخت با کریپتو",
    },
    "pay_with_wallet_balance": {
        "en": "Pay with Wallet",
        "fa": "پرداخت با کیف پول",
    },
    "not_enough_rank": {
        "en": "Your rank isn’t high enough to view this!",
        "fa": "رتبه شما برای دیدن این قسمت کافی نیست!",
    },
    "login_to_payment_gateway": {
        "en": "Proceed to Payment ↷",
        "fa": "ورود به درگاه پرداخت ↶",
    },
    "fail_to_create_payment_gateway": {
        "en": "Failed to create the payment gateway!",
        "fa": "ساخت درگاه پرداخت موفقیت‌آمیز نبود!",
    },
    "yes_im_sure": {
        "en": "Yes, I’m Sure",
        "fa": "بله، مطمئنم",
    },
    "no": {
        "en": "No",
        "fa": "خیر",
    },
    "change_language_setting": {
        "en": "🌎 Change Language",
        "fa": "🌎 تغییر زبان",
    },
    "vpn_guide_label": {
        "en": "VPN Guide",
        "fa": "راهنما VPN",
    },
    "previous": {
        "en": "⬅️ Previous",
        "fa": "⬅️ قبلی",
    },
    "next": {
        "en": "Next ➡️",
        "fa": "بعدی ➡️",
    },
    "recive_service": {
        "en": "Recive Service ↧",
        "fa": "دریافت سرویس ↧",
    },
    "get_vpn_test_label": {
        "en": "Get VPN Test",
        "fa": "دریافت تست VPN",
    },
    "ticket_new_message": {
        "en": "New Message 🆕",
        "fa": "پیام جدید 🆕",
    },
    "create_ticket_label": {
        "en": "Message To Support",
        "fa": "ارتباط با پشتیبانی",
    },
}

text_transaction.update(vpn_service_dialogues.text_transaction)
text_transaction.update(virtual_number_service_dialogues.text_transaction)

keyboard_transaction.update(vpn_service_dialogues.keyboard_transaction)
keyboard_transaction.update(virtual_number_service_dialogues.keyboard_transaction)

