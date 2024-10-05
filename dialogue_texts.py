import vpn_service.dialogue_texts as vpn_service_dialogues


text_transaction = {
    'error_message': {
        'en': '⚠️ Oops, something went wrong!',
        'fa': '⚠️ ببخشید، مشکلی وجود داشت!'
    },
    'start_menu': {
        'en': '👋 Welcome to FreeByte Bot!',
        'fa': '👋 درود، به ربات فری بایت خوش آمدید!'
    },
    'select_section': {
        'en': 'Please choose the section you’d like to continue:',
        'fa': 'برای ادامه بخش مورد نظر خودتان را انتخاب کنید:'
    },
    'message_expired_send_new_message': {
        'en': '⏳ This message has expired! We’ve sent you a new menu.',
        'fa': '⏳ پیام منقضی شده است! منو جدید برای شما ارسال شد.'
    },
    'recent_transactions': {
        'en': '• Recent Transactions:',
        'fa': '• تراکنش‌های اخیر:'
    },
    'receive_money': {
        'en': '💰 Received',
        'fa': '💰 دریافت'
    },
    'spend_money': {
        'en': '💸 Spend',
        'fa': '💸 برداشت'
    },
    'irt': {
        'en': 'IRT',
        'fa': 'تومان'
    },
    'usd': {
        'en': 'USD',
        'fa': 'دلار'
    },
    'no_transaction_yet': {
        'en': 'You haven’t made any transactions yet!',
        'fa': 'شما تا به حال تراکنشی نداشتید!'
    },
    'wallet_page_title': {
        'en': 'Your Wallet Overview:',
        'fa': 'اطلاعات کیف پول شما:'
    },
    'wallet_balance_key': {
        'en': '• Balance:',
        'fa': '• موجودی حساب:'
    },
    'last_transaction': {
        'en': '• Last Transaction:',
        'fa': '• آخرین تراکنش:'
    },
    'add_credit_to_wallet_title': {
        'en': '• Choose an amount to add to your wallet:',
        'fa': '• مشخص کنید چه مقدار اعتبار به کیف پولتان اضافه شود:'
    },
    'invoice_title': {
        'en': '• Please review the details below and finalize your payment if everything looks good:',
        'fa': '• اطلاعات زیر را بررسی کنید و درصورت تایید، پرداخت را نهایی کنید:'
    },
    'price': {
        'en': 'Amount:',
        'fa': 'مبلغ:'
    },
    'payment_option_title': {
        'en': '⤷ Select one of the following payment methods:',
        'fa': '⤶ برای پرداخت می‌توانید یکی از روش‌های زیر را انتخاب کنید:'
    },
    'invoice_extra_data': {
        'en': '• Invoice Details:',
        'fa': '• اطلاعات فاکتور:'
    },
    'charge_wallet': {
        'en': 'Add Credit to Wallet',
        'fa': 'افزایش اعتبار کیف پول'
    },
    'buy_vpn_service': {
        'en': 'Purchase VPN Service',
        'fa': 'خرید سرویس VPN'
    },
    'upgrade_vpn_service': {
        'en': 'Upgrade VPN Service #{0}',
        'fa': 'ارتقاء سرویس VPN شماره {0}'
    },
    'traffic': {
        'en': 'Data Traffic:',
        'fa': '• ترافیک (حجم):'
    },
    'period': {
        'en': 'Duration:',
        'fa': '• دوره زمانی:'
    },
    'payment_gateway_title': {
        'en': '• Redirecting to Payment Page',
        'fa': '• هدایت به صفحه پرداخت'
    },
    'zarinpal_payment_gateway_body': {
        'en': 'By clicking below, you’ll be transferred to the payment page. Please don’t close the page until the process completes.',
        'fa': 'با کلیک روی دکمه پایین به صفحه پرداخت منتقل می‌شوید. لطفاً تا پایان فرآیند پرداخت صبور باشید و از بستن صفحه خودداری کنید.'
    },
    'payment_gateway_tail': {
        'en': '• Your transaction will be processed automatically after payment.',
        'fa': '• پس از تکمیل پرداخت، عملیات به‌صورت خودکار انجام خواهد شد.'
    },
    'cryptomus_payment_gateway_body': {
        'en': 'By clicking below, you’ll be redirected to the payment page. Ensure the correct currency and network are selected.',
        'fa': 'با کلیک روی دکمه پایین به صفحه پرداخت منتقل می‌شوید. لطفاً به ارز و شبکه پرداخت دقت کنید.'
    },
    'amount_added_to_wallet_successfully': {
        'en': 'An amount of {0} IRT has been added to your wallet successfully ✅',
        'fa': 'مبلغ {0} تومان به کیف پول شما اضافه شد ✅'
    },
    'payment_gateway_label': {
        'en': 'Payment Gateway:',
        'fa': 'درگاه پرداخت:'
    },
    'zarinpal_label': {
        'en': 'ZarinPal',
        'fa': 'زرین پال'
    },
    'cryptomus_label': {
        'en': 'Cryptomus',
        'fa': 'کریپتوموس'
    },
    'just_for_show': {
        'en': 'This button is just for showing info.',
        'fa': 'این دکمه جهت نمایش اطلاعات است.'
    },
    'invoice_already_paid': {
        'en': 'This invoice has already been paid.',
        'fa': 'این فاکتور قبلاً پرداخت شده است.'
    },
    'not_enough_credit': {
        'en': 'You don’t have enough credit to pay this invoice!',
        'fa': 'اعتبار شما برای پرداخت این فاکتور کافی نیست!'
    },
    'invoice_paid_by_wallet_message': {
        'en': 'The invoice has been paid successfully ✅',
        'fa': 'فاکتور با موفقیت پرداخت شد ✅'
    },
    'upgrade_service_successfully': {
        'en': '🟢 Your service {0} has been upgraded successfully!'
              '\n• New specifications added:'
              '\n• Traffic: {1} GB'
              '\n• Duration: {2} days',
        'fa': '🟢 سرویس شما با نام {0} با موفقیت ارتقا یافت!'
              '\n• مشخصات جدید اضافه شده:'
              '\n• ترافیک: {1} گیگابایت'
              '\n• دوره زمانی: {2} روز'
    },
    'no_service_available': {
        'en': 'You don’t have any active services!',
        'fa': 'شما هیچ سرویس فعالی ندارید!'
    },
    'select_service_category': {
        'en': 'Select a category to view details:',
        'fa': 'برای مشاهده جزئیات، دسته‌بندی مورد نظر را انتخاب کنید:'
    },
    'config_applied_successfully': {
        'en': 'Configuration applied successfully ✅',
        'fa': 'تنظیمات با موفقیت اعمال شد ✅'
    },
    'please_select_your_language': {
        'en': '🌎 Please select your language:',
        'fa': '🌎 لطفاً زبان خود را انتخاب کنید:'
    },
    'guide_and_help_text': {
        'en': '📚 Welcome to the Bot Help Section!'
              '\n\n• Your ID: {0}',
        'fa': '📚 به بخش راهنمای ربات خوش آمدید!'
              '\n\n• آیدی شما: {0}'
    },
    'not_paid': {
        'en': '❌ Not Paid',
        'fa': '❌ پرداخت نشده'
    },
    'paid': {
        'en': '✔️ Paid',
        'fa': '✔️ پرداخت شده'
    },
    'refund': {
        'en': '↩️ Refunded',
        'fa': '↩️ بازپرداخت شده'
    },
    'upgrade_vpn_service_action': {
        'en': 'Upgrade VPN Service Number',
        'fa': 'ارتقاء سرویس VPN شماره'
    },
    'buy_vpn_service_action': {
        'en': 'Buy VPN Service Number',
        'fa': 'خرید سرویس VPN شماره'
    },
    'increase_wallet_balance_action': {
        'en': 'Increase Wallet Balance With ID',
        'fa': 'افزایش اعتبار کیف پول با شماره'
    },
    'payment_authority': {
        'en': 'Payment Authority:',
        'fa': 'شناسه پرداخت:'
    },
}

keyboard_transaction = {
    'error_message': {
        'en': 'Oops, something went wrong!',
        'fa': 'ببخشید، مشکلی وجود داشت!'
    },
    'menu_services': {
        'en': 'Services',
        'fa': 'خدمات'
    },
    'wallet': {
        'en': 'Wallet 👝',
        'fa': 'کیف پول 👝'
    },
    'ranking': {
        'en': 'Ranking 👥️',
        'fa': 'رتبه‌بندی 👥️'
    },
    'setting': {
        'en': 'Settings ⚙️',
        'fa': 'تنظیمات ⚙️'
    },
    'my_services': {
        'en': 'My Services 🎛',
        'fa': 'سرویس‌های من 🎛'
    },
    'invite': {
        'en': 'Invite',
        'fa': 'دعوت'
    },
    'back_button': {
        'en': 'Back ↰',
        'fa': 'برگشت ↰'
    },
    'bot_main_menu': {
        'en': 'Main Menu ↵',
        'fa': 'صفحه اصلی ربات ↵'
    },
    'confirm': {
        'en': 'Confirm ✓',
        'fa': '✓ تایید'
    },
    'help_button': {
        'en': 'Help & Support 📚',
        'fa': 'راهنما و پشتیبانی 📚'
    },
    'cancel_button': {
        'en': 'Cancel ✘',
        'fa': 'انصراف ✘'
    },
    'financial_transactions': {
        'en': '• Financial Transactions',
        'fa': '• تراکنش‌های مالی'
    },
    'increase_balance': {
        'en': 'Increase Balance ↟',
        'fa': 'افزایش موجودی ↟'
    },
    'refresh': {
        'en': 'Refresh ⟳',
        'fa': 'تازه‌سازی ⟳'
    },
    'buy_vpn_service_label': {
        'en': 'Buy VPN Service',
        'fa': 'خرید سرویس VPN'
    },
    'vpn_services_label': {
        'en': 'VPN Services',
        'fa': 'سرویس‌های VPN'
    },
    'vpn_setting_label': {
        'en': 'VPN Settings',
        'fa': 'تنظیمات VPN'
    },
    'iran_payment_gateway': {
        'en': 'Iran Payment Gateway',
        'fa': 'درگاه پرداخت بانکی'
    },
    'cryptomus_payment_gateway': {
        'en': 'Pay with Crypto',
        'fa': 'پرداخت با کریپتو'
    },
    'pay_with_wallet_balance': {
        'en': 'Pay with Wallet',
        'fa': 'پرداخت با کیف پول'
    },
    'not_enough_rank': {
        'en': 'Your rank isn’t high enough to view this!',
        'fa': 'رتبه شما برای دیدن این قسمت کافی نیست!'
    },
    'login_to_payment_gateway': {
        'en': 'Proceed to Payment ↷',
        'fa': 'ورود به درگاه پرداخت ↶'
    },
    'fail_to_create_payment_gateway': {
        'en': 'Failed to create the payment gateway!',
        'fa': 'ساخت درگاه پرداخت موفقیت‌آمیز نبود!'
    },
    'yes_im_sure': {
        'en': 'Yes, I’m Sure',
        'fa': 'بله، مطمئنم'
    },
    'no': {
        'en': 'No',
        'fa': 'خیر'
    },
    'change_language_setting': {
        'en': 'Change Language 🌎',
        'fa': 'تغییر زبان 🌎'
    },
    'vpn_guide_label': {
        'en': 'VPN Guide',
        'fa': 'راهنمای VPN'
    },
    'previous': {
        'en': 'Previous',
        'fa': 'قبلی'
    },
    'next': {
        'en': 'Next',
        'fa': 'بعدی'
    }
}

text_transaction.update(vpn_service_dialogues.text_transaction)
keyboard_transaction.update(vpn_service_dialogues.keyboard_transaction)
